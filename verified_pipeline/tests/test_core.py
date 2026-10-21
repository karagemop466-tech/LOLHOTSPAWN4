import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from verified_pipeline.core import (HOTSPAWN_FEED, american_implied, build_dataset, dt, fit,
    history_estimate, iso, norm, pinnacle_candidates, polymarket_candidates,
    result_eligible, sanitize_inventory, validate_dataset)

NOW = datetime(2026, 10, 21, 21, tzinfo=timezone.utc)
OBSERVED = "2026-10-21T20:39:54Z"
START = "2026-10-22T12:00:00Z"
PRICE_URL = "https://guest.api.arcadia.pinnacle.com/0.1/leagues/225201/markets/straight"
META_URL = "https://guest.api.arcadia.pinnacle.com/0.1/leagues/225201/matchups"


def raw_fixture(id_="1", a="Alpha", b="Beta", competition="EM 2026 Summer Main Event", start=START):
    return {"id": id_, "sport_alias": "lol", "status": "scheduled", "participants0_name": a,
            "participants1_name": b, "competition_name": competition, "scheduled_start_time": str(int(dt(start).timestamp() * 1000)) if start else None,
            "lock_time": str(int((dt(start) - timedelta(minutes=5)).timestamp() * 1000)) if start else None}


def external(a="Alpha", b="Beta", pa=.6, start=START):
    return {"id": "synthetic", "team_a": a, "team_b": b, "probability_a": pa, "probability_b": 1-pa,
            "provider": "Synthetic test bookmaker", "method": "bookmaker", "scope": "series", "competition": "League of Legends - EMEA Masters",
            "start_utc": start, "observed_at": OBSERVED, "source_url": PRICE_URL, "metadata_url": META_URL,
            "provider_updated_at": None}


def build(fixtures=None, candidates=(), history=(), **kwargs):
    return build_dataset(fixtures or [raw_fixture()], inventory_at=kwargs.pop("inventory_at", OBSERVED),
                         now=kwargs.pop("now", NOW), candidates=candidates, history=history, **kwargs)


def result(id_, a, b, sa=2, sb=0, day="2026-10-16", **kwargs):
    return {"id": id_, "team_a": a, "team_b": b, "score_a": sa, "score_b": sb, "source_date": day,
            "completed": True, "best_of": 3, "season": "2026/27", "competition": "PRM2",
            "observed_on": "2026-10-19", "source_url": "https://www.primeleague.gg/en/matches/602058-hannover-esports-e-v-vs-regold-esport", **kwargs}


def training():
    return [result("a1", "Alpha", "Opponent 1"), result("a2", "Alpha", "Opponent 2"),
            result("b1", "Beta", "Opponent 3", 0, 2), result("b2", "Beta", "Opponent 2", 0, 2)]


