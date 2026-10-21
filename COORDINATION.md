# Coordination

## Session and branch rules

- Current session: `arena-d126dc4d` (started 2026-10-21 UTC), fixed branch `arena/d126dc4d-lolhotspawn4`.
- Arena requires the assigned branch; do not create or rename session branches.
- Coordination issue: <https://github.com/karagemop466-tech/LOLHOTSPAWN4/issues/1>.
- Read this board and the coordination issue before editing. Do not overlap another active owner's scope. Pull/rebase before every push; resolve conflicts without discarding others' work.
- A `needs review` item is non-blocking and must be published on the site's Flagged for Review page. Claims stale for >60 minutes without commits may be taken over with a logged handoff.

## Task board

| Task | Status | Owner | File scope | Verification / sources / notes |
| --- | --- | --- | --- | --- |
| Collector, normalized evidence, fallback model, dashboard, workflows, tests, documentation | in progress | arena-1a78ec3b | Implementation files, excluding the two reserved paths below | Earlier claim discovered on `arena/1a78ec3b-lolhotspawn4`, commit `9314ecc` at 20:15 UTC. This session yielded its initial overlapping implementation claims before writing implementation code. |
| Independent official-source research and provider access audit | in progress | arena-d126dc4d | `research/d126dc4d/**` | Check original publisher pages and endpoints; record retrieval limitations. Never invent missing matches, prices, or results. Scope exclusion requested in issue #1. |
| Independent row/link/mobile audit and final integration | in progress | arena-d126dc4d | `audit/d126dc4d/**`; `COORDINATION.md` coordination records only | Final merge/deploy ownership requested in issue #1. Do not edit another session's implementation; log requested fixes there. Integrate published commits only after coordination. |

## Verification policy

- Hotspawn is a match-inventory source only, never a probability input.
- Directly observed, source-linked independent two-way bookmaker prices may be de-vigged. Prediction-market shares must be labelled distinctly and not confused with bookmaker prices.
- Publish fallback estimates only from a documented reproducible model using verified independent results; distinguish estimates from observed facts.
- No invented matches, odds, histories, timestamps, coverage counts, or verification claims. Unsupported values remain blank and explicitly unresolved.
- Preserve original source URLs, observed timestamps, retrieval outcomes, and validation results for manual review. Search snippets and other agents' claims are discovery leads, not independent verification.

## Activity log

- 2026-10-21 20:17 UTC: Repository checkout contained only README. Created initial board and committed/pushed claims (`fddd08b`) before implementation. Confirmed GitHub reports admin permission and existing legacy Pages configuration at <https://karagemop466-tech.github.io/LOLHOTSPAWN4/> (main, root); configuration is not yet proof of a working dashboard.
- 2026-10-21 20:18 UTC: Inspected remote refs and found an earlier active implementation claim (`9314ecc`, 20:15 UTC) on the other Arena branch. No implementation files had been written here. Yielded overlapping collector/site/workflow scopes and opened issue #1 requesting the non-overlapping research/audit split and final integration handoff. Original plans are superseded by this board.

## Publication

- Pull request: pending coordinated implementation and verification.
- Merge result: pending.
- Pages deployment: pending verification.
