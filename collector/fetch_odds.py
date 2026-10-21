"""Fetch external betting / prediction-market lines for LoL.

Sources (all verified 2026-10-21, see methodology.html):

  1. Polymarket (prediction market; per-match "Match Winner" markets and
     tournament futures). Public gamma API, no key required.
       GET https://gamma-api.polymarket.com/sports
       GET https://gamma-api.polymarket.com/events?tag_id=65&closed=false&limit=<n>&offset=<k>
     Public page per event: https://polymarket.com/event/<event-slug>

  2. Kalshi (regulated US prediction market; KXLOL "League of Legends"
     series - currently tournament futures). Public API, no key required.
       GET https://api.elections.kalshi.com/trade-api/v2/series/KXLOL
       GET https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXLOL&status=open
     Public page per market: https://kalshi.com/markets/<ticker>

  3. Pinnacle (established esports bookmaker; lists LoL leagues and
     matchups). Public guest API, no key required.
       GET https://guest.api.arcadia.pinnacle.com/0.1/sports
       GET https://guest.api.arcadia.pinnacle.com/0.1/sports/12/leagues
       GET https://guest.api.arcadia.pinnacle.com/0.1/leagues/<id>/matchups
     LIMITATION: no public price endpoint was found on 2026-10-21
     (GET /0.1/matchups/<id>/markets -> 404, GET /0.1/markets?matchupId=<id>
     -> 404, non-guest host -> 404). Pinnacle is therefore used to verify
     that a match carries a professional book line (coverage flag); the
     numeric probabilities come from Polymarket/Kalshi. This limitation is
     published on the Flagged for Review page.

Outputs (committed for audit):
  data/raw/polymarket_lol_markets.json   normalized extract of open LoL markets
  data/raw/kalshi_lol_markets.json       normalized extract of open KXLOL markets
  data/raw/pinnacle_lol_matchups.json    normalized extract of LoL matchups
  data/raw/manifest.json                 fetch metadata (merged)
The full Polymarket events response is saved as a workflow artifact only
(too large for git); the committed file is a lossless extract of the fields
we actually use.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


# ---------------------------------------------------------------------------
# Polymarket
# ---------------------------------------------------------------------------
def fetch_polymarket():
    common.log("polymarket: verifying LoL sport entry in /sports")
    sports, status = common.http_get_json(common.POLYMARKET_GAMMA_BASE + "/sports")
    if status != 200 or not isinstance(sports, list):
        raise RuntimeError("polymarket /sports failed (HTTP %s)" % status)
    lol_sport = None
    for s in sports:
        if s.get("sport") == "lol":
            lol_sport = s
            break
    if lol_sport is None:
        raise RuntimeError("polymarket: no 'lol' sport entry found")
    tag_id = int(lol_sport["primaryTagId"])
    common.log("polymarket: LoL sport id=%s slug=%s primaryTagId=%s" %
        (lol_sport.get("id"), lol_sport.get("sport"), tag_id))

    events = []
    offset = 0
    limit = 100
    while True:
        url = ("%s/events?tag_id=%d&closed=false&limit=%d&offset=%d"
               % (common.POLYMARKET_GAMMA_BASE, tag_id, limit, offset))
        page, status = common.http_get_json(url)
        if status != 200 or not isinstance(page, list):
            raise RuntimeError("polymarket /events failed (HTTP %s)" % status)
        events.extend(page)
        if len(page) < limit:
            break
        offset += limit
        if offset > 5000:  # safety
            break
    common.log("polymarket: fetched %d open LoL events" % len(events))

    markets = []
    for ev in events:
        ev_slug = ev.get("slug")
        ev_title = ev.get("title") or ""
        ev_start = ev.get("startDate")
        ev_end = ev.get("endDate")
        for m in ev.get("markets", []):
            try:
                outcomes = json.loads(m.get("outcomes") or "[]")
                prices = json.loads(m.get("outcomePrices") or "[]")
            except Exception:
                continue
            if len(outcomes) != 2 or len(prices) != 2:
                continue
            try:
                p0, p1 = float(prices[0]), float(prices[1])
            except Exception:
                continue
            markets.append({
                "event_id": str(ev.get("id")),
                "event_slug": ev_slug,
                "event_title": ev_title,
                "event_start": ev_start,
                "event_end": ev_end,
                "market_id": str(m.get("id")),
                "question": m.get("question"),
                "group_item_title": m.get("groupItemTitle"),
                "outcomes": outcomes,
                "prices": [p0, p1],
                "game_start": m.get("gameStartTime"),
                "volume": m.get("volumeNum"),
                "closed": bool(m.get("closed")),
                "url": "https://polymarket.com/event/%s" % ev_slug,
                "api_url": "%s/markets/%s" % (common.POLYMARKET_GAMMA_BASE, m.get("id")),
            })
    open_markets = [m for m in markets if not m["closed"]]
    common.log("polymarket: %d open markets extracted" % len(open_markets))

    payload = {
        "source": "Polymarket (gamma API)",
        "sport": {"id": lol_sport.get("id"), "slug": "lol",
                  "primaryTagId": tag_id,
                  "resolution_source_hint": lol_sport.get("resolution")},
        "events_fetched": len(events),
        "markets": open_markets,
    }
    common.save_snapshot("polymarket_lol_markets.json",
                         common.POLYMARKET_GAMMA_BASE + "/events?tag_id=%d&closed=false" % tag_id,
                         payload, status)
    # Keep the full dump as a workflow artifact (not committed).
    artifact = os.environ.get("RUNNER_TEMP", ".")
    try:
        with open(os.path.join(artifact, "polymarket_lol_events_full.json"), "w") as f:
            json.dump(events, f)
    except Exception as e:
        common.log("warning: could not write artifact: %s" % e)
    return payload


# ---------------------------------------------------------------------------
# Kalshi
# ---------------------------------------------------------------------------
def fetch_kalshi():
    common.log("kalshi: verifying KXLOL series")
    series, status = common.http_get_json(
        "%s/series/%s" % (common.KALSHI_API_BASE, common.KALSHI_LOL_SERIES))
    if status != 200 or not isinstance(series, dict) or "series" not in series:
        raise RuntimeError("kalshi /series failed (HTTP %s)" % status)
    s = series["series"]
    common.log("kalshi: series %s title=%s category=%s tags=%s" %
        (s.get("ticker"), s.get("title"), s.get("category"), s.get("tags")))

    markets = []
    cursor = None
    while True:
        url = ("%s/markets?series_ticker=%s&status=open&limit=200"
               % (common.KALSHI_API_BASE, common.KALSHI_LOL_SERIES))
        if cursor:
            url += "&cursor=" + urllib_quote(cursor)
        page, status = common.http_get_json(url)
        if status != 200 or not isinstance(page, dict):
            raise RuntimeError("kalshi /markets failed (HTTP %s)" % status)
        for m in page.get("markets", []):
            yes_bid = _dec(m.get("yes_bid_dollars"))
            yes_ask = _dec(m.get("yes_ask_dollars"))
            mid = None
            if yes_bid is not None and yes_ask is not None:
                mid = (yes_bid + yes_ask) / 2.0
            markets.append({
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "subtitle": m.get("yes_sub_title"),
                "event_ticker": m.get("event_ticker"),
                "status": m.get("status"),
                "open_time": m.get("open_time"),
                "close_time": m.get("close_time"),
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "mid": mid,
                "last_price": _dec(m.get("last_price_dollars")),
                "volume": m.get("volume_fp"),
                "rules_primary": m.get("rules_primary"),
                "url": "https://kalshi.com/markets/%s" % m.get("ticker"),
                "api_url": "%s/markets/%s" % (common.KALSHI_API_BASE, m.get("ticker")),
            })
        cursor = page.get("cursor")
        if not cursor:
            break
    common.log("kalshi: %d open KXLOL markets extracted" % len(markets))

    payload = {
        "source": "Kalshi (KXLOL series)",
        "series": {"ticker": s.get("ticker"), "title": s.get("title"),
                   "settlement_sources": s.get("settlement_sources")},
        "markets": markets,
    }
    common.save_snapshot("kalshi_lol_markets.json",
                         "%s/markets?series_ticker=%s&status=open"
                         % (common.KALSHI_API_BASE, common.KALSHI_LOL_SERIES),
                         payload, status)
    return payload


def _dec(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def urllib_quote(s):
    import urllib.parse
    return urllib.parse.quote(str(s), safe="")


# ---------------------------------------------------------------------------
# Pinnacle
# ---------------------------------------------------------------------------
def fetch_pinnacle():
    common.log("pinnacle: verifying E Sports sport id")
    sports, status = common.http_get_json(common.PINNACLE_API_BASE + "/sports")
    if status != 200 or not isinstance(sports, list):
        raise RuntimeError("pinnacle /sports failed (HTTP %s)" % status)
    sport_id = None
    for s in sports:
        if s.get("name") == "E Sports":
            sport_id = s.get("id")
            break
    if sport_id is None:
        raise RuntimeError("pinnacle: no 'E Sports' sport found")

    leagues, status = common.http_get_json(
        "%s/sports/%s/leagues" % (common.PINNACLE_API_BASE, sport_id))
    if status != 200 or not isinstance(leagues, list):
        raise RuntimeError("pinnacle /leagues failed (HTTP %s)" % status)
    lol_leagues = [l for l in leagues if (l.get("name") or "").startswith("League of Legends")]
    common.log("pinnacle: %d LoL leagues with lines: %s" %
        (len(lol_leagues), [l.get("name") for l in lol_leagues]))

    matchups = []
    for lg in lol_leagues:
        mid_url = "%s/leagues/%s/matchups" % (common.PINNACLE_API_BASE, lg["id"])
        page, status = common.http_get_json(mid_url)
        if status != 200 or not isinstance(page, list):
            common.log("pinnacle: league %s matchups fetch failed (HTTP %s)" % (lg["id"], status))
            continue
        for m in page:
            if m.get("type") != "matchup":
                continue  # skip props/specials
            parts = m.get("participants") or []
            home = next((p.get("name") for p in parts if p.get("alignment") == "home"), None)
            away = next((p.get("name") for p in parts if p.get("alignment") == "away"), None)
            if not home or not away:
                continue
            # Try the (currently unavailable) public price endpoint; keep the
            # attempt honest - if it ever starts working, use it.
            odds = None
            try:
                mk, mk_status = common.http_get_json(
                    "%s/matchups/%s/markets" % (common.PINNACLE_API_BASE, m.get("id")))
                if mk_status == 200 and isinstance(mk, list):
                    odds = {"raw": mk}
            except Exception:
                pass
            matchups.append({
                "matchup_id": str(m.get("id")),
                "league_id": lg.get("id"),
                "league_name": lg.get("name"),
                "home": home,
                "away": away,
                "start_time": m.get("startTime"),
                "best_of": m.get("bestOfX"),
                "status": m.get("status"),
                "has_markets": bool(m.get("hasMarkets")),
                "public_prices_available": odds is not None,
                "odds": odds,
                "url": "%s/matchups/%s" % (common.PINNACLE_API_BASE, m.get("id")),
            })
    common.log("pinnacle: %d LoL matchups extracted" % len(matchups))

    payload = {
        "source": "Pinnacle (guest Arcadia API)",
        "sport_id": sport_id,
        "price_endpoint_status": ("no public price endpoint found on 2026-10-21 "
                                  "(matchups/<id>/markets and markets?matchupId=<id> both 404)"),
        "leagues": [{"id": l.get("id"), "name": l.get("name"),
                     "matchupCount": l.get("matchupCount")} for l in lol_leagues],
        "matchups": matchups,
    }
    common.save_snapshot("pinnacle_lol_matchups.json",
                         "%s/sports/%s/leagues" % (common.PINNACLE_API_BASE, sport_id),
                         payload, status)
    return payload


SNAPSHOT_NAMES = {
    "polymarket": "polymarket_lol_markets.json",
    "kalshi": "kalshi_lol_markets.json",
    "pinnacle": "pinnacle_lol_matchups.json",
}


def main():
    failures = []
    for name, fn in (("polymarket", fetch_polymarket),
                     ("kalshi", fetch_kalshi),
                     ("pinnacle", fetch_pinnacle)):
        try:
            fn()
        except Exception as e:
            common.log("ERROR: %s fetch failed: %s" % (name, e))
            failures.append(name)
            try:
                common.save_snapshot(SNAPSHOT_NAMES[name], "(fetch failed)", None, None)
            except Exception:
                pass

    if failures and len(failures) == 3:
        common.fail("all odds sources failed: %s" % ", ".join(failures))
    if failures:
        common.log("WARNING: continuing with degraded sources (failed: %s)" % ", ".join(failures))
        common.log("degraded-source state is recorded in data/raw/manifest.json and surfaced on the site")


if __name__ == "__main__":
    main()
