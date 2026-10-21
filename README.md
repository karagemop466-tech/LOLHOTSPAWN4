# Hotspawn League of Legends (LoL) Pick'em Win Probability & Pick Origination

An automated, mobile-friendly intelligence platform providing match-winner probabilities and picks for **every League of Legends match** featured on the [Hotspawn Pick'em Lobby](https://play.hotspawn.com/lol-pickems).

🌐 **Live GitHub Pages Dashboard:** [https://karagemop466-tech.github.io/LOLHOTSPAWN4/](https://karagemop466-tech.github.io/LOLHOTSPAWN4/)

---

## Key Features

1. **100% Fixture Coverage:** Generates a pick and win probability for every match listed on Hotspawn, including lower-tier regional and amateur events.
2. **Strict Independence from Hotspawn Crowd %:** Hotspawn's public crowd pick percentage is treated strictly as informational context and is **never** used as an indicator or input for match win probability.
3. **Multi-Layered Origin Model:**
   - **Esportsbook Market Lines:** Median de-vigged implied probability across commercial bookmakers (Pinnacle, bet365, BetOnline) via OddsPapi (Sport ID: 18).
   - **Prediction Markets:** Equilibrium traded prices from Polymarket (Gamma API).
   - **Our Originated Elo Model:** Continuous Elo rating model ($K=32$) trained on 180 days of competitive match results from Leaguepedia's Cargo API (`ScoreboardGames` table), with Bayesian sample-size shrinkage toward 50%.
   - **Transparent 50/50 Baseline:** When zero market and zero historical data exists, matches are classified as `UNRESOLVED` (50.0% / 50.0% baseline, coin-flip with no edge) and flagged with detailed limitations.
4. **Mobile-First UX:**
   - Executive Summary with direct, finger-friendly navigation to picks by category.
   - High-contrast visual win probability bars and prominent green pick badges (`✅ PICK: Team (XX%)`).
   - Dual view modes: **Mobile Card View** and **Tabular Data View**.
   - Instant search and filtering by Tournament, Tier, and Resolution Method.
5. **Automated 6-Hour Refresh:** GitHub Actions workflow (`.github/workflows/update-picks.yml`) runs every 6 hours, re-ingests fixtures, originates probabilities, validates schema integrity, and publishes updates to GitHub Pages.

---

## Site Pages & Navigation

- **🏠 [Executive Summary](https://karagemop466-tech.github.io/LOLHOTSPAWN4/):** Overview of coverage metrics, direct links to pick categories, dedicated Unresolved Picks & Limitations section, and featured market picks.
- **✅ [All Picks](https://karagemop466-tech.github.io/LOLHOTSPAWN4/picks.html):** Comprehensive directory of all 190+ matches with search, filters, sorting, cards view, and tabular view.
- **⚠️ [Unresolved Picks](https://karagemop466-tech.github.io/LOLHOTSPAWN4/unresolved.html):** Isolated directory of low-tier amateur fixtures with full limitation disclosures.
- **🚩 [Flagged for Review](https://karagemop466-tech.github.io/LOLHOTSPAWN4/flagged.html):** Audit register cataloging fixtures with provisional `WAITING FOR INFORMATION` metadata or missing historical match data.
- **📖 [Methodology & Sources](https://karagemop466-tech.github.io/LOLHOTSPAWN4/methodology.html):** Detailed mathematical formulation of the de-vigging process, Bayesian shrinkage Elo model, and verified source links.

---

## Verified Official Sources

| Source | Role | Verified Link |
|---|---|---|
| **Hotspawn LoL Pick'ems** | Fixture identity, schedule, offered points | [play.hotspawn.com/lol-pickems](https://play.hotspawn.com/lol-pickems) |
| **Hotspawn Backend API** | Direct REST fixture ingest | [Cloudways Fixture API](https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures?sport_alias=lol&status=scheduled&tenantId=1) |
| **Hotspawn Rules** | Pick lock timings (5 min pre-match) | [play.hotspawn.com/how-it-works](https://play.hotspawn.com/how-it-works) |
| **Polymarket Gamma API** | Match-winner prediction markets | [gamma-api.polymarket.com](https://gamma-api.polymarket.com) |
| **OddsPapi LoL Network** | Bookmaker odds aggregation (Sport ID 18) | [oddspapi.io/sports/esports/lol](https://oddspapi.io/sports/esports/lol) |
| **Leaguepedia Cargo API** | Competitive match histories (`ScoreboardGames`) | [lol.fandom.com/api.php](https://lol.fandom.com/api.php?action=help&modules=cargoquery) |
| **Leaguepedia Esports Wiki** | Team rosters, tournament structures | [lol.fandom.com](https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki) |
| **Game of Legends (GOL.gg)** | Match stats cross-referencing | [gol.gg](https://gol.gg/tournament/list/) |
| **Pinnacle Esports API Docs** | Sharp bookmaker odds reference | [github.com/pinnacleapi](https://github.com/pinnacleapi/pinnacleapi-documentation) |

---

## Automation Pipeline

The repository uses GitHub Actions (`.github/workflows/update-picks.yml`):
- Runs every 6 hours on a cron schedule (`0 */6 * * *`) and supports manual execution (`workflow_dispatch`).
- Executes `scripts/update_picks.py` to query Hotspawn, external market APIs, and Leaguepedia.
- Performs strict data integrity tests: ensures every match has a pick, probabilities sum to 1.0, and official source links exist.
- Commits updated JSON payloads (`data/picks.json` and `docs/data/picks.json`), automatically triggering GitHub Pages deployment.
