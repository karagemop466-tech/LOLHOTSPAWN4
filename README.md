# Hotspawn League of Legends (LoL) Pick'em Win Probability & Pick Origination

An automated, mobile-friendly intelligence platform providing match-winner probabilities and picks for **every available League of Legends pick** on the [Hotspawn Pick'em Lobby](https://play.hotspawn.com/lobby).

🌐 **Live GitHub Pages Dashboard:** [https://karagemop466-tech.github.io/LOLHOTSPAWN4/](https://karagemop466-tech.github.io/LOLHOTSPAWN4/)

---

## Key Features

1. **Full Available-Pick Coverage:** Every fixture whose Hotspawn pick-lock time has not passed is listed with a pick and win probability, including lower-tier regional and amateur events. Fixtures already locked out are excluded from the board and listed on the Flagged for Review page for audit (nothing silently dropped).
2. **Strict Independence from Hotspawn Crowd %:** Hotspawn's public crowd pick percentage is treated strictly as informational context and is **never** used as an indicator or input for match win probability.
3. **Five-Stage Resolution Waterfall** (highest priority first):
   - **Esportsbook Market Lines:** Median de-vigged implied probability across commercial bookmakers via OddsPapi (Sport ID 18) — active when an `ODDSPAPI_KEY` secret is configured.
   - **Prediction Markets:** Polymarket (Gamma API) per-match market mids, exactly as reported; series/moneyline markets preferred, Game-1-only matches flagged.
   - **Our Derived Line (Kalshi futures):** ratio model `p(A)=f(A)/(f(A)+f(B))` on both teams' open Kalshi KXLOL tournament-futures mids (same event) — clearly labeled as our line.
   - **Our Originated Elo Model:** Elo (`K=32`, 180-day window) over competitive results from the Leaguepedia Cargo API, with sample-size shrinkage toward 50%. Fetched politely (one batch per refresh, persistent cache; degrades gracefully on rate limits).
   - **Transparent 50/50 Baseline:** `UNRESOLVED` matches get exactly 50.0% / 50.0% and display **⚖️ No Edge** — no invented favorite.
4. **Mobile-First UX:**
   - Executive Summary with direct, finger-friendly navigation to picks by category.
   - High-contrast win probability bars and prominent pick badges (`✅ PICK: Team (XX%)`).
   - Dual view modes: **Mobile Card View** and **Tabular Data View**, with search, filters (method/tier), and sorting.
   - **STALE DATA banner** appears automatically if any source fetch failed on the last refresh.
5. **Automated Refresh:** Two GitHub Actions workflows run the identical pipeline — `refresh.yml` every 4 hours (primary) and `update-picks.yml` every 6 hours (backup cadence) — within the required 4–8 hour window. Both serialize via a shared concurrency group, validate the schema before committing, and commit the dataset back to `main`, which deploys to GitHub Pages automatically.

---

## Site Pages & Navigation

- **🏠 [Executive Summary](https://karagemop466-tech.github.io/LOLHOTSPAWN4/):** Coverage metrics, direct links to pick categories, dedicated Unresolved Picks & Limitations section, and featured market picks.
- **✅ [All Picks](https://karagemop466-tech.github.io/LOLHOTSPAWN4/picks.html):** Directory of every available pick with search, method/tier filters, sorting, cards view, and tabular view.
- **⚠️ [Unresolved Picks](https://karagemop466-tech.github.io/LOLHOTSPAWN4/unresolved.html):** Isolated register of 50/50 fixtures with full limitation disclosures.
- **🚩 [Flagged for Review](https://karagemop466-tech.github.io/LOLHOTSPAWN4/flagged.html):** Audit register: provisional `WAITING FOR INFORMATION` metadata, unresolved fixtures, Game-1-market proxies, verified team-name aliases, time discrepancies, locked-out (excluded) fixtures, and stale-data handling.
- **📖 [Methodology & Sources](https://karagemop466-tech.github.io/LOLHOTSPAWN4/methodology.html):** Full mathematical formulation of each stage and the verified source directory.

---

## Verified Official Sources

| Source | Role | Verified Link |
|---|---|---|
| **Hotspawn LoL Pick'ems** | Fixture identity, schedule, offered points | [play.hotspawn.com/lobby](https://play.hotspawn.com/lobby) |
| **Hotspawn Backend API** | Direct REST fixture ingest (match list only — never probabilities) | [Cloudways Fixture API](https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures?sport_alias=lol&status=scheduled) |
| **Hotspawn Rules** | Pick lock timings (5 min pre-match) | [play.hotspawn.com/how-it-works](https://play.hotspawn.com/how-it-works) |
| **Polymarket Gamma API** | Match-winner prediction markets (LoL tag id 65) | [gamma-api.polymarket.com](https://gamma-api.polymarket.com) |
| **Kalshi KXLOL Series** | Tournament-futures mids for the derived ratio model | [api.elections.kalshi.com KXLOL](https://api.elections.kalshi.com/trade-api/v2/series/KXLOL) |
| **Pinnacle Guest API** | Pro-book matchup coverage check (no public price endpoint) | [guest.api.arcadia.pinnacle.com](https://guest.api.arcadia.pinnacle.com/0.1/sports) |
| **OddsPapi LoL Network** | Bookmaker odds aggregation (Sport ID 18) — with configured key | [oddspapi.io/sports/esports/lol](https://oddspapi.io/sports/esports/lol) |
| **Leaguepedia Cargo API** | Competitive match histories (`ScoreboardGames`) for the Elo model | [lol.fandom.com/api.php](https://lol.fandom.com/api.php?action=help&modules=cargoquery) |
| **Leaguepedia Esports Wiki** | Team rosters, tournament structures | [lol.fandom.com](https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki) |
| **Game of Legends (GOL.gg)** | Resolution source referenced by Polymarket markets | [gol.gg](https://gol.gg/tournament/list/) |

---

## Automation Pipeline

The repository uses two GitHub Actions workflows that run the identical chain:

1. `collector/fetch_hotspawn.py` — verified fixture snapshot → `data/raw/`
2. `collector/fetch_odds.py` — Polymarket + Kalshi + Pinnacle normalized extracts → `data/raw/` (full Polymarket dump kept as a workflow artifact only)
3. `scripts/update_picks.py` — resolves every available fixture into `data/picks.json` (the single dataset the site renders), maintaining the Leaguepedia cache in `data/raw/`
4. Schema verification step (pick present, probabilities sum to 1.0, method allowed, source link present, counts consistent)
5. Commit with rebase (conflict-safe) → GitHub Pages deploy

- `refresh.yml`: cron `0 */4 * * *` (primary) + `workflow_dispatch` + push-to-main trigger (bot data commits excluded to avoid loops).
- `update-picks.yml`: cron `0 */6 * * *` (backup) + `workflow_dispatch` + path-limited push trigger.
- Shared concurrency group `lol-pick-refresh` prevents the two from racing on the data commit.
- On any fetch failure the previous snapshot is reused, the run fails loudly (traceback surfaced as check annotations + step summary), and the published site keeps the last good data with a STALE banner until the next successful refresh.

## Tests

`test/offline_smoke.py` runs the resolver fully offline against fabricated-but-realistically-shaped snapshots and asserts every tier (market line, verified LØS/LOS alias, Game-1-only flag, Kalshi futures ratio, Elo model, 50/50 no-edge, locked-out exclusion, stale-source surfacing). Run with `python3 test/offline_smoke.py`.
