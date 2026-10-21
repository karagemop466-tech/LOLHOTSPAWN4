"""Regression tests for the independent auditor (no network or production data)."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("independent_static_audit", Path(__file__).with_name("check_static_site.py"))
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

PAGE = '''<!doctype html><html lang="en"><head><title>Picks</title>
<meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body><h1 id="picks">Picks</h1>{body}</body></html>'''


class StaticAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, body):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(PAGE.format(body=body), encoding="utf-8")

    def test_relative_and_project_absolute_links_with_fragments(self):
        self.write("index.html", '<a href="picks/#picks">Picks</a><a href="/LOLHOTSPAWN4/picks/#picks">All</a>')
        self.write("picks/index.html", '<a href="../index.html#picks">Summary</a>')
        self.assertTrue(module.audit(self.root)["passed"])

    def test_missing_fragment_is_rejected(self):
        self.write("index.html", '<a href="#missing">Bad</a>')
        report = module.audit(self.root)
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"][0]["issue"], "Missing local fragment")

    def test_root_absolute_link_must_include_repository_path(self):
        self.write("index.html", '<a href="/index.html">Bad</a>')
        self.assertFalse(module.audit(self.root)["passed"])

    def test_traversal_is_rejected(self):
        self.write("index.html", '<a href="../private.txt">Bad</a>')
        self.assertFalse(module.audit(self.root)["passed"])

    def test_original_publisher_link_is_required_per_data_row(self):
        self.write("index.html", '<table><thead><tr><th>Match</th></tr></thead><tbody><tr><td><a href="https://www.hotspawn.com/matches/example">Source</a></td></tr></tbody></table>')
        report = module.audit(self.root, check_rows=True)
        self.assertTrue(report["passed"])
        self.assertEqual(report["data_rows_checked"], 1)
        self.assertFalse(report["factual_accuracy_checked"])
        self.assertFalse(report["external_reachability_checked"])

    def test_spoofed_publisher_domain_is_rejected(self):
        self.write("index.html", '<table><tr><td><a href="https://www.hotspawn.com.evil.invalid/matches/1">Fake</a></td></tr></table>')
        self.assertFalse(module.audit(self.root, check_rows=True)["passed"])

    def test_placeholder_and_javascript_links_are_rejected(self):
        self.write("index.html", '<a href="#">Empty</a><a href="javascript:void(0)">Unsafe</a>')
        self.assertEqual(len(module.audit(self.root)["errors"]), 2)

    def test_duplicate_ids_are_rejected(self):
        self.write("index.html", '<p id="picks">Duplicate</p>')
        self.assertFalse(module.audit(self.root)["passed"])

    def test_language_viewport_title_and_h1_are_required(self):
        (self.root / "index.html").write_text('<html><body></body></html>')
        self.assertEqual(len(module.audit(self.root)["errors"]), 4)

    def test_query_does_not_change_local_file_resolution(self):
        self.write("index.html", '<a href="index.html?status=unresolved#picks">Filter</a>')
        self.assertTrue(module.audit(self.root)["passed"])


if __name__ == "__main__":
    unittest.main()
