# COORDINATION.md — Hotspawn LoL Pick'ems Reverse Engineering, Origination & GitHub Pages Hub

## Active Branch & Agent Registry
- **Active Branch**: `arena/a8a4df4b-lolhotspawn4`
- **Pull Request**: [`#19` (`https://github.com/karagemop466-tech/LOLHOTSPAWN4/pull/19`)](https://github.com/karagemop466-tech/LOLHOTSPAWN4/pull/19) — Merged into `main`
- **Live GitHub Pages URL**: `https://karagemop466-tech.github.io/LOLHOTSPAWN4/`
- **Last Sync Timestamp**: `2026-10-21 21:00 UTC`

## Task Board

| Task ID | Category | Scope / Description | Owner | Status | Deliverables |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TASK-1` | Reverse Engineering & Data Collection | Inspect `https://play.hotspawn.com/lobby`, `https://play.hotspawn.com/lol-pickems`, `https://www.hotspawn.com/matches`, and WP REST APIs (`/wp-json/pickem/v1/fixture/<id>`, `/wp-json/hotspawn/v1/tournaments?game=league-of-legends`). Reconcile all 264 filter-bar fixtures across 24 tournaments against the 213 active DOM cards (`27 Closing Soon` + `186 Upcoming`). | `arena/a8a4df4b-lolhotspawn4` | `completed` | `scripts/raw_pickems_195.py`, `data/filter_bar_reconciliation_264.json`, `automation.html` |
| `TASK-2` | Featured Match Odds & Consensus | Gather multi-bookmaker decimal odds (*Vave, Thunderpick, SpinBetter, GG.bet, Rainbet, Underdog, CocoBet, Sportsgambler*) and *Polymarket* orderbook prices for all 9 featured S-Tier matches (`Worlds 2026 Main Event` Swiss R1 & `EM 2026 Summer Main Event` Grand Final). Compute de-vigged probabilities and fair odds with 0% weight on Hotspawn crowd %. | `arena/a8a4df4b-lolhotspawn4` | `completed` | `scripts/build_dataset.py`, `featured.html`, `data/matches_active_213.json` |
| `TASK-3` | Low-Tier Match Origination | Originate win probabilities and picks for all 204 playoff & low-tier regional LoL matches across 11 leagues (`LCP 2027 Promotion`, `LGC Rising 2026 Playoffs`, `Komplettligaen`, `PRM 2nd Div`, `PRM 3rd Div`, `RIVALS LEAGUE`, `4 Nations Halloween Heist`, `Tunisian Super League`, `Arabian League 2nd Div`, `ARC 2026`, `LigaGG CELOL B Playoffs`) using official Leaguepedia `Data:` series/game records, H2H history, and DQ/forfeit rulings. | `arena/a8a4df4b-lolhotspawn4` | `completed` | `scripts/compute_standings.py`, `scripts/build_dataset.py`, `originated.html` |
| `TASK-4` | Unresolved Picks, Limitations & Flagged Audit | Document the 53 locked/stale filter-bar fixtures, unpromoted TBD bracket placeholders (left blank per non-hallucination rule), low-tier origination limitations, and all 27 flagged active cards (`Solid Gaming` DQ forfeit `#1059956`, already-played duplicates `#1079026` & `#1079143`, rescheduled duplicates, team aliases, and slug inversions). | `arena/a8a4df4b-lolhotspawn4` | `completed` | `unresolved.html`, `flagged.html`, `data/flagged_irregularities.json` |
| `TASK-5` | 4–8h Automation, GitHub Pages Site & PR Merge | Build mobile-friendly GitHub Pages dashboard (`index.html`, `featured.html`, `originated.html`, `unresolved.html`, `flagged.html`, `automation.html`), configure 6-hour GitHub Actions cron workflow (`.github/workflows/update-pickems.yml`), open and merge PR `#19` to `main`, and verify GitHub Pages deployment. | `arena/a8a4df4b-lolhotspawn4` | `completed` | `.github/workflows/update-pickems.yml`, `scripts/update_pickems.py`, `index.html`, PR `#19` merged |

## Verification & Audit Summary
1. **264 Filter-Bar Checkboxes vs 213 Active DOM Cards**:
   - `264 (filter-bar sum across 24 tournaments) - 53 (locked/stale past fixtures) + 2 (Oct 23 PRM 2nd Div unremoved duplicates #1079024 & #1079026) = 213 active pickable DOM cards` (`27 Closing Soon` on Oct 22 + `186 Upcoming` Oct 23–Nov 15).
2. **Non-Hallucination & Source Verification**:
   - Every table row across `index.html`, `featured.html`, `originated.html`, `unresolved.html`, and `flagged.html` links directly to its verified Hotspawn fixture URL (`https://www.hotspawn.com/matches/<slug>-<id>`) and official external source (`Polymarket`, `Tips.GG / EGamersWorld`, or `Leaguepedia Data:`).
   - Undetermined `Waiting for information vs Waiting for information` bracket slots are left blank and flagged as `UNVERIFIED_TBD_BRACKET` / `UNVERIFIED_TBD_BYE_SLOT` on `unresolved.html`.
