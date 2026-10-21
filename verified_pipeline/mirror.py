"""Explicit final-integration fallback for an unchangeable legacy Pages selector.

NOT a production refresh pipeline. Production deploys only verified/ with no
main pushes. This copies a validated, dated snapshot for implicit legacy root
builds so they cannot resurrect the rejected UI. Original observation dates and
browser expiry survive. Archive original shared HTML before the initial copy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from .check import check_site
from .public_check import FILES

ROOT = Path(__file__).resolve().parent.parent


def mirror(root=ROOT, *, archive_legacy=False):
    root = Path(root)
    source = root / "verified"
    report = check_site(source)
    if not report["passed"]:
        raise ValueError("Refusing to mirror an invalid verified snapshot: " + repr(report["errors"]))
    if archive_legacy:
        archive = root / "legacy_ui"
        if archive.exists():
            raise ValueError("Original legacy UI archive already exists; never overwrite provenance")
        original = sorted(root.glob("*.html"))
        archive.mkdir()
        hashes = {}
        for path in original:
            target = archive / path.name
            shutil.copyfile(path, target)
            hashes[path.name] = hashlib.sha256(target.read_bytes()).hexdigest()
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        (archive / "manifest.json").write_text(json.dumps({"source_commit": commit, "sha256": hashes,
            "note": "Byte-for-byte completed pre-corrective root HTML; archived before the safe fallback copy. Original functional collector/resolver/assets/data remain in place."}, indent=2) + "\n")
        (archive / "README.md").write_text("# Preserved historical UI source\n\nThese HTML files are byte-for-byte originals from the commit recorded in\n`manifest.json`. They preserve completed parallel-session work for provenance,\nnot current verified probabilities. Their collector/resolver/assets/data remain\nin the repository. This archive is **not** uploaded in the production Pages\nartifact. Root HTML now holds a dated validated fallback because the effective\nPages selector still reports legacy/main/root. Actual production publishes\nonly `verified/` after its independent gates.\n")
        # Obsolete unlinked routes are archived, not allowed to resurrect a
        # second probability implementation during implicit legacy builds.
        valid_pages = {p.name for p in source.glob("*.html")}
        for path in original:
            if path.name not in valid_pages:
                path.unlink()
    for filename in FILES:
        target = root / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / filename, target)
    metadata = root / "data/deployment.json"
    data = json.loads(metadata.read_text())
    data["artifact"] = "verified-legacy-fallback"
    data["publication_note"] = "Dated validated root safety mirror, not this run's live Pages artifact. Actual production acceptance requires artifact=verified-only and the expected generating run/commit."
    metadata.write_text(json.dumps(data, indent=2) + "\n")
    copied = check_site(root)
    if not copied["passed"]:
        raise ValueError("Root fallback integrity failed: " + repr(copied["errors"]))
    return copied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-legacy", action="store_true", help="One-time original HTML archive; refuses overwrite")
    args = parser.parse_args()
    print(json.dumps(mirror(archive_legacy=args.archive_legacy), indent=2))


if __name__ == "__main__":
    main()
