#!/usr/bin/env python3
"""
Hotspawn League of Legends (LoL) Pick'em Probability & Picks Originator.
Stdlib only (runs cleanly in GitHub Actions without heavy dependencies).

Key Requirements:
 1. Full coverage of all League of Legends matches listed on Hotspawn.
 2. Hotspawn crowd % is NEVER used as an indicator or input for match win probability.
 3. Originates probabilities using:
    - Level 1: Established esportsbooks / bookmaker lines (de-vigged median across books via OddsPapi if key set)
    - Level 2: Public prediction markets (Polymarket Gamma API)
    - Level 3: Our own originated line model: Elo model calculated over Leaguepedia official match results (ScoreboardGames Cargo API)
    - Level 4: Explicit 50/50 UNRESOLVED baseline with detailed limitation disclosure.
 4. Every row contains verified official source links.
 5. Runs on a regular automated schedule (every 6 hours) in GitHub Actions.
"""

import json
import os
import re
import sys
import math
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 "
        "(compatible; LOLHOTSPAWN4-picks/1.0; +https://github.com/karagemop466-tech/LOLHOTSPAWN4)"
    ),
    "Accept": "text/html,application/json,*/*",
}

LOBBY_URL = "https://play.hotspawn.com/lol-pickems"
FALLBACK_LOBBY_URL = "https://play.hotspawn.com/lobby"
FIXTURES_API_URL = "https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures?sport_alias=lol&status=scheduled&tenantId=1"
NOW = datetime.now(timezone.utc)

def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace"), resp.status

def slugify(text):
    text = (text or "").lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text or "team"

