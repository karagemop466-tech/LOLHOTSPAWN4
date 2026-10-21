import unittest
from pathlib import Path

from verified_pipeline.check import check_site


class PublishedArtifact(unittest.TestCase):
    def test_inventory_every_calculation_every_row_source_and_all_internal_links(self):
        site = Path(__file__).resolve().parents[2] / "verified"
        report = check_site(site)
        self.assertTrue(report["passed"], report["errors"])
        self.assertGreater(report["unique_inventory_ids"], 0)
        self.assertGreaterEqual(report["html_pages"], 7)


if __name__ == "__main__":
    unittest.main()
