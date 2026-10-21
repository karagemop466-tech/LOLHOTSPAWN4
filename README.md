# LOLHOTSPAWN4 — Hotspawn League of Legends Pick'ems Origination & Probability Hub

Live Mobile-Friendly GitHub Pages Site: **`https://karagemop466-tech.github.io/LOLHOTSPAWN4/`**

## Executive Summary

This repository reverse-engineers [`https://play.hotspawn.com/lol-pickems`](https://play.hotspawn.com/lol-pickems) and Hotspawn's WordPress REST APIs (`/wp-json/pickem/v1/fixture/<id>` and `/wp-json/hotspawn/v1/tournaments?game=league-of-legends`) to generate verified, non-crowd-biased win probabilities and obvious picks for **every active League of Legends match on Hotspawn Pick'ems**, automatically refreshing every **6 hours** (within the 4–8 hour schedule window) via GitHub Actions (`.github/workflows/update-pickems.yml`).

### Key Metrics & Reconciliation
- **213 Active Pickable LoL Matches** rendered in the DOM of `play.hotspawn.com/lol-pickems`:
  - **27 `Closing Soon` Matches** (October 22, 2026)
  - **186 `Upcoming` Matches** (October 23 – November 15, 2026)
- **264 Filter-Bar Fixtures Reconciled Across 24 Tournaments**:
  - `264 (Filter-Bar Sum) - 53 (Locked/Stale Completed Fixtures) + 2 (Oct 23 Unremoved PRM 2nd Div Ghost Duplicates #1079024 & #1079026) = 213 Active DOM Cards`.
- **0% Reliance on Hotspawn Community Pick Percentages**:
  - **9 Featured S-Tier Matches (`Worlds 2026 Main Event` Swiss R1 & `EM 2026 Summer Main Event` Grand Final):** Priced via de-vigged multi-bookmaker decimal odds (*Vave, Thunderpick, SpinBetter, GG.bet, Rainbet, Underdog, CocoBet, Sportsgambler*) and live *Polymarket* orderbooks.
  - **204 Originated Playoff & Low-Tier Regional Matches Across 11 Leagues:** Originated via a Laplace-smoothed Bayesian Bradley-Terry / Log5 model built from verified [Leaguepedia (`lol.fandom.com`)](https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki) `Data:` series records, game records, head-to-head results, and official forfeit/disqualification rulings.

## Site Structure & Subpages

| Page | Path | Description |
| :--- | :--- | :--- |
| **Executive Summary & All Picks** | [`index.html`](https://karagemop466-tech.github.io/LOLHOTSPAWN4/index.html) | Executive Summary, Top Contrarian Locks, Unresolved Summary, Tournament Breakdown, and Interactive 213-Match Master Table |
| **S & A Tier Featured Picks** | [`featured.html`](https://karagemop466-tech.github.io/LOLHOTSPAWN4/featured.html) | Worlds 2026 Swiss R1 (8), EMEA Masters Final (1), LCP 2027 Promotion (1), and LGC Rising Final (1) |
| **Originated Regional Picks** | [`originated.html`](https://karagemop466-tech.github.io/LOLHOTSPAWN4/originated.html) | 202 originated regional matches across Komplettligaen, PRM 2nd/3rd Div, RIVALS, 4 Nations, Tunisian Super League, Arabian League 2nd Div, ARC, and CELOL B |
| **Unresolved & Limitations** | [`unresolved.html`](https://karagemop466-tech.github.io/LOLHOTSPAWN4/unresolved.html) | Unresolved TBD bracket placeholders (left blank per non-hallucination policy), 264-vs-213 reconciliation, and low-tier origination limitations |
| **Flagged for Review** | [`flagged.html`](https://karagemop466-tech.github.io/LOLHOTSPAWN4/flagged.html) | 27 flagged active cards (`Solid Gaming` DQ forfeit lock `#1059956`, already-played duplicates `#1079026` & `#1079143`, rescheduled duplicates, team aliases, and slug inversions) |
| **API & 4–8h Automation** | [`automation.html`](https://karagemop466-tech.github.io/LOLHOTSPAWN4/automation.html) | Technical documentation of Hotspawn's endpoints and the 6-hour GitHub Actions automation workflow |

## Datasets & Scripts

- `data/matches_active_213.json` & `data/matches_active_213.csv`: All 213 active Pick'em matches with UTC/ET timestamps, team records, win probabilities, fair decimal odds, obvious picks, contrarian edges vs Hotspawn crowd %, and verified source URLs.
- `data/filter_bar_reconciliation_264.json`: Exact per-tournament reconciliation of all 24 filter-bar tournaments (`264` filter count vs `213` active DOM cards).
- `data/flagged_irregularities.json`: Structured audit log of all 27 flagged active cards.
- `scripts/update_pickems.py`: Main 4–8h updater script invoked by `.github/workflows/update-pickems.yml`.
