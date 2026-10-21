"""Non-network acceptance gate for the verified-only Pages artifact."""
from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from .core import (american_implied, dt, fit, history_estimate, iso, norm,
                   sanitize_inventory, validate_dataset, valid_https)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.duplicates, self.links, self.rows, self.active = set(), [], [], [], []
        self.h1 = 0
        self.generated_at = None
        self.inventory_at = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "body":
            self.generated_at = a.get("data-generated-at")
            self.inventory_at = a.get("data-inventory-at")
        if a.get("id"):
            if a["id"] in self.ids:
                self.duplicates.append(a["id"])
            self.ids.add(a["id"])
        self.h1 += tag == "h1"
        if a.get("data-match-id"):
            row = {"tag": tag, "id": a["data-match-id"], "external_sources": []}
            self.rows.append(row)
            self.active.append(row)
        for attr in ("href", "src"):
            if a.get(attr):
                self.links.append(a[attr])
                if tag == "a" and valid_https(a[attr]):
                    for row in self.active:
                        row["external_sources"].append(a[attr])

    def handle_endtag(self, tag):
        if self.active and self.active[-1]["tag"] == tag:
            self.active.pop()


def check_site(site):
    site = Path(site).resolve()
    errors, checks = [], []
    data = json.loads((site / "data/matches.json").read_text())
    history = json.loads((site / "data/history.json").read_text())["records"]
    cache = json.loads((site / "data/source-cache.json").read_text())
    validate_dataset(data)
    now = dt(data["generated_at"])
    raw = sanitize_inventory(cache["hotspawn"]["payload"])
    inventory = {str(r["id"]): r for r in raw}
    published = {r["id"]: r for r in data["matches"]}
    if set(inventory) != set(published):
        errors.append("Published inventory IDs differ from the original receipt")
    checks.append("All original inventory IDs accounted for, including stale-listed rows")
    for r in data["matches"]:
        original = inventory.get(r["id"], {})
        if (r["team_a"], r["team_b"], r["competition"], r["start_utc"], r["lock_utc"]) != (
                str(original.get("participants0_name") or ""), str(original.get("participants1_name") or ""),
                str(original.get("competition_name") or ""), iso(dt(original.get("scheduled_start_time"))), iso(dt(original.get("lock_time")))):
            errors.append("Inventory facts changed for " + r["id"])
        if r["method"] == "model":
            model, reason = history_estimate(r, history, now)
            if not model or model["probability_a"] != r["probability_a"] or model["training_ids"] != r["model"]["training_ids"]:
                errors.append("Model not reproducible from dated observations for " + r["id"])
        if r["method"] in {"bookmaker", "prediction_market"}:
            for ev in r["evidence"]:
                matches, reverse = fit(r, ev, now)
                if not matches or reverse != ev["reversed_to_inventory"]:
                    errors.append("Identity/scope/time/freshness guard fails for " + r["id"])
                prices = ev["raw_prices"]
                if ev["provider"] == "Pinnacle":
                    a, b = american_implied(prices["home"]), american_implied(prices["away"])
                else:
                    a, b = float(prices[0]), float(prices[1])
                expected = b/(a+b) if reverse else a/(a+b)
                if abs(expected - ev["probability_a"]) > .000001:
                    errors.append("Price-to-probability arithmetic mismatch for " + r["id"])
            if abs(r["probability_a"] - r["evidence"][0]["probability_a"]) > .000001:
                errors.append("Published primary line differs from source evidence for " + r["id"])
        if r["method"] == "unresolved" and (r["probability_a"] is not None or r["probability_b"] is not None or r["pick"] is not None):
            errors.append("Unsupported fill present for " + r["id"])
    checks += ["Inventory names/competition/times equal source receipt", "Every model reproduces from dated, eligible organizer / trusted wiki results",
               "Every accepted market passes identity/scope/time/freshness guards", "All quoted arithmetic and team reversals reproduce",
               "Unsupported probabilities and picks stay null; ties have no forced pick"]
    summary = data["summary"]
    if summary["listed"] != summary["upcoming"] + summary["elapsed"] + summary["locked_or_unknown"]:
        errors.append("Inventory state accounting does not reconcile")
    if summary["picks"] != sum(r["pick"] is not None for r in data["matches"]):
        errors.append("Directional pick count mismatch")
    for key in ("bookmaker", "prediction_market", "model"):
        if summary[key] != sum(r["method"] == key and r["state"] == "upcoming" for r in data["matches"]):
            errors.append("Method count mismatch: " + key)
    if summary["unresolved"] != sum(r["state"] == "upcoming" and r["pick"] is None for r in data["matches"]):
        errors.append("Unresolved count mismatch")
    checks.append("Executive-summary counts reconcile to the current fixture rows")
    pages = {}
    for path in site.glob("*.html"):
        parser = Page()
        parser.feed(path.read_text())
        pages[path.name] = parser
        if parser.generated_at != data["generated_at"] or parser.inventory_at != data["inventory_observed_at"]:
            errors.append(path.name + ": HTML/JSON snapshot timestamps differ")
        if parser.h1 != 1:
            errors.append(path.name + ": expected one primary heading")
        if parser.duplicates:
            errors.append(path.name + ": duplicate DOM IDs: " + ", ".join(parser.duplicates))
        for row in parser.rows:
            if not row["external_sources"]:
                errors.append(path.name + ": missing original source on row " + row["id"])
    for name, page in pages.items():
        for value in page.links:
            u = urlparse(value)
            if u.scheme:
                if u.scheme != "https":
                    errors.append(name + ": non-HTTPS/unsafe link " + value)
                continue
            target = (site / unquote(u.path)).resolve() if u.path else site / name
            if site not in target.parents and target != site:
                errors.append(name + ": asset/link escapes verified artifact " + value)
                continue
            if not target.is_file():
                errors.append(name + ": broken internal link " + value)
                continue
            if u.fragment and target.suffix == ".html":
                if target.name in pages and unquote(u.fragment) not in pages[target.name].ids:
                    errors.append(name + ": broken fragment " + value)
    all_cards = {r["id"] for r in pages["picks.html"].rows if r["tag"] == "article"}
    if all_cards != set(inventory):
        errors.append("Static all-matches page dropped inventory rows")
    checks += ["Every table/card row has original HTTPS sources", "All internal pages/assets/fragments resolve inside verified artifact",
               "Static/no-JavaScript inventory retains every fixture ID", "One primary heading and unique DOM IDs on every page"]
    return {"passed": not errors, "checked_at": data["generated_at"], "artifact": "verified-only",
            "html_pages": len(pages), "unique_inventory_ids": len(inventory), "summary": summary, "checks": checks, "errors": errors,
            "limitations": "Original receipts and calculations are checked; this is not a calibration/accuracy guarantee or live external-link uptime test."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("verified"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = check_site(args.site)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
