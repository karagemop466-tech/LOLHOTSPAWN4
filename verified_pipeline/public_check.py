"""Verify actual public Pages bytes, not just a successful deployment status.

Run on the GitHub-hosted runner after deploy. Bounded retries accommodate Pages
CDN propagation; no retry changes the expected run/commit or relaxes validation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import time
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from .check import check_site
from .core import iso
from .render import NAV

FILES = ["data/deployment.json"] + [route for route, _ in NAV] + ["404.html", "assets/site.css", "assets/site.js", "assets/mark.svg"]
FILES += ["data/" + name + ".json" for name in ("matches", "history", "integrity", "source-cache")]
MAX_BYTES = 12_000_000


def validate_public(site, *, expected_run, expected_commit):
    site = Path(site)
    metadata = json.loads((site / "data/deployment.json").read_text())
    data = json.loads((site / "data/matches.json").read_text())
    build = metadata.get("build") or {}
    if (metadata.get("artifact") != "verified-only" or str(build.get("run_id")) != str(expected_run)
            or build.get("commit") != expected_commit or data.get("build") != build
            or data.get("generated_at") != metadata.get("generated_at") or data.get("summary") != metadata.get("summary")):
        raise ValueError("Public artifact/run/commit/snapshot is not this tested production deployment")
    report = check_site(site)
    if not report["passed"]:
        raise ValueError("Public artifact integrity failed: " + "; ".join(report["errors"]))
    return metadata, report


def verify(base, *, expected_run, expected_commit, attempts=12, delay=10):
    if not base.startswith("https://") or not base.endswith("/"):
        raise ValueError("Expected an HTTPS Pages project-root URL ending in /")
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            with tempfile.TemporaryDirectory(prefix="verified-public-") as directory:
                site, hashes = Path(directory), {}
                query = urlencode({"verified_run": expected_run, "acceptance_attempt": attempt})
                for filename in FILES:
                    url = urljoin(base, filename) + "?" + query
                    request = Request(url, headers={"User-Agent": "LOLHOTSPAWN4 public acceptance/1.0", "Cache-Control": "no-cache"})
                    with urlopen(request, timeout=20) as response:
                        body = response.read(MAX_BYTES + 1)
                        if response.status != 200 or len(body) > MAX_BYTES:
                            raise ValueError("Invalid/oversized public response: " + filename)
                    target = site / filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(body)
                    hashes[filename] = hashlib.sha256(body).hexdigest()
                    # Fail fast on a previous deployment instead of repeatedly
                    # downloading its remaining files during CDN propagation.
                    if filename == "data/deployment.json":
                        meta = json.loads(body)
                        if str((meta.get("build") or {}).get("run_id")) != str(expected_run):
                            raise ValueError("Pages CDN still serves a previous deployment")
                metadata, static = validate_public(site, expected_run=expected_run, expected_commit=expected_commit)
                return {"passed": True, "checked_at": iso(datetime.now(timezone.utc)), "public_url": base,
                        "expected_run": str(expected_run), "expected_commit": expected_commit, "attempt": attempt,
                        "artifact": metadata["artifact"], "summary": metadata["summary"], "static_acceptance": static,
                        "public_file_sha256": hashes,
                        "limitations": "Confirms public bytes, inventory, source provenance and calculations; not source uptime, model calibration or outcome accuracy."}
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            print(f"Public acceptance {attempt}/{attempts}: {last_error}", flush=True)
            if attempt < attempts:
                time.sleep(delay)
    return {"passed": False, "checked_at": iso(datetime.now(timezone.utc)), "public_url": base,
            "expected_run": str(expected_run), "expected_commit": expected_commit, "error": last_error}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.url, expected_run=args.run, expected_commit=args.commit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
