import json
from pathlib import Path
import shutil
import tempfile
import unittest

from verified_pipeline.check import check_site
from verified_pipeline.public_check import validate_public

SITE = Path(__file__).resolve().parents[2] / "verified"


class PublishedArtifact(unittest.TestCase):
    def test_inventory_every_calculation_every_row_source_and_all_internal_links(self):
        report = check_site(SITE)
        self.assertTrue(report["passed"], report["errors"])
        self.assertGreater(report["unique_inventory_ids"], 0)
        self.assertGreaterEqual(report["html_pages"], 7)

    def test_public_acceptance_matches_exact_artifact_run_and_commit(self):
        build = json.loads((SITE / "data/deployment.json").read_text())["build"]
        metadata, report = validate_public(SITE, expected_run=build["run_id"], expected_commit=build["commit"])
        self.assertTrue(report["passed"])
        self.assertEqual(metadata["artifact"], "verified-only")

    def test_public_acceptance_rejects_old_run_or_wrong_commit(self):
        build = json.loads((SITE / "data/deployment.json").read_text())["build"]
        for run, commit in (("not-the-deployed-run", build["commit"]), (build["run_id"], "not-the-deployed-commit")):
            with self.assertRaises(ValueError):
                validate_public(SITE, expected_run=run, expected_commit=commit)

    def test_mixed_cdn_html_json_snapshots_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "verified"
            shutil.copytree(SITE, target)
            page = target / "index.html"
            text = page.read_text()
            generated = json.loads((target / "data/matches.json").read_text())["generated_at"]
            page.write_text(text.replace('data-generated-at="' + generated + '"', 'data-generated-at="old-snapshot"'))
            report = check_site(target)
            self.assertFalse(report["passed"])
            self.assertTrue(any("snapshot timestamps differ" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
