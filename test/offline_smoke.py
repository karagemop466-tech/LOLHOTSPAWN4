#!/usr/bin/env python3
"""Offline smoke test for the canonical pick pipeline (scripts/update_picks.py).

Builds a temp-dir replica of the repo with fabricated-but-realistically-shaped
raw snapshots (matching the verified API payload shapes recorded in
COORDINATION.md), runs update_picks.py in --offline mode, and asserts:

  * Polymarket match lines: G2/DK 0.395/0.605 -> pick Dplus KIA
    (plus Pinnacle coverage flag on the same row)
  * Verified alias: Hotspawn "LØS" == Polymarket/Kalshi "LOS"
    (T1/LØS market line -> pick T1)
  * Game-1-only market is used AND flagged (Galions/Solary)
  * Kalshi futures ratio model (TL 0.015 vs CFO 0.005 -> TL 75%)
  * Leaguepedia Elo model from the persistent cache (Venus beats Nameless)
  * UNRESOLVED 50/50 with no_edge (no invented favorite)
  * Stale (locked-out) fixture moved to excluded_stale, not matches
  * Manifest stale source surfaced in stale_sources

Run: python3 test/offline_smoke.py   (exits 0 with "SMOKE TEST PASSED" on success)
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def ms(dt):
    return str(int(dt.timestamp() * 1000))


def fixture(mid, t1, t2, comp, start_dt, lock_dt):
    return {
        "id": str(mid),
        "competition_id": "1",
        "competition_name": comp,
        "sport_alias": "lol",
        "status": "scheduled",
        "scheduled_start_time": ms(start_dt),
        "lock_time": ms(lock_dt),
        "lock_offset_sec": 300,
        "offered_points": 10,
        "base_points": 10,
        "best_of": 1,
        "tier": "waiting for information",
        "stage": "waiting for information",
        "points_breakdown": {"game_multiplier": 1},
        "participants0_id": "100",
        "participants0_name": t1,
        "participants0_picked_percent": 0,
        "participants0_score": 0,
        "participants1_id": "101",
        "participants1_name": t2,
        "participants1_picked_percent": 0,
        "participants1_score": 0,
    }


def market(question, outs, prices, url, game_start=None, volume=1000.0, closed=False):
    return {
        "question": question,
        "outcomes": outs,
        "prices": prices,
        "url": url,
        "game_start": game_start,
        "event_start": None,
        "volume": volume,
        "closed": closed,
    }


def main():
    tmp = tempfile.mkdtemp(prefix="smoke-")
    try:
        # --- replicate repo layout -------------------------------------
        os.makedirs(os.path.join(tmp, "scripts"))
        os.makedirs(os.path.join(tmp, "collector"))
        os.makedirs(os.path.join(tmp, "data", "raw"))
        shutil.copy(os.path.join(HERE, "scripts", "update_picks.py"),
                    os.path.join(tmp, "scripts", "update_picks.py"))
        shutil.copy(os.path.join(HERE, "collector", "common.py"),
                    os.path.join(tmp, "collector", "common.py"))

        raw = os.path.join(tmp, "data", "raw")

        d_start_g2dk = NOW + timedelta(days=2)
        d_start_los = NOW + timedelta(days=2, hours=2)
        d_start_sly = NOW + timedelta(days=1)
        d_start_cfo = NOW + timedelta(days=3)
        d_start_mb = NOW + timedelta(days=4)
        d_start_venus = NOW + timedelta(days=5)
        d_stale_start = NOW - timedelta(days=10)

        fixtures = [
            fixture(1, "G2 Esports", "Dplus KIA", "Worlds 2026 Main Event",
                    d_start_g2dk, d_start_g2dk - timedelta(minutes=5)),
            fixture(2, "T1", "L\u00d8S", "Worlds 2026 Main Event",
                    d_start_los, d_start_los - timedelta(minutes=5)),
            fixture(3, "Galions", "Solary", "EMEA Masters 2026",
                    d_start_sly, d_start_sly - timedelta(minutes=5)),
            fixture(4, "Team Liquid", "CTBC Flying Oyster", "Worlds 2026 Main Event",
                    d_start_cfo, d_start_cfo - timedelta(minutes=5)),
            fixture(5, "Mind Blue eSports", "LAST DANCE", "Benelux Ascend Series",
                    d_start_mb, d_start_mb - timedelta(minutes=5)),
            fixture(6, "Venus", "Nameless", "Benelux Rising Playoffs",
                    d_start_venus, d_start_venus - timedelta(minutes=5)),
            fixture(7, "Old Team A", "Old Team B", "Some Old Cup",
                    d_stale_start, d_stale_start - timedelta(minutes=5)),
        ]
        with open(os.path.join(raw, "hotspawn_fixtures_scheduled.json"), "w") as f:
            json.dump(fixtures, f)

        with open(os.path.join(raw, "polymarket_lol_markets.json"), "w") as f:
            json.dump({"source": "test", "markets": [
                market("LoL: G2 Esports vs Dplus KIA (BO1) - Worlds Group Stage",
                       ["G2 Esports", "Dplus KIA"], [0.395, 0.605],
                       "https://polymarket.com/event/lol-g2-dk-test",
                       iso(d_start_g2dk), 290000.0),
                market("LoL: LOS vs T1 (BO1) - Worlds Group Stage",
                       ["LOS", "T1"], [0.125, 0.875],
                       "https://polymarket.com/event/lol-los-t1-test",
                       iso(d_start_los), 32000.0),
                market("LoL: Galions vs Solary - Game 1 Winner",
                       ["Galions", "Solary"], [0.515, 0.485],
                       "https://polymarket.com/event/lol-gal-sly-test",
                       iso(d_start_sly), 41000.0),
                market("Will a team from LCK win Worlds?",
                       ["Yes", "No"], [0.725, 0.275],
                       "https://polymarket.com/event/future-test"),
            ]}, f)

        with open(os.path.join(raw, "kalshi_lol_markets.json"), "w") as f:
            json.dump({"source": "test", "markets": [
                {"title": "Will Team Liquid win Worlds?", "subtitle": "Team Liquid",
                 "ticker": "KXLOL-TEST-TL", "mid": 0.015, "status": "active",
                 "event_ticker": "KXLOL-TEST",
                 "url": "https://kalshi.com/markets/KXLOL-TEST-TL"},
                {"title": "Will CTBC Flying Oyster win Worlds?", "subtitle": "CTBC Flying Oyster",
                 "ticker": "KXLOL-TEST-CFO", "mid": 0.005, "status": "active",
                 "event_ticker": "KXLOL-TEST",
                 "url": "https://kalshi.com/markets/KXLOL-TEST-CFO"},
                {"title": "Will T1 win Worlds?", "subtitle": "T1",
                 "ticker": "KXLOL-TEST-T1", "mid": 0.175, "status": "active",
                 "event_ticker": "KXLOL-TEST",
                 "url": "https://kalshi.com/markets/KXLOL-TEST-T1"},
            ]}, f)

        with open(os.path.join(raw, "pinnacle_lol_matchups.json"), "w") as f:
            json.dump({"source": "test", "matchups": [
                {"matchup_id": "1", "league_id": 9587,
                 "league_name": "League of Legends - World Championship",
                 "home": "G2 Esports", "away": "Dplus KIA",
                 "start_time": iso(d_start_g2dk), "best_of": 1, "status": "pending",
                 "has_markets": True, "public_prices_available": False, "odds": None,
                 "url": "https://guest.api.arcadia.pinnacle.com/0.1/matchups/1"},
            ]}, f)

        with open(os.path.join(raw, "leaguepedia_games.json"), "w") as f:
            games = []
            base = NOW - timedelta(days=60)
            for i in range(10):
                games.append([
                    "Venus", "Nameless", "1",
                    (base + timedelta(days=i * 3)).strftime("%Y-%m-%d %H:%M:%S"),
                ])
            json.dump({"games": games, "fetched_at": iso(NOW),
                       "last_fetch_status": "test-seeded", "window_days": 180}, f)

        with open(os.path.join(raw, "manifest.json"), "w") as f:
            json.dump({
                "hotspawn_fixtures_scheduled.json": {"stale": False, "fetched_at": iso(NOW)},
                "polymarket_lol_markets.json": {"stale": False, "fetched_at": iso(NOW)},
                "kalshi_lol_markets.json": {"stale": True, "fetched_at": iso(NOW - timedelta(hours=30))},
                "pinnacle_lol_matchups.json": {"stale": False, "fetched_at": iso(NOW)},
            }, f)

        # --- run the pipeline offline -----------------------------------
        proc = subprocess.run(
            [sys.executable, "scripts/update_picks.py", "--offline"],
            cwd=tmp, capture_output=True, text=True)
        print(proc.stdout)
        if proc.returncode != 0:
            print("STDERR:\n" + proc.stderr)
            raise SystemExit("update_picks.py exited %d" % proc.returncode)

        data = json.load(open(os.path.join(tmp, "data", "picks.json")))
        by_pair = {}
        for m in data["matches"]:
            by_pair[(m["team1"], m["team2"])] = m

        fails = []

        def check(label, cond, detail=""):
            if not cond:
                fails.append("%s %s" % (label, detail))

        check("count==6 pickable", data["count"] == 6,
              "(got %s)" % data["count"])
        check("excluded_stale==1", len(data["excluded_stale"]) == 1,
              "(got %s)" % len(data["excluded_stale"]))
        check("excluded id", data["excluded_stale"] and
              data["excluded_stale"][0]["id"] == "7",
              "(got %s)" % (data["excluded_stale"][:1]))
        c = data["counts_by_method"]
        check("counts", c == {"MARKET_BOOKS": 0, "MARKET_POLYMARKET": 3,
                              "KALSHI_FUTURES": 1, "MODEL_ELO": 1,
                              "UNRESOLVED": 1}, "(got %s)" % c)
        check("stale_sources", data["stale_sources"] == ["kalshi_lol_markets.json"],
              "(got %s)" % data["stale_sources"])

        g2dk = by_pair.get(("G2 Esports", "Dplus KIA"))
        check("g2dk exists", g2dk is not None)
        if g2dk:
            check("g2dk method", g2dk["method"] == "MARKET_POLYMARKET", g2dk["method"])
            check("g2dk probs", g2dk["prob_team1"] == 0.395 and g2dk["prob_team2"] == 0.605,
                  "%s/%s" % (g2dk["prob_team1"], g2dk["prob_team2"]))
            check("g2dk pick", g2dk["pick"] == "Dplus KIA", g2dk["pick"])
            check("g2dk pinnacle", g2dk.get("pinnacle_listed") is True)

        los = by_pair.get(("T1", "L\u00d8S"))
        check("los alias match", los is not None,
              "(teams: %s)" % [k for k in by_pair if "T1" in k[0]])
        if los:
            check("los method", los["method"] == "MARKET_POLYMARKET", los["method"])
            check("los pick", los["pick"] == "T1", los["pick"])
            check("los prob", los["prob_team1"] == 0.875, str(los["prob_team1"]))

        sly = by_pair.get(("Galions", "Solary"))
        check("sly exists", sly is not None)
        if sly:
            check("sly flagged game-1", "Game-1 market only" in sly["evidence"],
                  sly["evidence"][:80])
            check("sly pick", sly["pick"] == "Galions", sly["pick"])

        cfo = by_pair.get(("Team Liquid", "CTBC Flying Oyster"))
        check("cfo exists", cfo is not None)
        if cfo:
            check("cfo method", cfo["method"] == "KALSHI_FUTURES", cfo["method"])
            check("cfo pick", cfo["pick"] == "Team Liquid", cfo["pick"])
            check("cfo prob", abs(cfo["prob_team1"] - 0.75) < 0.001,
                  str(cfo["prob_team1"]))

        mb = by_pair.get(("Mind Blue eSports", "LAST DANCE"))
        check("mb exists", mb is not None)
        if mb:
            check("mb method", mb["method"] == "UNRESOLVED", mb["method"])
            check("mb 50/50", mb["prob_team1"] == 0.5 and mb["prob_team2"] == 0.5)
            check("mb no_edge", mb.get("no_edge") is True)

        ven = by_pair.get(("Venus", "Nameless"))
        check("venus exists", ven is not None)
        if ven:
            check("venus method", ven["method"] == "MODEL_ELO", ven["method"])
            check("venus pick", ven["pick"] == "Venus", ven["pick"])
            check("venus prob range", 0.6 < ven["prob_team1"] < 0.8,
                  str(ven["prob_team1"]))

        # schema invariants (same checks as the workflow verification step)
        for m in data["matches"]:
            assert m.get("team1") and m.get("team2")
            assert m.get("pick") in (m["team1"], m["team2"])
            assert abs((m.get("prob_team1", 0) + m.get("prob_team2", 0)) - 1.0) < 0.01
            assert m.get("method") in ("MARKET_BOOKS", "MARKET_POLYMARKET",
                                       "KALSHI_FUTURES", "MODEL_ELO", "UNRESOLVED")
            assert m.get("source_url") or m.get("market_url") or m.get("hotspawn_url")

        if fails:
            print("SMOKE TEST FAILED:")
            for f_ in fails:
                print("  -", f_)
            raise SystemExit(1)
        print("SMOKE TEST PASSED: %s" % json.dumps(c))
        print("scratch dir: %s" % tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
