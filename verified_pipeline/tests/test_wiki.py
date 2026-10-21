"""All rows here are synthetic parser fixtures, never publication input."""
import unittest
from datetime import timedelta

from verified_pipeline.core import build_dataset, dt, history_estimate, result_eligible
from verified_pipeline.wiki import PAGES, fields, page_url, parse_page, scheduled_utc, trusted_record
from test_core import NOW, OBSERVED, START, build, external, raw_fixture, result, training

SPEC = next(p for p in PAGES if p["key"] == "rivals")


def native(*, score_a="2", score_b="1", winner="1", day="2026-10-16", extra="", start="3", team_a="Alpha", team_b="Beta"):
    return ('{{TournamentGroups|groups=Group A|Group A=Alpha,Beta,Opponent 1,Opponent 2,Opponent 3}}'
            '{{MatchSchedule/Start|tab=Week 1|bestof=' + start + '}}'
            '{{MatchSchedule|initialorder=1|team1=' + team_a + '|team2=' + team_b + '|team1score=' + score_a + '|team2score=' + score_b + '|winner=' + winner + '|date=' + day + '|time=19:00|timezone=CET|dst=yes' + extra + '}}'
            '{{MatchSchedule/End}}')


class NativeWiki(unittest.TestCase):
    def parse(self, **kwargs):
        return parse_page(native(**kwargs), SPEC, observed_on="2026-10-21")

    def test_real_native_series_not_invented_per_game_rows(self):
        data = self.parse()
        self.assertEqual(len(data["records"]), 1)
        r = data["records"][0]
        self.assertEqual((r["score_a"], r["score_b"], r["best_of"]), (2, 1, 3))
        self.assertEqual(r["scheduled_utc"], "2026-10-16T17:00:00Z")
        self.assertEqual(r["group"], "Group A")
        self.assertTrue(trusted_record(r))
        self.assertTrue(result_eligible(r, NOW))
        self.assertNotIn("completion_utc", r)

    def test_unplayed_schedule_is_not_a_training_result(self):
        d = self.parse(score_a="", score_b="", winner="", day="2026-10-22")
        self.assertEqual(d["records"], [])
        self.assertEqual(len(d["schedule"]), 1)
        self.assertFalse(d["schedule"][0]["completed"])

    def test_future_preawarded_score_fails_causality(self):
        r = self.parse(day="2026-10-23")["records"][0]
        self.assertFalse(result_eligible(r, NOW))

    def test_wrong_winner_zero_zero_forfeit_draw_and_bad_bestof_rejected(self):
        for changes in ({"winner": "2"}, {"score_a": "0", "score_b": "0"}, {"extra": "|ff=1"},
                        {"extra": "|note=disqualified"}, {"score_a": "2*"}, {"score_a": "1", "score_b": "1"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.parse(**changes)["records"], [])
        with self.assertRaises(ValueError):
            self.parse(start="unknown")

    def test_nested_game_is_not_promoted_to_a_series(self):
        r = self.parse(extra="|games={{MatchSchedule/Game|winner=1|team1score=1|team2score=0}}")
        self.assertEqual(len(r["records"]), 1)
        self.assertEqual(r["records"][0]["score_a"], 2)

    def test_no_team_alias_or_year_or_timezone_inference(self):
        with self.assertRaises(ValueError):
            self.parse(team_a="[[Alpha|Alpha Academy]]")
        with self.assertRaises(ValueError):
            self.parse(day="10-16")
        self.assertIsNone(scheduled_utc("2026-10-16", "19:00", "CET", ""))
        self.assertIsNone(scheduled_utc("2026-10-16", "19:00", "UNPRINTED", "yes"))
        self.assertEqual(scheduled_utc("2026-11-16", "19:00", "CET", "no"), "2026-11-16T18:00:00Z")

    def test_changed_page_url_or_family_not_trusted(self):
        r = self.parse()["records"][0]
        for changes in ({"source_url": "https://lol.fandom.com/wiki/Team_Profile"},
                        {"source_url": page_url(SPEC) + "&invented=1"}, {"season": "2025"}, {"competition": "PRM3"}):
            self.assertFalse(trusted_record({**r, **changes}))
            self.assertFalse(result_eligible({**r, **changes}, NOW))

    def test_html_shell_duplicate_field_and_malformed_template_refused(self):
        for text in ("<html><div id='root'></div></html>", native()[:-2], native(extra="|winner=2")):
            with self.assertRaises(ValueError):
                parse_page(text, SPEC, observed_on="2026-10-21")

    def test_fresh_complete_page_replaces_old_corrected_observations(self):
        from verified_pipeline.wiki import collect
        corrected = self.parse(score_a="1", score_b="2", winner="2")
        previous = [{**self.parse()["records"][0], "id": "old-retracted"}]
        class Client:
            offline = False
            cache = {}
            def request(self, key, url, **kwargs):
                self.cache[key] = {"error": None}
                return corrected if key == "wiki-rivals" else None
            def observed(self, key):
                return OBSERVED
        records, schedule = collect(Client(), previous)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["score_a"], 1)
        self.assertNotEqual(records[0]["id"], "old-retracted")
        self.assertEqual(schedule[0]["observed_at"], OBSERVED)

    def test_solid_gaming_administrative_scores_are_quarantined(self):
        spec = next(p for p in PAGES if p["key"] == "komplett")
        d = parse_page(native(team_a="Solid Gaming"), spec, observed_on="2026-10-21")
        self.assertEqual(d["records"], [])
        self.assertTrue(d["schedule"][0]["result_unusable"])


