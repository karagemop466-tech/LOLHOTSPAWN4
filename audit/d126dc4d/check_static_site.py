#!/usr/bin/env python3
"""Independent local-only GitHub Pages link and document-structure audit.

This checks file/fragment existence and source-link presence, NOT external page
availability or factual accuracy. It never follows arbitrary publisher links.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

DEFAULT_SOURCE_HOSTS = {
    "hotspawn.com", "play.hotspawn.com", "www.hotspawn.com",
    "pinnacle.com", "www.pinnacle.com", "guest.api.arcadia.pinnacle.com",
    "polymarket.com", "gamma-api.polymarket.com", "clob.polymarket.com",
    "thunderpick.io", "gg.bet", "www.bwin.com", "www.bet365.com",
    "news.bet365.com", "lolesports.com", "www.lolesports.com",
    "primeleague.gg", "www.primeleague.gg", "komplettligaen.no",
    "www.komplettligaen.no", "rivalsleague.gg", "www.rivalsleague.gg",
    "developer.riotgames.com",
}


@dataclass
class Document:
    path: Path
    ids: list[str] = field(default_factory=list)
    references: list[tuple[str, str]] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    title: str = ""
    lang: str | None = None
    viewport: str | None = None
    h1_count: int = 0


class Parser(HTMLParser):
    def __init__(self, path: Path):
        super().__init__(convert_charrefs=True)
        self.doc = Document(path)
        self.in_title = False
        self.in_head_row = False
        self.in_thead = False
        self.row: list[str] | None = None
        self.row_has_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.doc.ids.append(a["id"])
        if tag == "a" and a.get("name"):
            self.doc.ids.append(a["name"])
        if tag == "html":
            self.doc.lang = a.get("lang")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.doc.h1_count += 1
        if tag == "meta" and (a.get("name") or "").lower() == "viewport":
            self.doc.viewport = a.get("content")
        if tag == "thead":
            self.in_thead = True
        if tag == "tr":
            self.row = []
            self.in_head_row = self.in_thead
            self.row_has_cell = False
        if tag == "td" and self.row is not None:
            self.row_has_cell = True
        if tag == "a" and self.row is not None and a.get("href"):
            self.row.append(a["href"])
        for key in ("href", "src", "poster"):
            if a.get(key):
                self.doc.references.append((tag + ":" + key, a[key]))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "tr" and self.row is not None:
            if not self.in_head_row and self.row_has_cell:
                self.doc.rows.append(self.row)
            self.row = None
        if tag == "thead":
            self.in_thead = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.doc.title += data


def audit(site_root: Path, base_path: str = "/LOLHOTSPAWN4/", check_rows: bool = False,
          source_hosts: set[str] | None = None) -> dict:
    root = site_root.resolve()
    if not root.is_dir():
        raise ValueError(f"Site directory does not exist: {root}")
    docs: dict[Path, Document] = {}
    errors: list[dict] = []
    warnings: list[dict] = []
    external: set[str] = set()
    accepted_sources = source_hosts or DEFAULT_SOURCE_HOSTS
    for path in sorted(root.rglob("*.html")):
        if any(p in {"node_modules", ".git", ".arena", ".venv"} for p in path.parts):
            continue
        parser = Parser(path)
        parser.feed(path.read_text(encoding="utf-8"))
        docs[path.resolve()] = parser.doc
    if not docs:
        errors.append({"file": ".", "issue": "No HTML documents found"})
    total_rows = 0
    for path, doc in docs.items():
        rel = str(path.relative_to(root))
        def error(issue, **extra):
            errors.append({"file": rel, "issue": issue, **extra})
        if not doc.title.strip():
            error("Missing document title")
        if not doc.lang:
            error("Missing html language")
        if not doc.viewport or "width=device-width" not in doc.viewport.replace(" ", ""):
            error("Missing mobile viewport")
        if doc.h1_count != 1:
            error("Expected exactly one h1", count=doc.h1_count)
        for identifier, count in Counter(doc.ids).items():
            if count > 1:
                error("Duplicate fragment identifier", fragment=identifier)
        total_rows += len(doc.rows)
        if check_rows:
            for number, links in enumerate(doc.rows, 1):
                if not any(urlsplit(link).scheme == "https" and
                           urlsplit(link).hostname in accepted_sources for link in links):
                    error("Data row has no recognized original-publisher source link", row=number)
        for kind, ref in doc.references:
            parsed = urlsplit(ref)
            if parsed.scheme in {"http", "https"} or parsed.netloc:
                external.add(ref)
                if parsed.scheme == "http":
                    warnings.append({"file": rel, "issue": "Non-HTTPS external link", "url": ref})
                continue
            if parsed.scheme in {"mailto", "tel", "data", "blob"}:
                continue
            if parsed.scheme:
                error("Unsupported/unsafe reference scheme", reference=ref)
                continue
            if ref == "#":
                error("Placeholder fragment link", reference=ref)
                continue
            url_path = unquote(parsed.path)
            if not url_path:
                target = path
            elif url_path.startswith("/"):
                if base_path != "/" and not url_path.startswith(base_path):
                    error("Absolute internal URL omits repository base path", reference=ref)
                    continue
                target = root / url_path[len(base_path):]
            else:
                target = path.parent / url_path
            target = target.resolve()
            if not target.is_relative_to(root):
                error("Reference escapes published site directory", reference=ref)
                continue
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                error("Missing local target", reference=ref, kind=kind)
                continue
            if parsed.fragment and target.suffix.lower() in {".html", ".htm"}:
                target_doc = docs.get(target)
                if target_doc and unquote(parsed.fragment) not in target_doc.ids:
                    error("Missing local fragment", reference=ref)
    return {
        "audit": "Independent local static structure and link audit",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "site_root": str(site_root),
        "base_path": base_path,
        "pages_checked": len(docs),
        "data_rows_checked": total_rows if check_rows else None,
        "original_publisher_link_presence_only": check_rows,
        "external_urls_discovered": len(external),
        "external_reachability_checked": False,
        "factual_accuracy_checked": False,
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("site_root", type=Path)
    p.add_argument("--base-path", default="/LOLHOTSPAWN4/")
    p.add_argument("--check-row-sources", action="store_true")
    p.add_argument("--source-host", action="append", default=[])
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    result = audit(args.site_root, args.base_path, args.check_row_sources,
                   DEFAULT_SOURCE_HOSTS | set(args.source_host))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
