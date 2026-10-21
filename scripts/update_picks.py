#!/usr/bin/env python3
"""
Hotspawn LoL Pick'em - canonical pick & probability resolver.

Writes data/picks.json (the single dataset the GitHub Pages site renders)
plus data/debug.json (run diagnostics) and data/raw/leaguepedia_games.json
(persistent, rate-limit-friendly cache of community-wiki match results).

Data flow (integration of the two earlier pipelines, see COORDINATION.md):
  1. Raw layer  - collector/fetch_hotspawn.py + collector/fetch_odds.py
                  (verified endpoints; raw snapshots + manifest in data/raw).
  2. This script resolves every fixture into a probability + pick, reading
                  those raw snapshots first and only fetching directly as a
                  fallback (keeps the 6h standalone workflow working).

Resolution hierarchy (highest first) - Hotspawn crowd % is NEVER an input:
  MARKET_BOOKS      de-vigged median of commercial books via OddsPapi
                    (only if ODDSPAPI_KEY secret is configured).
  MARKET_POLYMARKET exact mids of a public per-match "winner" market
                    (series/moneyline preferred over a Game-1 market; a
                    Game-1-only match is flagged).
  KALSHI_FUTURES    our own originated line: ratio model on both teams'
                    open Kalshi tournament-futures mids (same event).
  MODEL_ELO         our own originated line: Elo (K=32) over Leaguepedia
                    community-wiki results, past 180 days, shrunk toward
                    50/50 by sample size. Polite by design: ONE API batch
                    per run, merged into a persistent cache; on rate limit
                    or error the cache is reused (model degrades, never
                    crashes).
  UNRESOLVED        explicit 50.0/50.0 baseline, pick shown as "No Edge"
                    (the stored pick is nominal only and carries no edge).

Coverage rule: only fixtures whose pick lock time has not passed
(lock_time >= now) are "available picks" on the Hotspawn lobby and are
listed in matches[]. Fixtures already locked out are published in
excluded_stale[] with the reason, so nothing is silently dropped.
"""

import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(REPO_ROOT, "data", "raw")
sys.path.insert(0, os.path.join(REPO_ROOT, "collector"))
import common  # noqa: E402  (teams_match, http_get_json, ms/iso parsing)

NOW = datetime.now(timezone.utc)
OFFLINE = ("--offline" in sys.argv) or os.environ.get("OFFLINE") == "1"

LOBBY_URL = "https://play.hotspawn.com/lobby"
LEAGUEPEDIA_API = "https://lol.fandom.com/api.php"
LEAGUEPEDIA_WIKI = "https://lol.fandom.com/wiki/Leaguepedia:League_of_Legends_Esports_Wiki"
LEAGUEPEDIA_WINDOW_DAYS = 180

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 "
        "(compatible; LOLHOTSPAWN4-picks/1.0; +https://github.com/karagemop466-tech/LOLHOTSPAWN4)"
    ),
    "Accept": "text/html,application/json,*/*",
}

# Verified team-name aliases (see COORDINATION.md verification log I-12).
# Keyed on the *normalized* fixture/source name (common.normalize_team).
TEAM_ALIASES = {
    # 2026-10-21: Hotspawn spells the Worlds team "LØS" (Nordic spelling);
    # Polymarket (event lol-los-t1-2026-10-23, page verified) and Kalshi
    # (KXLOL-WORLDS26-LOS) both list it as "LOS". Polymarket's own market
    # rules treat alternate spellings as the same team.
    "l s": "los",
}


def log(msg):
    print("[%s] %s" % (NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), msg), flush=True)