class ContextAndPoolSafety(unittest.TestCase):
    def context(self, **changes):
        return {"competition": "rivals", "season": "2026", "team_a": "Alpha", "team_b": "Beta", "best_of": 3,
                "scheduled_utc": START, "source_url": page_url(SPEC), "observed_at": OBSERVED,
                "group": "Group A", "completed": False, **changes}

    def history(self):
        return [{**r, "competition": "rivals", "season": "2026", "group": "Group A", "source_url": page_url(SPEC)} for r in training()]

    def test_generalized_model_requires_current_exact_scheduled_format(self):
        f = raw_fixture(competition="RIVALS LEAGUE Season 2")
        for context in ([], [self.context(best_of=5)], [self.context(team_a="Alpha Academy")],
                        [self.context(observed_at="2026-10-20T00:00:00Z")],
                        [self.context(), self.context()], [self.context(completed=True)], [self.context(result_unusable=True)]):
            d = build_dataset([f], inventory_at=OBSERVED, now=NOW, history=self.history(), scheduled=context)
            self.assertIsNone(d["matches"][0]["probability_a"])
        d = build_dataset([f], inventory_at=OBSERVED, now=NOW, history=self.history(), scheduled=[self.context()])
        self.assertEqual(d["matches"][0]["method"], "model")
        self.assertEqual(d["matches"][0]["model"]["target_best_of"], 3)

    def test_different_groups_or_disconnected_pools_are_not_comparable(self):
        r = build([raw_fixture(competition="PRM 2nd Division 26-27 Fall")])["matches"][0]
        histories = [{**v, "group": "A" if v["team_a"] == "Alpha" else "B"} for v in training()]
        self.assertIsNone(history_estimate(r, histories, NOW)[0])
        histories = [{**v, "team_b": "Other pool " + v["team_b"]} if v["team_a"] == "Beta" else v for v in training()]
        self.assertIsNone(history_estimate(r, histories, NOW)[0])

    def test_duplicate_observations_cannot_be_a_second_game(self):
        r = build([raw_fixture(competition="PRM 2nd Division 26-27 Fall")])["matches"][0]
        histories = [training()[0], {**training()[0], "id": "wiki-copy"}, training()[2], {**training()[2], "id": "wiki-copy-2"}]
        self.assertIsNone(history_estimate(r, histories, NOW)[0])

    def test_browser_expiry_cannot_outlive_provider_update_or_external_start(self):
        from verified_pipeline.render import valid_until
        r = build(candidates=[{**external(), "provider_updated_at": "2026-10-21T18:00:00Z"}])["matches"][0]
        self.assertEqual(valid_until(r), "2026-10-22T02:00:00Z")
        r["evidence"][0]["start_utc"] = "2026-10-21T23:00:00Z"
        self.assertEqual(valid_until(r), "2026-10-21T23:00:00Z")

    def test_worlds_group_stage_scope_and_explicit_old_provider_update(self):
        from verified_pipeline.core import polymarket_candidates
        m = {"id": "synthetic-1", "question": "LoL: Alpha vs Beta (BO1) - Worlds Group Stage", "sportsMarketType": "moneyline",
             "groupItemTitle": "Match Winner", "active": True, "closed": False, "acceptingOrders": True,
             "outcomes": ["Alpha", "Beta"], "outcomePrices": [.6, .4], "gameStartTime": START, "updatedAt": OBSERVED}
        candidates = polymarket_candidates([m], observed_at=OBSERVED, source_url="https://gamma-api.polymarket.com/events?tag_id=65")
        f = raw_fixture(competition="Worlds 2026 Main Event")
        self.assertEqual(build([f], candidates=candidates)["matches"][0]["method"], "prediction_market")
        candidates[0]["provider_updated_at"] = "2026-10-20T00:00:00Z"
        self.assertIsNone(build([f], candidates=candidates)["matches"][0]["pick"])


if __name__ == "__main__":
    unittest.main()
