"""Offline smoke test for the collector pipeline.

Stubs common.http_get_json with canned responses shaped like the REAL API
payloads captured during source verification (2026-10-21), runs the three
collector steps, and asserts the expected matching/pick behaviour.

Run from a scratch copy of the repo (never the live data/ dir):
    cp -r <repo> /tmp/smoke && cd /tmp/smoke && python3 test/offline_smoke.py
"""

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "collector"))

import common  # noqa: E402


def iso2ms(s):
    return str(int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
                   .replace(tzinfo=timezone.utc).timestamp() * 1000))


def fx(i, comp, a, b, start, tier="c", stage="waiting for information", pts=10):
    return {
        "id": str(i), "competition_id": "999", "competition_name": comp,
        "sport_alias": "lol", "sport_name": "League of Legends",
        "status": "scheduled",
        "scheduled_start_time": iso2ms(start), "lock_time": iso2ms(start),
        "lock_offset_sec": 300, "offered_points": pts, "base_points": pts,
        "best_of": None, "series_format": None, "tier": tier, "stage": stage,
        "points_breakdown": {"game_multiplier": 1.25, "tier_multiplier": 1,
                             "series_multiplier": 1, "stage_multiplier": 1,
                             "tournament_multiplier": 1},
        "start_time": None, "end_time": None, "total_picks": 0,
        "participants0_id": "1", "participants0_name": a,
        "participants0_picked_percent": 0, "participants0_score": 0,
        "participants1_id": "2", "participants1_name": b,
        "participants1_picked_percent": 0, "participants1_score": 0,
    }


# --- canned responses (shapes verified against live APIs 2026-10-21) --------
HOTSPAWN_FIXTURES = [
    fx(501, "Benelux Ascend Series 2026 Summer Split", "Mind Blue eSports",
       "LAST DANCE", "2026-10-21T16:00:00Z"),
    fx(502, "World Championship 2026", "G2", "Dplus KIA",
       "2026-10-23T20:00:00Z", tier="s", pts=30),
    fx(503, "World Championship 2026", "Anyone's Legend", "Karmine Corp",
       "2026-10-23T19:00:00Z", tier="s", pts=30),
    fx(504, "World Championship 2026", "T1", "Gen.G",
       "2026-10-24T11:00:00Z", tier="s", pts=30),
    fx(505, "EMEA Masters 2026", "Solary", "Galions",
       "2026-10-22T16:00:00Z", tier="b", stage="playoffs", pts=15),
    fx(506, "FPL 2026 Summer Playoffs", "Epic Avalanche", "Finnish Red Mafia",
       "2026-10-22T07:00:00Z"),
]

POLY_SPORTS = [
    {"id": 630, "sport": "ufl", "name": "UFL", "primaryTagId": 105925, "series": "12553"},
    {"id": 39, "sport": "lol", "name": "LoL", "primaryTagId": 65, "series": "10311",
     "resolution": "https://liquipedia.net/leagueoflegends/Main_Page"},
]


def pm_event(slug, title, start, end, markets):
    return {"id": "1214242", "slug": slug, "title": title, "startDate": start,
            "endDate": end, "active": True, "closed": False, "markets": markets}


def pm_market(qid, question, outcomes, prices, game_start=None, group=None, vol=1000.0):
    m = {"id": str(qid), "question": question,
         "outcomes": json.dumps(outcomes), "outcomePrices": json.dumps(prices),
         "closed": False, "active": True, "volumeNum": vol}
    if game_start:
        m["gameStartTime"] = game_start
    if group:
        m["groupItemTitle"] = group
    return m