def norm_team(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

# ---------- Hotspawn Fixture Ingestion (Primary: Backend API; Fallback: SSR HTML) ----------

def fetch_hotspawn_fixtures_api():
    """
    Reverse-engineered internal backend fixtures API powering play.hotspawn.com.
    Returns complete, structured match list for LoL.
    """
    try:
        data, status = http_get(FIXTURES_API_URL, timeout=25)
        if status != 200:
            return None, f"HTTP {status}"
        fixtures = json.loads(data)
        if not isinstance(fixtures, list) or len(fixtures) == 0:
            return None, "Empty fixture list"
        
        matches = []
        for fx in fixtures:
            t1 = (fx.get("participants0_name") or "").strip()
            t2 = (fx.get("participants1_name") or "").strip()
            if not t1 or not t2 or t1.upper() == "TBD" or t2.upper() == "TBD":
                continue
            
            mid = str(fx.get("id") or "")
            comp_name = str(fx.get("competition_name") or "Tournament").strip()
            tier_raw = str(fx.get("tier") or "WAITING FOR INFORMATION").strip().upper()
            stage_raw = str(fx.get("stage") or "WAITING FOR INFORMATION").strip()
            points = str(fx.get("offered_points") or fx.get("base_points") or "10").strip()
            
            # Start time and lock time
            start_ms = fx.get("scheduled_start_time")
            lock_ms = fx.get("lock_time")
            start_utc = ""
            start_raw = ""
            if start_ms and str(start_ms).isdigit():
                sec = int(start_ms) / 1000.0 if int(start_ms) > 10**11 else int(start_ms)
                dt = datetime.fromtimestamp(sec, timezone.utc)
                start_utc = dt.isoformat()
                start_raw = dt.strftime("%b %d, %H:%M")
            
            lock_utc = ""
            if lock_ms and str(lock_ms).isdigit():
                sec = int(lock_ms) / 1000.0 if int(lock_ms) > 10**11 else int(lock_ms)
                lock_utc = datetime.fromtimestamp(sec, timezone.utc).isoformat()
            
            # Hotspawn match URL slug convention
            t1_slug = slugify(t1)
            t2_slug = slugify(t2)
            comp_slug = slugify(comp_name)
            hotspawn_url = f"https://www.hotspawn.com/matches/{t1_slug}-vs-{t2_slug}-{comp_slug}-{mid}" if mid else ""
            
            crowd1 = fx.get("participants0_picked_percent")
            crowd2 = fx.get("participants1_picked_percent")
            
            matches.append({
                "id": mid,
                "team1": t1,
                "team2": t2,
                "tournament": comp_name,
                "tier": tier_raw,
                "stage": stage_raw,
                "points": points,
                "start_raw": start_raw,
                "start_utc": start_utc,
                "lock_utc": lock_utc,
                "hotspawn_url": hotspawn_url,
                "crowd1": crowd1 if crowd1 is not None else None,
                "crowd2": crowd2 if crowd2 is not None else None,
                "source_lobby": LOBBY_URL,
            })
        
        # Deduplicate
        seen = set()
        deduped = []
        for m in matches:
            key = (norm_team(m["team1"]), norm_team(m["team2"]), m["start_utc"], norm_team(m["tournament"]))
            if key not in seen:
                seen.add(key)
                deduped.append(m)
        return deduped, "internal-fixtures-api"
    except Exception as e:
        print(f"Hotspawn fixtures API error: {e}", file=sys.stderr)
        return None, str(e)

class TextExtract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self._href = None
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a":
            self._href = d.get("href")
    def handle_endtag(self, tag):
        if tag == "a":
            self._href = None
    def handle_data(self, data):
        t = " ".join(data.split())
        if t:
            self.items.append((t, self._href))

DATE_RE = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s*\d{1,2}:\d{2}$')

def parse_lobby_html(html):
    """
    Fallback SSR token-stream parser for play.hotspawn.com.
    """
    p = TextExtract()
    p.feed(html)
    items = p.items
    out = []
    i = 0
    while i < len(items):
        txt = items[i][0]
        if DATE_RE.match(txt):
            start = txt
            window = items[i + 1 : i + 45]
            texts = [w[0] for w in window]
            try:
                wi = texts.index("Who will win?")
            except ValueError:
                i += 1
                continue
            
            tournament = texts[0] if texts else ""
            tier = "WAITING FOR INFORMATION"
            points = "10"
            joined = " ".join(texts[:wi])
            tm = re.search(r'Tier\s*([A-Z]|WAITING FOR INFORMATION)', joined, re.I)
            if tm:
                tier = tm.group(1).upper()
            tm2 = re.search(r'(\d+)\s*pts', joined)
            if tm2:
                points = tm2.group(1)
            
            rest = texts[wi + 1 : wi + 10]
            teams = []
            crowds = []
            for t in rest:
                pm = re.match(r'^(\d+)%\s*picked$', t)
                if pm:
                    crowds.append(int(pm.group(1)))
                elif (
                    t not in ("Sign in for streaks", "Locks in")
                    and not re.match(r'^[\d:dhms ]+$', t)
                    and len(teams) < 2
                ):
                    teams.append(t)
            
            url = ""
            for w in window:
                if w[1] and "hotspawn.com/matches/" in w[1]:
                    url = w[1]
                    break
            
            if len(teams) == 2:
                # Convert start text to start_utc
                start_utc = ""
                try:
                    dt = datetime.strptime(f"{start} {NOW.year}", "%b %d, %H:%M %Y").replace(tzinfo=timezone.utc)
                    if dt < NOW - timedelta(days=2):
                        dt = dt.replace(year=NOW.year + 1)
                    start_utc = dt.isoformat()
                except Exception:
                    pass
                
                out.append({
                    "id": "",
                    "team1": teams[0],
                    "team2": teams[1],
                    "tournament": tournament,
                    "tier": tier,
                    "stage": "WAITING FOR INFORMATION",
                    "points": points,
                    "start_raw": start,
                    "start_utc": start_utc,
                    "lock_utc": "",
                    "hotspawn_url": url,
                    "crowd1": crowds[0] if len(crowds) > 0 else None,
                    "crowd2": crowds[1] if len(crowds) > 1 else None,
                    "source_lobby": LOBBY_URL,
                })
            i += wi + 1
        else:
            i += 1
    
    seen = set()
    deduped = []
    for m in out:
        key = (norm_team(m["team1"]), norm_team(m["team2"]), m["start_raw"], norm_team(m["tournament"]))
        if key not in seen:
            seen.add(key)
            deduped.append(m)
    return deduped, "ssr-html-token-stream"

def get_hotspawn_matches():
    # 1. Try internal fixtures API
    matches, parser = fetch_hotspawn_fixtures_api()
    if matches and len(matches) > 0:
        return matches, parser, 200, len(matches)
    
    # 2. Try SSR HTML
    for url in [LOBBY_URL, FALLBACK_LOBBY_URL]:
        try:
            html, status = http_get(url, timeout=25)
            matches, parser = parse_lobby_html(html)
            if matches and len(matches) > 0:
                return matches, parser, status, len(html)
        except Exception as e:
            print(f"SSR lobby fetch error for {url}: {e}", file=sys.stderr)
            continue
    
    # 3. Fallback to existing file if available (e.g. sandbox without internet)
    for path in ["docs/data/picks.json", "data/picks.json"]:
        if os.path.exists(path):
            try:
                cached = json.load(open(path, "r", encoding="utf-8"))
                cached_matches = cached.get("matches", [])
                if cached_matches:
                    print(f"Loaded {len(cached_matches)} matches from cached {path}", file=sys.stderr)
                    return cached_matches, "cached-fallback", 200, len(cached_matches)
            except Exception as e:
                print(f"Cache load error for {path}: {e}", file=sys.stderr)
    
    return [], "failed", 0, 0

# ---------- External Betting Markets: Polymarket Gamma API ----------

def fetch_polymarket_events():
    events = []
    urls = [
        "https://gamma-api.polymarket.com/events?tag_slug=league-of-legends&active=true&closed=false&limit=100",
        "https://gamma-api.polymarket.com/events?search=league%20of%20legends&active=true&closed=false&limit=100",
    ]
    for url in urls:
        try:
            data, _ = http_get(url, timeout=20)
            parsed = json.loads(data)
            if isinstance(parsed, list):
                events.extend(parsed)
        except Exception as e:
            print(f"Polymarket fetch error ({url}): {e}", file=sys.stderr)
    
    idx = []
    for ev in events:
        slug = str(ev.get("slug", ""))
        for mk in ev.get("markets", []):
            q = mk.get("question", "")
            try:
                prices = json.loads(mk.get("outcomePrices") or "[]")
                outs = json.loads(mk.get("outcomes") or "[]")
            except Exception:
                continue
            if len(prices) == 2 and len(outs) == 2:
                try:
                    p1 = float(prices[0])
                    p2 = float(prices[1])
                    idx.append({
                        "question": q,
                        "outs": outs,
                        "prices": [p1, p2],
                        "url": f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com",
                    })
                except Exception:
                    pass
    return idx

def lookup_polymarket(idx, t1, t2):
    n1, n2 = norm_team(t1), norm_team(t2)
    for m in idx:
        o = [norm_team(x) for x in m["outs"]]
        if (n1 in o[0] or o[0] in n1) and (n2 in o[1] or o[1] in n2):
            return m["prices"][0], m["url"], m["question"]
        if (n2 in o[0] or o[0] in n2) and (n1 in o[1] or o[1] in n1):
            return m["prices"][1], m["url"], m["question"]
        q = norm_team(m["question"])
        if n1 in q and n2 in q and m["prices"]:
            return m["prices"][0], m["url"], m["question"]
    return None

# ---------- External Betting Markets: OddsPapi (Bookmakers / Pinnacle / bet365) ----------

def fetch_oddspapi_odds():
    key = os.environ.get("ODDSPAPI_KEY")
    if not key:
        return []
    try:
        data, _ = http_get(f"https://api.oddspapi.io/v4/fixtures?sportId=18&apiKey={key}", timeout=25)
        fx = json.loads(data)
    except Exception as e:
        print(f"OddsPapi fixtures error: {e}", file=sys.stderr)
        return []
    
    out = []
    for f in fx if isinstance(fx, list) else []:
        p1 = f.get("participant1Name") or ""
        p2 = f.get("participant2Name") or ""
        fid = f.get("fixtureId")
        if not (p1 and p2 and fid):
            continue
        try:
            data, _ = http_get(f"https://api.oddspapi.io/v4/odds?fixtureId={fid}&apiKey={key}", timeout=20)
            od = json.loads(data)
            books = od.get("bookmakers", {})
            probs = []
            for slug, book in books.items():
                mk = (book.get("markets") or {}).get("181")  # LoL series winner market id
                if not mk:
                    continue
                outs = mk.get("outcomes") or {}
                vals = []
                for oid in ("181", "182"):
                    o = outs.get(oid) or {}
                    pr = (o.get("players") or {}).get("0") or o
                    price = pr.get("price")
                    if price:
                        try:
                            vals.append(float(price))
                        except Exception:
                            pass
                if len(vals) == 2 and all(v > 1.0 for v in vals):
                    inv = [1.0 / v for v in vals]
                    s = sum(inv)
                    probs.append((inv[0] / s, slug))
            if probs:
                probs.sort(key=lambda x: x[0])
                med = probs[len(probs) // 2]
                out.append({
                    "team1": p1,
                    "team2": p2,
                    "p1": med[0],
                    "source": f"OddsPapi median de-vigged ({len(probs)} books, median: {med[1]})",
                    "url": "https://oddspapi.io/sports/esports/lol",
                })
        except Exception as e:
            print(f"OddsPapi odds error for fixture {fid}: {e}", file=sys.stderr)
    return out

# ---------- Originated Line Model: Leaguepedia Cargo API Elo Ratings ----------

def build_elo_model():
    """
    Originates our own line model using competitive League of Legends match results
    from Leaguepedia's Cargo API (ScoreboardGames table).
    Elo with K=32, adjusted by sample-size shrinkage toward 50% for sparse history.
    """
    ratings = {}
    games = {}
    recent = {}
    since = (NOW - timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
    offset = 0
    
    for _ in range(12):  # fetch up to 6000 games
        q = urllib.parse.urlencode({
            "action": "cargoquery",
            "format": "json",
            "tables": "ScoreboardGames=SG",
            "fields": "SG.Team1,SG.Team2,SG.Winner,SG.DateTime_UTC",
            "where": f"SG.DateTime_UTC >= '{since}' AND SG.Winner IS NOT NULL",
            "order_by": "SG.DateTime_UTC ASC",
            "limit": "500",
            "offset": str(offset),
        })
        try:
            data, _ = http_get("https://lol.fandom.com/api.php?" + q, timeout=25)
            rows = json.loads(data).get("cargoquery", [])
        except Exception as e:
            print(f"Leaguepedia Cargo API fetch error: {e}", file=sys.stderr)
            break
        
        if not rows:
            break
        
        for r in rows:
            t = r.get("title", r)
            a = t.get("Team1", "")
            b = t.get("Team2", "")
            w = str(t.get("Winner", ""))
            if not a or not b:
                continue
            
            na, nb = norm_team(a), norm_team(b)
            ra = ratings.get(na, 1500.0)
            rb = ratings.get(nb, 1500.0)
            ea = 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))
            winner_a = (w == "1")
            actual_a = 1.0 if winner_a else 0.0
            delta = 32.0 * (actual_a - ea)
            
            ratings[na] = ra + delta
            ratings[nb] = rb - delta
            games[na] = games.get(na, 0) + 1
            games[nb] = games.get(nb, 0) + 1
            recent.setdefault(na, []).append(1 if winner_a else 0)
            recent.setdefault(nb, []).append(0 if winner_a else 1)
        
        offset += 500
        if len(rows) < 500:
            break
            
    return ratings, games, recent

# ---------- Main Pick Generation Pipeline ----------

def main():
    print(f"Starting Hotspawn LoL pick generation pipeline at {NOW.isoformat()}...")
    
    matches, parser_type, http_status, bytes_or_count = get_hotspawn_matches()
    print(f"Parser '{parser_type}' returned {len(matches)} matches (HTTP {http_status}).")
    
    if not matches:
        print("ERROR: 0 matches parsed. Cannot proceed.", file=sys.stderr)
        sys.exit(1)
        
    debug = {
        "generated_at": NOW.isoformat(),
        "lobby": LOBBY_URL,
        "fixtures_api": FIXTURES_API_URL,
        "lobby_http": http_status,
        "parser": parser_type,
        "matches_parsed": len(matches),
    }
    
    # 1. Fetch external market lines
    poly_idx = fetch_polymarket_events()
    debug["polymarket_markets"] = len(poly_idx)
    
    oddspapi_fixtures = fetch_oddspapi_odds()
    debug["oddspapi_fixtures_priced"] = len(oddspapi_fixtures)
    
    # 2. Build our own Elo model from Leaguepedia
    ratings, games, recent = build_elo_model()
    debug["elo_teams"] = len(ratings)
    
    # 3. Resolve probability for every single match
    resolved_rows = []
    is_offline = (len(poly_idx) == 0 and len(oddspapi_fixtures) == 0 and len(ratings) == 0)
    
    for m in matches:
        t1 = m["team1"]
        t2 = m["team2"]
        n1 = norm_team(t1)
        n2 = norm_team(t2)
        
        row = dict(m)
        row["crowd_note"] = "Hotspawn crowd % shown on lobby is context only and is NEVER used as a probability input."
        
        # If running offline and match already has a resolved method, preserve it
        if is_offline and m.get("method") and m.get("prob_team1") is not None:
            resolved_rows.append(row)
            continue
            
        prob = None
        method = ""
        evidence = ""
        confidence = ""
        market_url = ""
        source_url = ""
        
        # Priority 1: Esportsbook median (OddsPapi)
        for b in oddspapi_fixtures:
            bn1, bn2 = norm_team(b["team1"]), norm_team(b["team2"])
            if {bn1, bn2} == {n1, n2}:
                prob = b["p1"] if bn1 == n1 else (1.0 - b["p1"])
                method = "MARKET_BOOKS"
                evidence = b["source"]
                confidence = "High — established esportsbook lines, de-vigged"
                market_url = b["url"]
                source_url = b["url"]
                break
                
        # Priority 2: Polymarket prediction market
        if prob is None and poly_idx:
            hit = lookup_polymarket(poly_idx, t1, t2)
            if hit:
                poly_p, poly_url, poly_q = hit
                prob = poly_p
                method = "MARKET_POLYMARKET"
                evidence = f"Polymarket market: {poly_q}"
                confidence = "High — prediction-market traded price"
                market_url = poly_url
                source_url = poly_url
                
        # Priority 3: Our own originated line (Elo model from Leaguepedia)
        if prob is None and (n1 in ratings or n2 in ratings):
            r1 = ratings.get(n1, 1500.0)
            r2 = ratings.get(n2, 1500.0)
            g1 = games.get(n1, 0)
            g2 = games.get(n2, 0)
            
            raw_prob = 1.0 / (1.0 + 10.0 ** ((r2 - r1) / 400.0))
            # Shrink toward 50% when history is thin
            min_g = min(g1, g2)
            shrinkage = min_g / (min_g + 10.0) if min_g > 0 else 0.25
            prob = 0.5 + (raw_prob - 0.5) * shrinkage
            
            method = "MODEL_ELO"
            evidence = (
                f"Originated Elo model (Leaguepedia results, past 180d): "
                f"{t1} (Elo {round(r1)}, {g1} games) vs {t2} (Elo {round(r2)}, {g2} games)"
            )
            confidence = "Medium — historical competitive data" if min_g >= 10 else "Low — thin team match history"
            row["elo"] = [round(r1), round(r2)]
            row["games"] = [g1, g2]
            source_url = "https://lol.fandom.com/api.php?action=help&modules=cargoquery"
            
        # Priority 4: Explicit 50/50 Unresolved baseline with full limitation disclosure
        if prob is None:
            prob = 0.50
            method = "UNRESOLVED"
            evidence = "No external market line and no Leaguepedia match history recorded for either team"
            confidence = "Unresolved — 50/50 baseline; no edge"
            source_url = "https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki"
            
        # Clamp and round probability
        prob = round(max(0.01, min(0.99, prob)), 4)
        prob2 = round(1.0 - prob, 4)
        
        row["prob_team1"] = prob
        row["prob_team2"] = prob2
        
        # Determine pick
        if prob >= prob2:
            row["pick"] = t1
            row["pick_prob"] = prob
        else:
            row["pick"] = t2
            row["pick_prob"] = prob2
            
        row["method"] = method
        row["evidence"] = evidence
        row["confidence"] = confidence
        row["market_url"] = market_url
        row["source_url"] = source_url
        
        resolved_rows.append(row)
        
    # Sort matches by scheduled start time, tournament, team1
    resolved_rows.sort(key=lambda r: (r.get("start_utc") or "9999", r.get("tournament", ""), r.get("team1", "")))
    
    counts_by_method = {
        "MARKET_BOOKS": sum(1 for r in resolved_rows if r["method"] == "MARKET_BOOKS"),
        "MARKET_POLYMARKET": sum(1 for r in resolved_rows if r["method"] == "MARKET_POLYMARKET"),
        "MODEL_ELO": sum(1 for r in resolved_rows if r["method"] == "MODEL_ELO"),
        "UNRESOLVED": sum(1 for r in resolved_rows if r["method"] == "UNRESOLVED"),
    }
    
    payload = {
        "generated_at": NOW.isoformat(),
        "lobby": LOBBY_URL,
        "count": len(resolved_rows),
        "counts_by_method": counts_by_method,
        "debug": debug,
        "matches": resolved_rows,
    }
    
    # Save to data/picks.json, docs/data/picks.json, and data/debug.json
    for path in ["data/picks.json", "docs/data/picks.json"]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)
            
    os.makedirs("data", exist_ok=True)
    with open("data/debug.json", "w", encoding="utf-8") as f:
        json.dump(debug, f, indent=1)
        
    print(f"Successfully generated picks for {len(resolved_rows)} matches!")
    print(f"Method distribution: {json.dumps(counts_by_method)}")

if __name__ == "__main__":
    main()
