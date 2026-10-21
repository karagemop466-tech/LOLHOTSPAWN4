#!/usr/bin/env python3
"""Non-mutating adversarial probes of the first published collector.

All fixtures/markets in these probes are explicitly SYNTHETIC. They are not
published match data. This reports risks, not a claim that a real row is wrong.
Run again after fixes; a replaced collector may require an adapter update.
"""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "collector/build.py").exists():
    raise SystemExit("Legacy collector not present; update probe adapter before reuse")
sys.path.insert(0, str(ROOT / "collector"))
import common
spec = importlib.util.spec_from_file_location("published_build", ROOT / "collector/build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

fixture = {
    "team_a": {"name": "Audit Alpha"},
    "team_b": {"name": "Audit Beta"},
    "start_utc": "2026-10-23T17:00:00Z",
}
base_market = {
    "closed": False,
    "outcomes": ["Audit Alpha", "Audit Beta"],
    "prices": [0.6, 0.4],
    "game_start": "2026-10-23T17:00:00Z",
    "event_start": "2026-10-23T17:00:00Z",
    "event_title": "SYNTHETIC Audit League",
    "question": "SYNTHETIC Audit Alpha vs Audit Beta (BO3) - Match Winner",
    "volume": 100,
}
results = []


def record(name, correct, detail):
    results.append({"probe": name, "passed": bool(correct), "detail": detail})


map_market = dict(base_market, question="SYNTHETIC Audit Alpha vs Audit Beta - Map 1 Winner")
selected, _ = build.find_polymarket_match_line(fixture, [map_market])
record("Reject map-winner as full-series moneyline", selected is None,
       "Accepted a synthetic Map 1 Winner market" if selected else "Rejected map market")

undated = dict(base_market, game_start=None, event_start=None)
selected, _ = build.find_polymarket_match_line(fixture, [undated])
record("Reject unconfirmed event time", selected is None,
       "Accepted synthetic market with no event/start timestamp" if selected else "Rejected unknown date")

rematch = dict(base_market, game_start="2026-10-25T17:00:00Z", event_start="2026-10-25T17:00:00Z")
selected, _ = build.find_polymarket_match_line(fixture, [rematch])
record("Do not silently attach a later rematch", selected is None,
       "Accepted same synthetic pair two days after fixture without reschedule evidence" if selected else "Rejected later rematch")

record("Do not conflate main and academy rosters",
       not common.teams_match("Audit Alpha", "Audit Alpha Academy"),
       "Synthetic main/academy identity comparison")
record("Allow harmless esports suffix normalization",
       common.teams_match("Audit Alpha Esports", "Audit Alpha"),
       "Synthetic esports-suffix identity comparison")

with tempfile.TemporaryDirectory() as tmp:
    raw = Path(tmp)
    old = {"file": "data/raw/synthetic.json", "url": "https://example.invalid/audit-only",
           "fetched_at": "2026-10-20T12:00:00Z", "http_status": 200,
           "stale": False, "sha256": "synthetic-test-hash"}
    (raw / "synthetic.json").write_text('{"synthetic": true}')
    (raw / "manifest.json").write_text(json.dumps({"synthetic.json": old}))
    with patch.object(common, "RAW_DIR", str(raw)), patch.object(common, "now_iso", return_value="2026-10-21T20:00:00Z"), redirect_stdout(io.StringIO()):
        meta = common.save_snapshot("synthetic.json", "https://example.invalid/audit-only", None, 503)
    record("Retain original evidence time when reusing cache", meta.get("fetched_at") == old["fetched_at"],
           {"old_evidence_at": old["fetched_at"], "returned_fetched_at": meta.get("fetched_at"), "stale": meta.get("stale")})
    with patch.object(common, "RAW_DIR", str(raw)), redirect_stdout(io.StringIO()):
        meta = common.save_snapshot("missing-synthetic.json", "https://example.invalid/audit-only", None, 503)
    record("No previous cache is not a successful fresh source", meta.get("stale") is True or meta.get("available") is False or meta.get("status") in {"failed", "unavailable"},
           {"returned_stale": meta.get("stale"), "note": meta.get("note")})

report = {
    "audit": "Synthetic adversarial safety probes of first published collector",
    "checked_at": datetime.now(timezone.utc).isoformat(),
    "synthetic_inputs_only": True,
    "source_facts_verified": False,
    "results": results,
    "passed": all(p["passed"] for p in results),
}
text = json.dumps(report, indent=2) + "\n"
print(text)
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(text)
raise SystemExit(0 if report["passed"] else 1)