POLY_EVENTS = [
    pm_event("lol-g2-dk-2026-10-23",
             "LoL: G2 Esports vs Dplus KIA (BO1) - Worlds Group Stage",
             "2026-10-18T20:50:18Z", "2026-10-24T02:00:00Z",
             [pm_market(5906214,
                        "LoL: G2 Esports vs Dplus KIA (BO1) - Worlds Group Stage",
                        ["G2 Esports", "Dplus KIA"], ["0.395", "0.605"],
                        game_start="2026-10-23 20:00:00+00", vol=290206.78)]),
    pm_event("worlds-2026-winner", "Worlds 2026: Winner",
             "2026-09-09T02:42:46Z", "2026-11-29T04:59:00Z",
             [pm_market(4397022, "Will Gen.G win Worlds 2026?", ["Yes", "No"],
                        ["0.335", "0.665"], group="Gen.G", vol=198475.99),
              pm_market(4397025, "Will T1 win Worlds 2026?", ["Yes", "No"],
                        ["0.155", "0.845"], group="T1", vol=147699.52)]),
    pm_event("emea-masters-solary-galions", "LoL: Solary vs Galions (BO5) - EMEA Masters",
             "2026-10-18T00:00:00Z", "2026-10-23T00:00:00Z",
             [pm_market(6000001, "LoL: Solary vs Galions (BO5) - EMEA Masters",
                        ["Solary", "Galions"], ["0.55", "0.45"],
                        game_start="2026-10-22 16:00:00+00", vol=42000.0)]),
]

KALSHI_SERIES = {"series": {"ticker": "KXLOL", "title": "League of Legends",
                            "category": "Sports", "tags": ["Esports"],
                            "settlement_sources": [{"name": "LoL Esports",
                                                    "url": "https://lolesports.com/en-US/"}]}}


def kl_market(ticker, title, sub, event, bid, ask, mid):
    return {"ticker": ticker, "title": title, "yes_sub_title": sub,
            "event_ticker": event, "status": "active",
            "yes_bid_dollars": str(bid), "yes_ask_dollars": str(ask),
            "last_price_dollars": str(mid), "volume_fp": "100.0"}


KALSHI_MARKETS = {"cursor": "", "markets": [
    kl_market("KXLOL-WORLDS26-T1", "Will T1 win League of Legends Worlds?", "T1",
              "KXLOL-WORLDS26", 0.17, 0.18, 0.175),
    kl_market("KXLOL-WORLDS26-GG", "Will Gen.G win League of Legends Worlds?", "Gen.G",
              "KXLOL-WORLDS26", 0.32, 0.34, 0.33),
    kl_market("KXLOL-WORLDS26-TL", "Will Team Liquid win League of Legends Worlds?",
              "Team Liquid", "KXLOL-WORLDS26", 0.01, 0.02, 0.015),
]}

PINNACLE_SPORTS = [{"id": 12, "name": "E Sports", "matchupCount": 43}]
PINNACLE_LEAGUES = [
    {"id": 9587, "name": "League of Legends - World Championship", "matchupCount": 10},
    {"id": 225201, "name": "League of Legends - EMEA Masters", "matchupCount": 1},
    {"id": 276139, "name": "CS2 - DraculaN", "matchupCount": 2},
]


def pk_matchup(mid, home, away, start, bo):
    return {"id": mid, "type": "matchup", "startTime": start, "bestOfX": bo,
            "status": "pending", "hasMarkets": True, "parent": None,
            "participants": [{"alignment": "home", "name": home},
                             {"alignment": "away", "name": away}]}


PINNACLE_MATCHUPS = {
    "9587": [pk_matchup(1638750815, "G2", "Dplus KIA", "2026-10-23T20:00:00Z", 1),
             pk_matchup(1638750902, "Anyone's Legend", "Karmine Corp",
                        "2026-10-23T19:00:00Z", 1)],
    "225201": [pk_matchup(1638709103, "Solary", "Galions", "2026-10-22T16:00:00Z", 5)],
}


def stub_http_get_json(url, timeout=60, retries=3, backoff=5):
    u = url.split("?")[0]
    if u.endswith("/api/v1/fixtures"):
        return list(HOTSPAWN_FIXTURES), 200
    if u.endswith("/sports") and "polymarket" in url:
        return list(POLY_SPORTS), 200
    if u.endswith("/events"):
        offset = 0
        if "offset=" in url:
            offset = int(url.split("offset=")[1].split("&")[0])
        return POLY_EVENTS[offset:offset + 100], 200
    if u.endswith("/series/KXLOL"):
        return KALSHI_SERIES, 200
    if u.endswith("/markets") and "kalshi" in url:
        return KALSHI_MARKETS, 200
    if u.endswith("/sports") and "pinnacle" in url:
        return list(PINNACLE_SPORTS), 200
    if u.endswith("/leagues"):
        return list(PINNACLE_LEAGUES), 200
    if "/leagues/" in u and u.endswith("/matchups"):
        lid = u.split("/leagues/")[1].split("/")[0]
        return PINNACLE_MATCHUPS.get(lid, []), 200
    if u.endswith("/markets") and "pinnacle" in url:
        return {"detail": "The requested URL was not found on the server."}, 404
    raise AssertionError("unexpected URL in smoke test: %s" % url)