class InventorySafety(unittest.TestCase):
    def test_crowd_and_hotspawn_history_never_cross_firewall(self):
        raw = {**raw_fixture(), "participants0_picked_pct": 99, "participants1_picked_pct": 1,
               "participants0_score": 2, "total_picks": 555, "probability_a": .99, "history": [{"win": True}]}
        safe = sanitize_inventory([raw])[0]
        for forbidden in ("participants0_picked_pct", "participants1_picked_pct", "total_picks", "probability_a", "participants0_score", "history"):
            self.assertNotIn(forbidden, safe)
        data = build([raw])
        self.assertIsNone(data["matches"][0]["probability_a"])
        self.assertIsNone(data["matches"][0]["pick"])

    def test_empty_inventory_is_a_hard_failure(self):
        for value in ([], {}, None, [raw_fixture(), raw_fixture()]):
            with self.assertRaises(ValueError):
                sanitize_inventory(value)

    def test_all_ids_including_elapsed_are_accounted_for(self):
        fixtures = [raw_fixture("1"), raw_fixture("2", start="2026-08-26T12:00:00Z")]
        data = build(fixtures)
        self.assertEqual({r["id"] for r in data["matches"]}, {"1", "2"})
        self.assertEqual(data["summary"]["listed"], 2)
        self.assertEqual(data["summary"]["elapsed"], 1)
        self.assertIsNone(next(r for r in data["matches"] if r["id"] == "2")["pick"])

    def test_stale_inventory_does_not_generate_picks(self):
        data = build(candidates=[external()], inventory_at="2026-10-20T00:00:00Z")
        self.assertFalse(data["inventory_fresh"])
        self.assertIsNone(data["matches"][0]["probability_a"])

    def test_provisional_duplicate_and_unknown_start_are_blank(self):
        for a, b, start in (("TBD", "Beta", START), ("Alpha", "Alpha", START), ("Alpha", "Beta", None)):
            with self.subTest(a=a, b=b, start=start):
                data = build([raw_fixture(a=a, b=b, start=start)], candidates=[external(a, b)])
                self.assertIsNone(data["matches"][0]["probability_a"])

    def test_locked_fixture_has_no_prematch_pick(self):
        fixture = raw_fixture()
        fixture["lock_time"] = str(int((NOW - timedelta(seconds=1)).timestamp()*1000))
        row = build([fixture], candidates=[external()])["matches"][0]
        self.assertEqual(row["state"], "locked")
        self.assertIsNone(row["pick"])

    def test_times_require_timezone_or_millisecond_epoch(self):
        self.assertIsNone(dt("2026-10-22 12:00:00"))
        self.assertIsNone(dt(1792670400))
        self.assertIsNone(dt(True))
        self.assertEqual(iso(dt("2026-10-22 12:00:00+00")), START)

    def test_no_fuzzy_academy_or_sponsor_normalization(self):
        self.assertEqual(norm("Locked IN"), norm("Locked In"))
        self.assertNotEqual(norm("AceGaming"), norm("ACEGaming Hearts"))
        self.assertNotEqual(norm("MT1 Esports"), norm("MT1 Vision"))
        self.assertNotEqual(norm("PvB"), norm("Phong Vũ Buffalo"))


class EvidenceSafety(unittest.TestCase):
    def test_exact_match_reverse_team_order_is_not_reversed_pick(self):
        row = build(candidates=[external("Beta", "Alpha", .7)])["matches"][0]
        self.assertEqual(row["probability_a"], .3)
        self.assertEqual(row["pick"], "Beta")
        self.assertTrue(row["evidence"][0]["reversed_to_inventory"])

    def test_map_scope_unknown_start_distant_date_wrong_competition_fail(self):
        cases = [{"scope": "map1"}, {"start_utc": None}, {"start_utc": "2026-10-24T12:00:00Z"},
                 {"competition": "Counter Strike"}, {"team_a": "Alpha Academy"}, {"observed_at": "2026-10-20T00:00:00Z"}]
        for changes in cases:
            with self.subTest(changes=changes):
                row = build(candidates=[{**external(), **changes}])["matches"][0]
                self.assertIsNone(row["probability_a"])

    def test_near_schedule_conflict_is_visible_not_silently_equal(self):
        row = build(candidates=[external(start="2026-10-22T16:00:00Z")])["matches"][0]
        self.assertIsNotNone(row["probability_a"])
        self.assertTrue(any("Schedule conflict" in f for f in row["flags"]))
        self.assertEqual(row["start_utc"], START)

    def test_ambiguous_rematches_reject_a_quote_for_both(self):
        rows = build([raw_fixture("1"), raw_fixture("2")], candidates=[external()])["matches"]
        self.assertTrue(all(r["probability_a"] is None for r in rows))

    def test_supported_tie_never_defaults_to_team_a(self):
        row = build(candidates=[external(pa=.5)])["matches"][0]
        self.assertEqual(row["probability_a"], .5)
        self.assertIsNone(row["pick"])
        self.assertEqual(row["method"], "bookmaker")

    def test_bookmaker_is_primary_not_unexplained_average(self):
        poly = {**external(pa=.8), "provider": "Prediction exchange", "method": "prediction_market", "id": "poly"}
        row = build(candidates=[poly, external(pa=.6)])["matches"][0]
        self.assertEqual(row["probability_a"], .6)
        self.assertEqual(len(row["evidence"]), 2)
        self.assertTrue(any("Providers disagree" in f for f in row["flags"]))

    def test_bad_source_scheme_rejected(self):
        row = build(candidates=[{**external(), "source_url": "javascript:alert(1)"}])["matches"][0]
        self.assertIsNone(row["pick"])

    def test_validator_rejects_unbacked_fills(self):
        data = build()
        data["matches"][0].update(probability_a=.5, probability_b=.5, pick="Alpha")
        with self.assertRaises(ValueError):
            validate_dataset(data)

    def test_validator_rejects_one_sided_null_or_nan(self):
        for b in (None, float("nan")):
            data = build()
            data["matches"][0].update(probability_a=.6, probability_b=b)
            with self.assertRaises(ValueError):
                validate_dataset(data)