def slugify(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "team"


def norm_team(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def canon(name):
    n = common.normalize_team(name)
    return TEAM_ALIASES.get(n, n)


def match_teams(a, b):
    """Conservative team-name match (shared matcher + verified aliases)."""
    return bool(common.teams_match(a, b)) or (canon(a) != "" and canon(a) == canon(b))


def ms_to_dt(v):
    if v in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(int(v) / 1000.0, tz=timezone.utc)
    except Exception:
        return None


def parse_pm_game_start(s):
    if not s:
        return None
    s2 = str(s).strip()
    if " " in s2 and "T" not in s2:
        s2 = s2.replace(" ", "T", 1)
    return common.parse_iso(s2)


def game_start_to_dt(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 1) Hotspawn fixtures (raw snapshot first, direct fetch as fallback)
# ---------------------------------------------------------------------------

def fixtures_from_snapshot():
    path = os.path.join(RAW_DIR, "hotspawn_fixtures_scheduled.json")
    if os.path.exists(path):
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
            if isinstance(data, list) and data:
                log("fixtures: using raw snapshot (%d fixtures)" % len(data))
                return data, "raw-snapshot"
        except Exception as e:
            log("fixtures: snapshot unreadable (%s)" % e)
    return None, "snapshot-missing"


def fixtures_from_api():
    try:
        req = urllib.request.Request(common.HOTSPAWN_FIXTURES_URL, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        if isinstance(data, list) and data:
            return data, "api-direct"
    except Exception as e:
        log("fixtures: API fetch failed: %s" % e)
    return None, "api-failed"


def fixture_rows(raw_fixtures):
    rows = []
    for fx in raw_fixtures:
        t1 = (fx.get("participants0_name") or "").strip()
        t2 = (fx.get("participants1_name") or "").strip()
        if not t1 or not t2 or t1.upper() == "TBD" or t2.upper() == "TBD":
            continue
        mid = str(fx.get("id") or "")
        comp = str(fx.get("competition_name") or "Tournament").strip()
        tier_raw = str(fx.get("tier") or "waiting for information").strip()
        stage_raw = str(fx.get("stage") or "waiting for information").strip()
        points = str(fx.get("offered_points") or fx.get("base_points") or "10").strip()

        start_dt = ms_to_dt(fx.get("scheduled_start_time"))
        lock_dt = ms_to_dt(fx.get("lock_time"))
        start_utc = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if start_dt else ""
        lock_utc = lock_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if lock_dt else ""
        start_raw = start_dt.strftime("%b %d, %H:%M") if start_dt else ""

        t1_slug, t2_slug, comp_slug = slugify(t1), slugify(t2), slugify(comp)
        hotspawn_url = (
            "https://www.hotspawn.com/matches/%s-vs-%s-%s-%s" % (t1_slug, t2_slug, comp_slug, mid)
            if mid else ""
        )
        rows.append({
            "id": mid,
            "team1": t1,
            "team2": t2,
            "tournament": comp,
            "tier": tier_raw,
            "stage": stage_raw,
            "points": points,
            "start_raw": start_raw,
            "start_utc": start_utc,
            "lock_utc": lock_utc,
            "_lock_dt": lock_dt,
            "hotspawn_url": hotspawn_url,
            "crowd1": fx.get("participants0_picked_percent"),
            "crowd2": fx.get("participants1_picked_percent"),
            "source_lobby": LOBBY_URL,
        })

    seen, deduped = set(), []
    for m in rows:
        key = (norm_team(m["team1"]), norm_team(m["team2"]), m["start_utc"], norm_team(m["tournament"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(m)
    return deduped


def get_hotspawn_matches():
    raw, how = fixtures_from_snapshot()
    if raw is None and not OFFLINE:
        raw, how = fixtures_from_api()
    if raw is None:
        return None, how
    return fixture_rows(raw), how


# ---------------------------------------------------------------------------
# 2) External markets (raw snapshots first)
# ---------------------------------------------------------------------------

def snapshot(name, key):
    path = os.path.join(RAW_DIR, name)
    if not os.path.exists(path):
        return None
    try:
        data = json.load(open(path, "r", encoding="utf-8"))
        return data.get(key) if isinstance(data, dict) else data
    except Exception:
        return None


def polymarket_markets():
    mk = snapshot("polymarket_lol_markets.json", "markets")
    if mk:
        log("polymarket: using raw snapshot (%d markets)" % len(mk))
        return mk, "raw-snapshot"
    if OFFLINE:
        return [], "offline-no-snapshot"
    # Fallback: direct gamma fetch (tag_id=65 = LoL primary tag, verified).
    try:
        events, _ = common.http_get_json(
            common.POLYMARKET_GAMMA_BASE +
            "/events?tag_id=65&closed=false&limit=100&offset=0", timeout=30)
        out = []
        for ev in (events or []):
            if not isinstance(ev, dict):
                continue
            slug = str(ev.get("slug", ""))
            for m in ev.get("markets", []) or []:
                try:
                    prices = json.loads(m.get("outcomePrices") or "[]")
                    outs = json.loads(m.get("outcomes") or "[]")
                    if len(prices) != 2 or len(outs) != 2:
                        continue
                    out.append({
                        "question": m.get("question", ""),
                        "outcomes": outs,
                        "prices": [float(prices[0]), float(prices[1])],
                        "url": "https://polymarket.com/event/%s" % slug if slug else "https://polymarket.com",
                        "game_start": m.get("gameStartTime"),
                        "event_start": ev.get("startDate"),
                        "volume": m.get("volumeNum") or ev.get("volumeNum"),
                        "closed": False,
                    })
                except Exception:
                    continue
        log("polymarket: direct fetch (%d markets)" % len(out))
        return out, "api-direct"
    except Exception as e:
        log("polymarket: direct fetch failed: %s" % e)
        return [], "api-failed"


def kalshi_markets():
    mk = snapshot("kalshi_lol_markets.json", "markets")
    if mk:
        log("kalshi: using raw snapshot (%d markets)" % len(mk))
        return mk, "raw-snapshot"
    if OFFLINE:
        return [], "offline-no-snapshot"
    try:
        url = "%s/markets?series_ticker=%s&status=open" % (common.KALSHI_API_BASE, common.KALSHI_LOL_SERIES)
        data, _ = common.http_get_json(url, timeout=30)
        out = []
        for m in (data or {}).get("markets", []) or []:
            out.append({
                "title": m.get("title", ""),
                "subtitle": m.get("subtitle", ""),
                "ticker": m.get("ticker", ""),
                "mid": m.get("mid"),
                "status": m.get("status", ""),
                "event_ticker": m.get("event_ticker", ""),
                "url": "https://kalshi.com/markets/%s" % m.get("ticker", ""),
            })
        log("kalshi: direct fetch (%d markets)" % len(out))
        return out, "api-direct"
    except Exception as e:
        log("kalshi: direct fetch failed: %s" % e)
        return [], "api-failed"


def pinnacle_matchups():
    mk = snapshot("pinnacle_lol_matchups.json", "matchups")
    if mk:
        log("pinnacle: using raw snapshot (%d matchups)" % len(mk))
        return mk, "raw-snapshot"
    if OFFLINE:
        return [], "offline-no-snapshot"
    return [], "snapshot-missing"  # coverage flag only; never blocks


def oddspapi_odds():
    key = os.environ.get("ODDSPAPI_KEY")
    if not key or OFFLINE:
        return []
    try:
        data, _ = common.http_get_json(
            "https://api.oddspapi.io/v4/fixtures?sportId=18&apiKey=%s" % key, timeout=25)
    except Exception as e:
        log("oddspapi: fixtures fetch failed: %s" % e)
        return []
    out = []
    for f in (data if isinstance(data, list) else []):
        p1 = f.get("participant1Name") or ""
        p2 = f.get("participant2Name") or ""
        fid = f.get("fixtureId")
        if not (p1 and p2 and fid):
            continue
        try:
            data, _ = common.http_get_json(
                "https://api.oddspapi.io/v4/odds?fixtureId=%s&apiKey=%s" % (fid, key), timeout=20)
        except Exception:
            continue
        od = data if isinstance(data, dict) else {}
        books = od.get("bookmakers", {}) or {}
        probs = []
        for slug, book in books.items():
            mk = (book.get("markets") or {}).get("181")
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
                "team1": p1, "team2": p2, "p1": med[0],
                "source": "OddsPapi median de-vigged (%d books, median: %s)" % (len(probs), med[1]),
                "url": "https://oddspapi.io/sports/esports/lol",
            })
    return out


# ---------------------------------------------------------------------------
# 3) Leaguepedia Elo (polite: one batch per run, persistent cache)
# ---------------------------------------------------------------------------

LEAGUEPEDIA_CACHE = os.path.join(RAW_DIR, "leaguepedia_games.json")


def fetch_leaguepedia_games():
    """Fetch ONE 500-game batch and merge it into the persistent cache.

    Fandom rate-limits datacenter clients (observed 2026-10-21), so this makes
    at most a couple of requests per run and reuses the cache on any failure.
    Returns (games, status_string).
    """
    cache = {"games": [], "fetched_at": "", "last_fetch_status": "never"}
    if os.path.exists(LEAGUEPEDIA_CACHE):
        try:
            cache = json.load(open(LEAGUEPEDIA_CACHE, "r", encoding="utf-8"))
        except Exception:
            pass
    games = cache.get("games", [])

    status = "offline (cache only)"
    if not OFFLINE:
        since = (NOW - timedelta(days=LEAGUEPEDIA_WINDOW_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
        q = urllib.parse.urlencode({
            "action": "cargoquery",
            "format": "json",
            "tables": "ScoreboardGames=SG",
            "fields": "SG.Team1,SG.Team2,SG.Winner,SG.DateTime_UTC",
            "where": "SG.DateTime_UTC >= '%s' AND SG.Winner IS NOT NULL" % since,
            "order_by": "SG.DateTime_UTC DESC",
            "limit": "500",
        })
        known = set((g[0], g[1], g[3]) for g in games)
        new_rows = 0
        try:
            data, http_status = common.http_get_json(LEAGUEPEDIA_API + "?" + q,
                                                      timeout=30, retries=1, backoff=5)
            if isinstance(data, dict) and data.get("error"):
                status = "rate-limited/errored (%s) - cache reused" % (
                    data["error"].get("code", "unknown"))
            else:
                for r in (data.get("cargoquery") or []):
                    t = r.get("title", r) if isinstance(r, dict) else {}
                    a = t.get("Team1", "")
                    b = t.get("Team2", "")
                    w = str(t.get("Winner", ""))
                    dt = t.get("DateTime UTC") or t.get("DateTime_UTC") or ""
                    if not (a and b and w in ("1", "2")):
                        continue
                    if (a, b, dt) in known:
                        continue
                    games.append([a, b, w, dt])
                    known.add((a, b, dt))
                    new_rows += 1
                status = "ok (%d new games, HTTP %s)" % (new_rows, http_status)
        except Exception as e:
            status = "fetch error (%s) - cache reused" % e

    window_start = NOW - timedelta(days=LEAGUEPEDIA_WINDOW_DAYS)
    games = [g for g in games if (game_start_to_dt(g[3]) or NOW) >= window_start]
    games.sort(key=lambda g: g[3])
    cache = {
        "games": games,
        "fetched_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_fetch_status": status,
        "window_days": LEAGUEPEDIA_WINDOW_DAYS,
        "source": LEAGUEPEDIA_WIKI,
    }
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(LEAGUEPEDIA_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    log("leaguepedia: %s; cache now %d games" % (status, len(games)))
    return games, status


def build_elo(games):
    """Elo (K=32, start 1500) over chronological results."""
    ratings, counts = {}, {}
    for a, b, w, _dt in games:
        na, nb = canon(a), canon(b)
        if not na or not nb:
            continue
        ra = ratings.get(na, 1500.0)
        rb = ratings.get(nb, 1500.0)
        ea = 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))
        actual_a = 1.0 if w == "1" else 0.0
        delta = 32.0 * (actual_a - ea)
        ratings[na] = ra + delta
        ratings[nb] = rb - delta
        counts[na] = counts.get(na, 0) + 1
        counts[nb] = counts.get(nb, 0) + 1
    return ratings, counts


SEED_RATINGS_PATH = os.path.join(REPO_ROOT, "data", "seeded_ratings.json")


def load_seed_ratings():
    """Bootstrap ratings from data/seeded_ratings.json.

    The seed is a snapshot of this same Elo model from an earlier run
    (added by the parallel session in PR #14): normalized team name ->
    {"team", "elo", "games"}. It is used to fill gaps in the live cache so
    teams with any recorded history are not stuck at UNRESOLVED while the
    rate-limited cache fills; rows resolved from it carry the seed's small
    sample counts, so they are labeled low confidence.
    """
    if not os.path.exists(SEED_RATINGS_PATH):
        return {}
    try:
        seeds = json.load(open(SEED_RATINGS_PATH, "r", encoding="utf-8"))
        return {k: (float(v.get("elo", 1500.0)), int(v.get("games", 1)))
                for k, v in seeds.items() if isinstance(v, dict)}
    except Exception as e:
        log("seed ratings load error: %s" % e)
        return {}


# ---------------------------------------------------------------------------
# 4) Per-match resolution
# ---------------------------------------------------------------------------

def find_polymarket_line(fixture, pm_markets):
    fa = fixture["team1"]
    fb = fixture["team2"]
    t0 = common.parse_iso(fixture["start_utc"])
    best, best_key = None, None
    for m in pm_markets:
        if m.get("closed"):
            continue
        outs = m.get("outcomes") or []
        if len(outs) != 2:
            continue
        o0, o1 = outs[0], outs[1]
        if o0.lower() in ("yes", "no") or o1.lower() in ("yes", "no"):
            continue  # futures, not a match market
        if not ((match_teams(o0, fa) and match_teams(o1, fb)) or
                (match_teams(o0, fb) and match_teams(o1, fa))):
            continue
        t1 = parse_pm_game_start(m.get("game_start")) or common.parse_iso(m.get("event_start"))
        if t0 and t1:
            delta_h = abs((t1 - t0).total_seconds()) / 3600.0
            if t0.date() == t1.date():
                window_h = 48.0
            else:
                window_h = 72.0
            if delta_h > window_h:
                continue
        else:
            delta_h = 9999.0
        q = (m.get("question") or "").lower()
        game_specific = ("game 1" in q) or ("first game" in q) or ("map 1" in q)
        key = (1 if game_specific else 0, delta_h, -(m.get("volume") or 0))
        if best_key is None or key < best_key:
            best_key = key
            best = m
    return best, best_key


def find_kalshi_futures(fixture, kl_markets):
    fa, fb = fixture["team1"], fixture["team2"]
    ma = mb = None
    for m in kl_markets:
        if m.get("mid") in (None, 0) or m.get("status") != "active":
            continue
        sub = m.get("subtitle") or ""
        if ma is None and match_teams(sub, fa):
            ma = m
        elif mb is None and match_teams(sub, fb):
            mb = m
    if ma and mb and ma.get("event_ticker") and ma["event_ticker"] == mb.get("event_ticker"):
        return ma, mb
    return None, None


def find_pinnacle(fixture, pk_matchups):
    fa, fb = fixture["team1"], fixture["team2"]
    t0 = common.parse_iso(fixture["start_utc"])
    for m in pk_matchups:
        if not ((match_teams(m.get("home"), fa) and match_teams(m.get("away"), fb)) or
                (match_teams(m.get("home"), fb) and match_teams(m.get("away"), fa))):
            continue
        t1 = common.parse_iso(m.get("start_time"))
        if t0 and t1 and abs((t1 - t0).total_seconds()) > 24 * 3600:
            continue
        return m
    return None


def resolve_match(m, pm_markets, kl_markets, pk_matchups, oddspapi_rows, ratings, elo_counts):
    row = {k: v for k, v in m.items() if k != "_lock_dt"}
    row["crowd_note"] = ("Hotspawn crowd % shown on the lobby is context only and is "
                         "NEVER used as a probability input.")

    prob = None
    method = ""
    evidence = ""
    confidence = ""
    market_url = ""
    source_url = ""
    pinnacle = None

    # 1) Commercial books (only with a configured key)
    for b in oddspapi_rows:
        if {norm_team(b["team1"]), norm_team(b["team2"])} == {norm_team(m["team1"]), norm_team(m["team2"])}:
            if norm_team(b["team1"]) == norm_team(m["team1"]):
                prob, evidence = b["p1"], b["source"]
            else:
                prob, evidence = 1.0 - b["p1"], b["source"]
            method = "MARKET_BOOKS"
            confidence = "High - established esportsbook lines, de-vigged"
            market_url = source_url = b["url"]
            break

    # 2) Polymarket per-match market
    if prob is None:
        pm_line, _key = find_polymarket_line(m, pm_markets)
        if pm_line:
            outs = pm_line["outcomes"]
            if match_teams(outs[0], m["team1"]):
                prob = pm_line["prices"][0]
            else:
                prob = pm_line["prices"][1]
            method = "MARKET_POLYMARKET"
            q = pm_line.get("question", "")
            ql = q.lower()
            game1 = ("game 1" in ql) or ("first game" in ql)
            evidence = "Polymarket market: %s" % q
            if game1:
                evidence += " (Game-1 market only - no series market found; flagged)"
            confidence = "High - prediction-market traded price"
            market_url = source_url = pm_line["url"]

    # 3) Our originated line from Kalshi tournament futures (ratio model)
    if prob is None:
        ma, mb = find_kalshi_futures(m, kl_markets)
        if ma and mb:
            fa, fb = float(ma["mid"]), float(mb["mid"])
            if fa + fb > 0:
                prob = fa / (fa + fb)
                method = "KALSHI_FUTURES"
                evidence = (
                    "Our own line: ratio model p(A)=f(A)/(f(A)+f(B)) on open Kalshi "
                    "tournament-futures mids, same event %s (A: %s=%.3f, B: %s=%.3f)"
                    % (ma["event_ticker"], m["team1"], fa, m["team2"], fb)
                )
                confidence = "Medium - our derived line from market futures (not a book line)"
                market_url = source_url = ma["url"]
                row["futures"] = {
                    "team1": {"ticker": ma["ticker"], "mid": fa, "url": ma["url"]},
                    "team2": {"ticker": mb["ticker"], "mid": fb, "url": mb["url"]},
                }

    # 4) Our originated Elo line (Leaguepedia community-wiki results)
    if prob is None:
        c1, c2 = canon(m["team1"]), canon(m["team2"])
        g1, g2 = elo_counts.get(c1, 0), elo_counts.get(c2, 0)
        if g1 > 0 or g2 > 0:
            r1 = ratings.get(c1, 1500.0)
            r2 = ratings.get(c2, 1500.0)
            raw_prob = 1.0 / (1.0 + 10.0 ** ((r2 - r1) / 400.0))
            min_g = min(g1, g2)
            shrinkage = min_g / (min_g + 10.0) if min_g > 0 else 0.25
            prob = 0.5 + (raw_prob - 0.5) * shrinkage
            method = "MODEL_ELO"
            evidence = (
                "Our originated Elo line (Leaguepedia results, past %dd): %s (Elo %d, %d games) "
                "vs %s (Elo %d, %d games), shrunk toward 50%% by sample size"
                % (LEAGUEPEDIA_WINDOW_DAYS, m["team1"], round(r1), g1,
                   m["team2"], round(r2), g2)
            )
            confidence = ("Medium - historical competitive data" if min_g >= 10
                          else "Low - thin team match history")
            source_url = LEAGUEPEDIA_WIKI
            row["elo"] = [round(r1), round(r2)]
            row["games"] = [g1, g2]

    # 5) Explicit 50/50 baseline
    if prob is None:
        prob = 0.50
        method = "UNRESOLVED"
        evidence = ("No external market line and no Leaguepedia match history recorded "
                    "for either team")
        confidence = "Unresolved - 50/50 baseline; no edge"
        source_url = LEAGUEPEDIA_WIKI

    prob = round(max(0.01, min(0.99, prob)), 4)
    prob2 = round(1.0 - prob, 4)
    row["prob_team1"] = prob
    row["prob_team2"] = prob2

    if prob > prob2:
        row["pick"] = m["team1"]
        row["pick_prob"] = prob
    elif prob2 > prob:
        row["pick"] = m["team2"]
        row["pick_prob"] = prob2
    else:
        # Nominal only - rendered as "No Edge" by the site; stored as team1
        # so downstream schema checks (pick in {team1, team2}) keep working.
        row["pick"] = m["team1"]
        row["pick_prob"] = prob
        row["no_edge"] = True

    row["method"] = method
    row["evidence"] = evidence
    row["confidence"] = confidence
    row["market_url"] = market_url
    row["source_url"] = source_url

    pinnacle = find_pinnacle(m, pk_matchups)
    row["pinnacle_listed"] = pinnacle is not None
    if pinnacle:
        row["pinnacle_url"] = pinnacle.get("url", "")
        row["pinnacle_note"] = (
            "Pinnacle lists a professional line for this matchup (no public price "
            "endpoint, verified 2026-10-21); used as coverage confirmation only."
        )
    return row


# ---------------------------------------------------------------------------
# 5) Main
# ---------------------------------------------------------------------------

def manifest_stale_sources():
    path = os.path.join(RAW_DIR, "manifest.json")
    out = []
    if os.path.exists(path):
        try:
            manifest = json.load(open(path, "r", encoding="utf-8"))
            for name, meta in manifest.items():
                if isinstance(meta, dict) and meta.get("stale"):
                    out.append(name)
        except Exception:
            pass
    return out


def main():
    log("starting pick generation pipeline (offline=%s)..." % OFFLINE)

    matches, fixture_how = get_hotspawn_matches()
    if not matches:
        print("ERROR: no fixtures available (offline and no snapshot).", file=sys.stderr)
        sys.exit(1)
    log("fixtures via %s: %d" % (fixture_how, len(matches)))

    pm_markets, pm_how = polymarket_markets()
    kl_markets, kl_how = kalshi_markets()
    pk_matchups, pk_how = pinnacle_matchups()
    oddspapi_rows = oddspapi_odds()

    games, leaguepedia_status = fetch_leaguepedia_games()
    ratings, elo_counts = build_elo(games)

    seed = load_seed_ratings()
    seed_used = 0
    for k, (elo, g) in seed.items():
        if k not in ratings:
            ratings[k] = elo
            elo_counts[k] = g
            seed_used += 1
    if seed_used and not games:
        elo_source = "seeded ratings snapshot only (Leaguepedia cache empty - rate limited)"
    elif seed_used:
        elo_source = "Leaguepedia cache + seeded bootstrap (%d seed teams)" % seed_used
    else:
        elo_source = "Leaguepedia cache"
    log("elo: %s (%d teams total)" % (elo_source, len(ratings)))

    pickable, excluded = [], []
    for m in matches:
        if m["_lock_dt"] is None or m["_lock_dt"] >= NOW - timedelta(seconds=30):
            pickable.append(m)
        else:
            excluded.append({
                "id": m["id"],
                "team1": m["team1"],
                "team2": m["team2"],
                "tournament": m["tournament"],
                "start_utc": m["start_utc"],
                "lock_utc": m["lock_utc"],
                "reason": "Pick lock time has passed on Hotspawn; no longer an "
                          "available pick (kept here for audit, not dropped).",
            })
    excluded.sort(key=lambda e: (e["start_utc"], e["id"]))
    log("pickable=%d excluded_stale=%d" % (len(pickable), len(excluded)))

    rows = [
        resolve_match(m, pm_markets, kl_markets, pk_matchups, oddspapi_rows, ratings, elo_counts)
        for m in pickable
    ]
    rows.sort(key=lambda r: (r["lock_utc"] or "9999", r["start_utc"], r["tournament"]))

    counts = {
        "MARKET_BOOKS": sum(1 for r in rows if r["method"] == "MARKET_BOOKS"),
        "MARKET_POLYMARKET": sum(1 for r in rows if r["method"] == "MARKET_POLYMARKET"),
        "KALSHI_FUTURES": sum(1 for r in rows if r["method"] == "KALSHI_FUTURES"),
        "MODEL_ELO": sum(1 for r in rows if r["method"] == "MODEL_ELO"),
        "UNRESOLVED": sum(1 for r in rows if r["method"] == "UNRESOLVED"),
    }

    debug = {
        "generated_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lobby": LOBBY_URL,
        "fixtures_via": fixture_how,
        "polymarket_markets": len(pm_markets),
        "polymarket_via": pm_how,
        "kalshi_markets": len(kl_markets),
        "kalshi_via": kl_how,
        "pinnacle_matchups": len(pk_matchups),
        "pinnacle_via": pk_how,
        "oddspapi_fixtures_priced": len(oddspapi_rows),
        "leaguepedia_status": leaguepedia_status,
        "elo_source": elo_source,
        "elo_teams": len(ratings),
        "elo_games": len(games),
        "seeded_teams_used": seed_used,
        "matches_total": len(matches),
        "matches_pickable": len(pickable),
        "matches_excluded_stale": len(excluded),
        "stale_sources": manifest_stale_sources(),
        "offline": OFFLINE,
    }

    payload = {
        "generated_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lobby": LOBBY_URL,
        "count": len(rows),
        "counts_by_method": counts,
        "stale_sources": manifest_stale_sources(),
        "excluded_stale": excluded,
        "debug": debug,
        "matches": rows,
    }

    os.makedirs(os.path.join(REPO_ROOT, "data"), exist_ok=True)
    with open(os.path.join(REPO_ROOT, "data", "picks.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    with open(os.path.join(REPO_ROOT, "data", "debug.json"), "w", encoding="utf-8") as f:
        json.dump(debug, f, indent=1, ensure_ascii=False)

    log("done: %d pickable matches. %s" % (len(rows), json.dumps(counts)))
    for r in rows:
        if r["method"] != "UNRESOLVED":
            log("  %s | %s vs %s | %.1f/%.1f | %s" % (
                (r["start_utc"] or "?")[:16], r["team1"][:20], r["team2"][:20],
                r["prob_team1"] * 100, r["prob_team2"] * 100, r["method"]))


if __name__ == "__main__":
    main()