def main():
    # isolated scratch repo copy
    tmp = tempfile.mkdtemp(prefix="smoke-")
    for item in ("collector", "test"):
        src = os.path.join(REPO, item)
        dst = os.path.join(tmp, item)
        shutil.copytree(src, dst)
    os.chdir(tmp)
    # re-import the copied common so REPO_ROOT points at tmp
    for mod in ("common", "fetch_hotspawn", "fetch_odds", "build"):
        sys.modules.pop(mod, None)
    sys.path.insert(0, os.path.join(tmp, "collector"))
    import common as tcommon  # noqa: E402
    import fetch_hotspawn as fhs  # noqa: E402
    import fetch_odds as fo  # noqa: E402
    import build as bld  # noqa: E402
    tcommon.http_get_json = stub_http_get_json

    fhs.main()
    fo.main()
    bld.main()

    data = tcommon.read_json(os.path.join(tmp, "data", "matches.json"))
    by_id = {m["hotspawn_id"]: m for m in data["matches"]}

    # 1. G2 vs DK -> market line from Polymarket + Pinnacle coverage
    g2 = by_id["502"]
    assert g2["pick_basis"] == "market-line", g2
    assert abs(g2["prob_team_a"] - 0.395) < 1e-9 and abs(g2["prob_team_b"] - 0.605) < 1e-9
    assert g2["pick"] == "Dplus KIA" and g2["pick_side"] == "b"
    assert g2["pinnacle_covered"] is True
    assert any(l["source"] == "Polymarket" and l["kind"] == "match-winner-market"
               for l in g2["lines"])
    assert any(l["source"] == "Pinnacle" for l in g2["lines"])
    pm_link = [l for l in g2["lines"] if l["source"] == "Polymarket"][0]["url"]
    assert pm_link == "https://polymarket.com/event/lol-g2-dk-2026-10-23"

    # 2. AL vs KC -> unresolved (no Polymarket market, no futures inputs)
    al = by_id["503"]
    assert al["pick_basis"] is None and al["pick"] is None
    assert al["prob_team_a"] is None and al["prob_team_b"] is None
    assert "no-external-market-found" in al["flags"]
    assert al["pinnacle_covered"] is True

    # 3. T1 vs Gen.G -> derived estimate from Kalshi futures
    t1 = by_id["504"]
    assert t1["pick_basis"] == "derived-estimate", t1
    exp_a = 0.175 / (0.175 + 0.33)
    assert abs(t1["prob_team_a"] - exp_a) < 1e-9
    assert t1["pick"] == "Gen.G"
    assert any(l["kind"] == "derived-estimate-input" for l in t1["lines"])

    # 4. Solary vs Galions -> EMEA Masters market line
    sol = by_id["505"]
    assert sol["pick_basis"] == "market-line" and sol["pick"] == "Solary"
    assert sol["pinnacle_covered"] is True

    # 5. Low-tier fixtures -> unresolved, no lines
    for i in ("501", "506"):
        m = by_id[i]
        assert m["pick_basis"] is None and m["lines"] == [] or \
            all(l["kind"] == "listed-matchup-coverage" for l in m["lines"]), m

    s = data["summary"]
    assert s["total_matches"] == 6
    assert s["market_line"] == 2 and s["derived_estimate"] == 1 and s["unresolved"] == 3
    assert s["pinnacle_covered"] == 3
    print("\nSMOKE TEST PASSED:", json.dumps(s))
    print("scratch dir:", tmp)


if __name__ == "__main__":
    main()