class PinnacleScope(unittest.TestCase):
    def setUp(self):
        self.parent = {"id": 123, "type": "matchup", "parentId": None, "parent": None, "isLive": False, "status": "pending",
                       "league": {"name": "League of Legends - EMEA Masters", "sport": {"id": 12}}, "startTime": START,
                       "participants": [{"alignment": "home", "name": "Alpha"}, {"alignment": "away", "name": "Beta"}]}
        self.line = {"matchupId": 123, "type": "moneyline", "period": 0, "key": "s;0;m", "isAlternate": False, "status": "open",
                     "prices": [{"designation": "home", "price": -120}, {"designation": "away", "price": 110}]}

    def parse(self, parent=None, line=None):
        return pinnacle_candidates([parent or self.parent], [line or self.line], observed_at=OBSERVED, source_url=PRICE_URL, metadata_url=META_URL)

    def test_de_vig_reproducible(self):
        candidate = self.parse()[0]
        expected = (120/220)/((120/220)+(100/210))
        self.assertAlmostEqual(candidate["probability_a"], expected)
        self.assertAlmostEqual(candidate["probability_a"] + candidate["probability_b"], 1)
        self.assertIsNone(candidate["provider_updated_at"])

    def test_map_alternate_closed_spread_bad_designations_rejected(self):
        for changes in ({"period": 1}, {"key": "s;1;m"}, {"isAlternate": True}, {"status": "closed"}, {"type": "spread"},
                        {"prices": [{"designation": "home", "price": -120}, {"designation": "home", "price": 110}]}):
            self.assertEqual(self.parse(line={**self.line, **changes}), [])

    def test_live_child_special_wrong_sport_rejected(self):
        for changes in ({"isLive": True}, {"parentId": 321}, {"type": "special"}, {"status": "started"},
                        {"league": {"name": "Counter Strike", "sport": {"id": 12}}}):
            self.assertEqual(self.parse(parent={**self.parent, **changes}), [])

    def test_invalid_american_quotes_rejected(self):
        for value in (0, 99, -99, True, float("nan")):
            with self.assertRaises(ValueError):
                american_implied(value)


class PolymarketScope(unittest.TestCase):
    def setUp(self):
        self.market = {"id": "123", "question": "LoL: Alpha vs Beta (BO5) - EMEA Masters", "sportsMarketType": "moneyline",
                       "groupItemTitle": "Match Winner", "active": True, "closed": False, "acceptingOrders": True,
                       "outcomes": '["Alpha", "Beta"]', "outcomePrices": '["0.6", "0.4"]', "gameStartTime": START}

    def parse(self, **changes):
        return polymarket_candidates([{**self.market, **changes}], observed_at=OBSERVED, source_url="https://gamma-api.polymarket.com/events?tag_id=65")

    def test_series_accepted(self):
        self.assertEqual(len(self.parse()), 1)

    def test_game1_with_identical_prices_never_accepted(self):
        self.assertEqual(self.parse(sportsMarketType="child_moneyline", groupItemTitle="Game 1 Winner"), [])
        self.assertEqual(self.parse(question="LoL: Alpha vs Beta - Game 1 Winner"), [])

    def test_close_yesno_unknown_start_and_bad_sum_rejected(self):
        for changes in ({"closed": True}, {"outcomes": '["Yes", "No"]'}, {"gameStartTime": None},
                        {"outcomePrices": '["0.9", "0.9"]'}, {"acceptingOrders": False}):
            self.assertEqual(self.parse(**changes), [])


