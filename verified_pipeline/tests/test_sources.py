from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from verified_pipeline.sources import SourceClient, gamma_events, parse_prime_result


class ReceiptSafety(unittest.TestCase):
    def test_failed_request_preserves_original_observation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipts.json"
            url = "https://example.com/source"
            old = {"source_url": url, "observed_at": "2026-10-20T12:00:00Z", "payload": [1], "http_status": 200}
            path.write_text(json.dumps({"test": old}))
            client = SourceClient(path)
            with patch("verified_pipeline.sources.urlopen", side_effect=HTTPError(url, 403, "Forbidden", {}, None)):
                self.assertEqual(client.request("test", url), [1])
            record = client.cache["test"]
            self.assertEqual(record["observed_at"], old["observed_at"])
            self.assertTrue(record["cache_used"])
            self.assertEqual(record["http_status"], 403)
            self.assertIn("no access workaround", record["error"])

    def test_offline_build_is_not_a_new_http_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipts.json"
            url = "https://example.com/source"
            old = {"source_url": url, "observed_at": "2026-10-20T12:00:00Z", "attempted_at": "2026-10-20T11:59:59Z", "payload": [1]}
            path.write_text(json.dumps({"test": old}))
            client = SourceClient(path, offline=True)
            with patch("verified_pipeline.sources.urlopen", side_effect=AssertionError("offline must not fetch")):
                self.assertEqual(client.request("test", url), [1])
            self.assertEqual(client.cache["test"]["observed_at"], old["observed_at"])
            self.assertEqual(client.cache["test"]["attempted_at"], old["attempted_at"])

    def test_different_url_cannot_inherit_an_old_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "receipts.json"
            path.write_text(json.dumps({"test": {"source_url": "https://example.com/old", "payload": [1]}}))
            client = SourceClient(path, offline=True)
            self.assertIsNone(client.request("test", "https://example.com/new"))

    def test_shell_is_not_parsed_as_a_result(self):
        self.assertIsNone(parse_prime_result('<html><title>Prime League</title><div id="root"></div></html>',
            "https://www.primeleague.gg/en/matches/1-synthetic", "PRM2"))

    def test_parser_excludes_predictions_and_does_not_invent_a_season(self):
        html = '''<html><head><title>Alpha vs Beta | Matches | Prime League</title></head><body>
        <p>2026-10-16 12:00</p><p>Show Results</p><b>2:1</b><span>best of three</span>
        <h2>Predictions</h2><p>90% / 10%</p><h2>Game 1 Details</h2><p>0:1</p></body></html>'''
        r = parse_prime_result(html, "https://www.primeleague.gg/en/matches/1-synthetic", "PRM2")
        self.assertEqual((r["score_a"], r["score_b"]), (2, 1))
        self.assertEqual((r["team_a"], r["team_b"]), ("Alpha", "Beta"))
        self.assertIsNone(r["season"])
        self.assertIsNone(r["source_timezone"])
        self.assertNotIn("90%", json.dumps(r))

    def test_map_score_only_and_forfeit_not_accepted(self):
        for prefix in ("", "<p>default win</p><p>2:0 best of three</p>"):
            html = f'<title>Alpha vs Beta | Matches | Prime League</title><p>2026-10-16 12:00</p>{prefix}<h2>Predictions</h2><p>2:0 best of three</p>'
            self.assertIsNone(parse_prime_result(html, "https://www.primeleague.gg/en/matches/1-synthetic", "PRM2"))

    def test_gamma_cache_drops_unneeded_fields_not_event_count(self):
        values = [{"id": "1", "markets": [{"id": "2", "question": "test", "unneeded_image": "image"}]}]
        parsed = gamma_events(values)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["markets"][0]["id"], "2")
        self.assertNotIn("unneeded_image", parsed[0]["markets"][0])


if __name__ == "__main__":
    unittest.main()
