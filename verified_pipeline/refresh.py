"""python -m verified_pipeline.refresh [--offline] [--bootstrap-receipts DIR]

One independent publisher. Does not read or modify collector/, scripts/,
legacy data/, root HTML, docs/, seeded ratings, or Hotspawn crowd/history.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from .core import HOTSPAWN_FEED, build_dataset, dt, iso, pinnacle_candidates, polymarket_candidates, sanitize_inventory
from .sources import (PINNACLE, SourceClient, alternative_source_checks, atomic_json,
                      canonical_links, discover_gamma, discover_pinnacle, organizer_history)
from .render import render_site
from .wiki import collect as collect_wiki

ROOT = Path(__file__).resolve().parent.parent


def review_findings(root):
    path = root / "research/d126dc4d/review-findings.json"
    findings = json.loads(path.read_text())["findings"] if path.exists() else []
    for f in findings:
        f["context"] = "Independent Oct21 research observation / historical implementation audit. Not an assertion that this build uses the rejected data."
        # No guessed match slugs. Exact canonical identity links come only from
        # the WP resolver; the official inventory is always linked separately.
        f["sources"] = [s for s in f.get("sources", []) if not ("hotspawn.com/matches/" in s and "1081205" not in s)]
    findings.extend([
        {"id": "partial-model", "title": "History estimates are uncalibrated and based on a partial audited archive",
         "status": "needs review", "description": "Organizer and recognized native community-wiki match results are dated observations, not a complete season database or proof of model accuracy. Both teams need at least two dated same-format eligible series from a comparable observed opponent pool. Team-name aliases, academy squads, season changes and absent history are never guessed. A supported tie does not select team A.",
         "sources": ["https://www.primeleague.gg/en/liga2", "https://www.primeleague.gg/en/liga3"]},
        {"id": "native-history-only", "title": "Native result observations, not synthetic game-cache rows",
         "status": "needs review", "description": "A series score or a standing is not an individual-game archive. The independent collector reads dated MatchSchedule templates directly, checks winner/score/format, and never imports the retained legacy seeded ratings, synthetic minute offsets or league-average opponents. Community-wiki records are not organizer endorsements; aliases and administrative outcomes still require separate review.",
         "sources": ["https://lol.fandom.com/wiki/Data:Prime_League_3rd_Division/2027_Season/Fall_Split?action=raw", "https://lol.fandom.com/wiki/Data:RIVALS_LEAGUE/2026_Season/Season_2?action=raw", "https://www.komplettligaen.no/lol/resultater?season=13909&division=18859"]},
        {"id": "limited-access", "title": "Coverage limitations persist when original sources restrict automated access",
         "status": "needs review", "description": "All source attempts have receipts below. Prime League runner requests previously returned 403; RIVALS and Komplett returned page shells, not usable results. The public feeds do not cover every amateur match. Access restrictions are not proof that a sportsbook has no market. No access controls are bypassed.",
         "sources": ["https://www.primeleague.gg/en/liga3", "https://www.komplettligaen.no/lol/resultater?season=13909&division=18859", "https://www.rivalsleague.gg/lol/teams"]}
    ])
    return findings


def refresh(*, root=ROOT, offline=False, bootstrap=None, now=None):
    now = now or datetime.now(timezone.utc)
    output = root / "verified"
    client = SourceClient(output / "data/source-cache.json", offline=offline)
    if bootstrap:
        client.bootstrap(bootstrap)
    inventory = client.request("hotspawn", HOTSPAWN_FEED, transform=sanitize_inventory)
    if not inventory:
        # Leave every last-good published file unchanged; do not silently ship an
        # empty board while calling it 100% coverage.
        client.save()
        raise RuntimeError("No valid original inventory or dated cache. Publication refused.")
    inventory = sanitize_inventory(inventory)
    links = canonical_links(client, [str(m["id"]) for m in inventory])
    league_ids = discover_pinnacle(client)
    candidates = []
    for id_ in league_ids:
        meta_key, price_key = "pinnacle-meta-" + id_, "pinnacle-prices-" + id_
        meta, prices = client.cache.get(meta_key, {}), client.cache.get(price_key, {})
        dates = [dt(meta.get("observed_at")), dt(prices.get("observed_at"))]
        oldest = iso(min(dates)) if all(dates) else None
        candidates.extend(pinnacle_candidates(meta.get("payload"), prices.get("payload"), observed_at=oldest,
                          source_url=PINNACLE + "/leagues/" + id_ + "/markets/straight",
                          metadata_url=PINNACLE + "/leagues/" + id_ + "/matchups"))
    markets, single, truncated = discover_gamma(client)
    for market in markets:
        candidates.extend(polymarket_candidates([market], observed_at=market.get("_receipt_observed_at"), source_url=market.get("_receipt_source_url")))
    if single:
        existing_ids = {c["id"] for c in candidates if c["provider"] == "Polymarket"}
        if str(single.get("id")) not in existing_ids:
            candidates.extend(polymarket_candidates([single], observed_at=client.observed("gamma-series-audit"), source_url=client.cache["gamma-series-audit"]["source_url"]))
    audited = json.loads((root / "verified_pipeline/history.json").read_text())["records"]
    previous_path = output / "data/history.json"
    previous = json.loads(previous_path.read_text()).get("records", []) if previous_path.exists() else []
    # Preserve independently source-linked automatic results between successful
    # deployments, but curated observations win any duplicate ID conflict.
    history_by_id = {r["id"]: r for r in previous + audited}
    results = organizer_history(client, list(history_by_id.values()))
    results, scheduled = collect_wiki(client, results)
    alternative_source_checks(client)
    findings = review_findings(root)
    if truncated:
        findings.append({"id": "gamma-pagination", "title": "Prediction-market discovery hit its documented pagination safety cap",
                         "status": "needs review", "description": "More events may exist. This refresh does not claim exhaustive external market discovery.",
                         "sources": ["https://gamma-api.polymarket.com/events?tag_id=65&active=true&closed=false&limit=100&offset=0"]})
    data = build_dataset(inventory, inventory_at=client.observed("hotspawn"), now=now, candidates=candidates,
                         history=results, scheduled=scheduled, permalinks=links, sources=client.receipts(), findings=findings)
    data["build"] = {"commit": os.environ.get("GITHUB_SHA"), "run_id": os.environ.get("GITHUB_RUN_ID"),
                     "repository": "karagemop466-tech/LOLHOTSPAWN4", "mode": "dated receipts / offline" if offline else "original publisher refresh"}
    data["discovery"] = {"inventory_rows": len(inventory), "canonical_links_resolved": len(links),
                         "pinnacle_leagues_queried": league_ids, "full_series_candidates": len(candidates),
                         "organizer_result_observations": sum("primeleague.gg" in r["source_url"] for r in results),
                         "trusted_result_observations": len(results), "native_wiki_schedule_rows": len(scheduled), "external_discovery_exhaustive": False,
                         "gamma_pagination_capped": truncated}
    history_data = {"schema_version": 1, "description": "Partial, dated original-organizer and native community-wiki observations; no synthetic games, seed ratings or complete-season claim.",
                    "records": results}
    # Write only after inventory/schema/calculation validation has succeeded.
    client.save()
    atomic_json(output / "data/matches.json", data)
    atomic_json(output / "data/history.json", history_data)
    render_site(data, history_data, output)
    atomic_json(output / "data/integrity.json", {"schema_version": 1, "checked_at": iso(now), "passed": True,
                "checks": ["nonempty unique LoL inventory IDs", "no dropped inventory fixtures", "null unsupported values",
                           "exact identities; no fuzzy aliases", "full-series scope", "known nearby external starts",
                           "fresh receipt dates", "paired probabilities and honest tie picks", "dated causal model inputs"],
                "summary": data["summary"], "source_receipts": len(data["sources"]),
                "limitations": "Calculation/inventory integrity is not a claim of calibrated probabilities or exhaustive bookmaker access."})
    print(json.dumps({"summary": data["summary"], "discovery": data["discovery"]}, indent=2))
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use dated receipts without refreshing their observation timestamps")
    parser.add_argument("--bootstrap-receipts", type=Path)
    args = parser.parse_args()
    refresh(offline=args.offline, bootstrap=args.bootstrap_receipts)


if __name__ == "__main__":
    main()
