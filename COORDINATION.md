# Coordination

## Session and branch rules

- Integration/implementation owner: `arena-d126dc4d` (started 2026-10-21 UTC).
- Session branch: `arena/d126dc4d-lolhotspawn4`. Arena requires this fixed branch; no alternate session branch will be created.
- The repository initially contains only a README. No pre-existing claims or implementation were present.
- Check this board before editing. Do not overlap an active owner's file scope. A `needs review` item is non-blocking and must appear on the site's Flagged for Review page.
- A stale claim (>60 minutes without commits) may be taken over with a logged handoff. Pull/rebase before every push; resolve conflicts without discarding others' work.

## Task board

| Task | Status | Owner | File scope | Verification / sources / notes |
| --- | --- | --- | --- | --- |
| Discover Hotspawn's public match feed and independent LoL evidence sources | in progress | arena-d126dc4d | `research/**`, `scripts/discover*` | Check official publisher endpoints and record retrieval limitations. Do not invent unavailable matches, prices, or results. |
| Implement normalized match coverage, evidence-based probabilities, fallback hierarchy, and tests | in progress | arena-d126dc4d | `scripts/**` except `discover*`, `tests/**`, `requirements.txt`, `pyproject.toml` | Every published value must retain source provenance. Unsupported probabilities remain blank and explicitly unresolved. |
| Build accessible mobile dashboard and category pages | in progress | arena-d126dc4d | `site/**` | Executive summary links to all picks, featured/market-backed picks, fallback picks, unresolved picks, sources, and review flags. |
| Schedule refreshes, integrate, verify, and publish GitHub Pages | in progress | arena-d126dc4d (final integration session) | `.github/**`, `README.md`, `.gitignore`, `COORDINATION.md`, root configuration | Refresh every 6 hours, validate rows and links, create and merge PR from the fixed session branch, verify deployment. |

## Verification policy

- Hotspawn is a match-inventory source only, never a probability input.
- Prefer directly observed, source-linked independent bookmaker/prediction-market prices. Remove overround when converting two-way prices into probabilities.
- Publish lower-tier fallback estimates only from a documented reproducible model using verified independent match results; distinguish estimates from market odds.
- No invented matches, odds, histories, timestamps, coverage counts, or verification claims. When access or evidence is unavailable, leave unsupported values blank and publish the limitation.
- Preserve original source URLs, observed timestamps, retrieval outcomes, and validation results for manual review.

## Activity log

- 2026-10-21: Read the empty repository and confirmed no existing coordination board. Claimed the scopes above before implementation. GitHub reports administrator permission and an existing legacy Pages configuration at `https://karagemop466-tech.github.io/LOLHOTSPAWN4/` (main, root). This is configuration evidence, not yet confirmation of a working dashboard.

## Publication

- Pull request: pending.
- Merge result: pending.
- Pages deployment: pending verification.
