#!/usr/bin/env python3
"""Read-only original-publisher source receipts. Not a production pick writer.

Run on a GitHub-hosted runner because the local sandbox restricts publisher
network access. Only this session's research directory is written. Never uses
Hotspawn crowd statistics, never fills probabilities, never bypasses access
controls. Failed sources remain failed in the manifest.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

OUTPUT = Path(__file__).resolve().parent / "receipts"
BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
SOURCES = {
    "hotspawn-fixtures": "https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures?sport_alias=lol&status=scheduled",
    "pinnacle-worlds-matchups": BASE + "/leagues/9587/matchups",
    "pinnacle-worlds-prices": BASE + "/leagues/9587/markets/straight",
    "pinnacle-emea-matchups": BASE + "/leagues/225201/matchups",
    "pinnacle-emea-prices": BASE + "/leagues/225201/markets/straight",
    "polymarket-series-5721049": "https://gamma-api.polymarket.com/markets/5721049",
    "polymarket-map-5721045": "https://gamma-api.polymarket.com/markets/5721045",
    "prime-liga2": "https://www.primeleague.gg/en/liga2",
    "prime-liga3": "https://www.primeleague.gg/en/liga3",
    "prime-result-601780": "https://www.primeleague.gg/en/matches/601780-mt1-vision-vs-babos-gaming-academy",
    "prime-result-601784": "https://www.primeleague.gg/en/matches/601784-glacial-guardians-vs-blackdivision",
    "komplett-standings": "https://www.komplettligaen.no/lol/tabeller",
    "komplett-results": "https://www.komplettligaen.no/lol/resultater?season=13909&division=18859",
    "rivals-teams": "https://www.rivalsleague.gg/lol/teams",
    "rivals-result": "https://www.rivalsleague.gg/lol/match/08083633-9115-4db9-95de-19940a62b738",
}
MAX_BYTES = 6_000_000


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def redact_crowd(value):
    """Retain factual inventory/results, drop all crowd-pick fields recursively."""
    if isinstance(value, list):
        return [redact_crowd(v) for v in value]
    if isinstance(value, dict):
        return {k: redact_crowd(v) for k, v in value.items()
                if "picked" not in k.lower() and "total_picks" not in k.lower()}
    return value


def retrieve(item):
    name, url = item
    record = {"name": name, "source_url": url, "attempted_at": now(),
              "verified_retrieval": False}
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; independent-source-audit/1.0)",
                                    "Accept": "application/json,text/html;q=0.9,*/*;q=0.5"})
        with urlopen(req, timeout=35) as resp:
            body = resp.read(MAX_BYTES + 1)
            record["http_status"] = resp.status
            record["content_type"] = resp.headers.get("Content-Type")
            record["response_date_header"] = resp.headers.get("Date")
            record["final_url"] = resp.geturl()
        if len(body) > MAX_BYTES:
            raise ValueError("Response exceeds documented receipt size limit; not parsed")
        text = body.decode("utf-8", "replace")
        record.update({"retrieved_at": now(), "body_sha256": hashlib.sha256(body).hexdigest(),
                       "body_bytes": len(body)})
        try:
            data = json.loads(text)
            if isinstance(data, dict) and data.get("status") in (401, 403):
                raise PermissionError("Publisher returned an authorization notice")
            record["json"] = redact_crowd(data)
            record["transformation"] = "JSON parsed; crowd-pick fields removed recursively; original response hash retained"
        except json.JSONDecodeError:
            # Keep actual markup for parser development, not fetched page claims.
            record["html"] = text
            record["transformation"] = "Original decoded UTF-8 HTML; not a verified result table"
        record["verified_retrieval"] = record["http_status"] == 200
    except HTTPError as exc:
        record.update({"http_status": exc.code, "error": str(exc)})
    except Exception as exc:
        record["error"] = str(exc)
    return name, record


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {"owner": "arena-d126dc4d", "generated_at": now(),
                "purpose": "Independent original-publisher retrieval receipts; not live probabilities",
                "sources": {}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for name, record in pool.map(retrieve, SOURCES.items()):
            path = OUTPUT / (name + ".json")
            path.write_text(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            manifest["sources"][name] = {k: v for k, v in record.items() if k not in ("json", "html")}
            print(name, record.get("http_status"), record.get("error", "retrieved"), flush=True)
    manifest["successful_retrievals"] = sum(x["verified_retrieval"] for x in manifest["sources"].values())
    manifest["result_values_verified"] = False
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Receipts are retrieval evidence, not a claim that every result or model is verified.")
    return 0 if manifest["successful_retrievals"] else 1


if __name__ == "__main__":
    sys.exit(main())