class HistorySafety(unittest.TestCase):
    def row(self):
        return build([raw_fixture(competition="PRM 2nd Division 26-27 Fall")])["matches"][0]

    def test_both_teams_need_two_real_dated_results(self):
        for records in ([], training()[:2], training()[:3]):
            model, reason = history_estimate(self.row(), records, NOW)
            self.assertIsNone(model)
            self.assertIn("Insufficient", reason)

    def test_reproducible_shrunken_log5_not_seeded_ratings(self):
        model, reason = history_estimate(self.row(), training(), NOW)
        self.assertFalse(reason)
        self.assertEqual(model["counts"], [2, 2])
        ra, rb = 4/6, 2/6
        raw = (ra-ra*rb)/(ra+rb-2*ra*rb)
        self.assertAlmostEqual(model["probability_a"], .5+(2/12)*(raw-.5), places=6)
        self.assertGreater(model["probability_a"], .5)
        self.assertLess(model["probability_a"], .6)
        self.assertEqual(set(model["training_ids"]), {"a1", "a2", "b1", "b2"})

    def test_future_result_undated_wrong_competition_season_and_profile_rejected(self):
        record = training()[0]
        for changes in ({"source_date": "2026-10-23"}, {"source_date": "not a date"}, {"completed": False},
                        {"score_a": 0, "score_b": 0}, {"best_of": 1}, {"observed_on": "2026-10-22"},
                        {"source_url": "https://example.com/profile"}):
            self.assertFalse(result_eligible({**record, **changes}, NOW))
        for changes in ({"competition": "PRM3"}, {"season": None}, {"season": "2025/26"}):
            records = [{**r, **changes} for r in training()]
            self.assertIsNone(history_estimate(self.row(), records, NOW)[0])

    def test_timezone_unknown_uses_conservative_day_bound(self):
        r = result("x", "Alpha", "Opponent", day="2026-10-20")
        self.assertFalse(result_eligible(r, datetime(2026, 10, 21, 19, tzinfo=timezone.utc)))
        self.assertTrue(result_eligible(r, NOW))

    def test_duplicates_do_not_inflate_samples(self):
        records = [training()[0], training()[0], training()[2], training()[2]]
        self.assertIsNone(history_estimate(self.row(), records, NOW)[0])

    def test_aliases_and_old_history_are_not_filled(self):
        records = [{**r, "team_a": r["team_a"] + " Academy"} for r in training()]
        self.assertIsNone(history_estimate(self.row(), records, NOW)[0])
        old = [{**r, "source_date": "2026-10-01"} for r in training()]
        model, reason = history_estimate(self.row(), old, NOW)
        self.assertIsNone(model)
        self.assertIn("stale", reason)

    def test_equal_partial_records_produce_tie_not_team_a_pick(self):
        records = [result("a1", "Alpha", "O1"), result("a2", "Alpha", "O2", 0, 2),
                   result("b1", "Beta", "O3"), result("b2", "Beta", "O2", 0, 2)]
        row = build([raw_fixture(competition="PRM 2nd Division 26-27 Fall")], history=records)["matches"][0]
        self.assertEqual(row["probability_a"], .5)
        self.assertIsNone(row["pick"])
        self.assertEqual(row["method"], "model")


if __name__ == "__main__":
    unittest.main()
