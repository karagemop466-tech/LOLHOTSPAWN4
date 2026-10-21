# Coordination Board

Session: `arena/6b271c44-lolhotspawn4` (branch `arena/6b271c44-lolhotspawn4` per Arena platform tracking rules)

| Task | Status | Owner | Files |
|---|---|---|---|
| T1: Hotspawn LoL fixture ingest (internal API `api/v1/fixtures` + SSR lobby fallback) | in progress | arena/6b271c44 | scripts/update_picks.py, .github/workflows/update-picks.yml |
| T2: External odds adapters (Polymarket Gamma API + OddsPapi LoL sportId 18) | in progress | arena/6b271c44 | scripts/update_picks.py |
| T3: Originated line model (Leaguepedia Cargo Elo K=32 + Bayesian shrinkage + 50/50 unresolved) | in progress | arena/6b271c44 | scripts/update_picks.py |
| T4: Mobile-first GitHub Pages dashboard & Executive Summary with in-site pick links | in progress | arena/6b271c44 | index.html, picks.html, assets/, docs/ |
| T5: Separate Unresolved section + Flagged for Review page + explicit limitations | in progress | arena/6b271c44 | unresolved.html, flagged.html, methodology.html, docs/ |
| T6: Automation workflow (6-hour refresh schedule, strict schema validation, commit & deploy) | in progress | arena/6b271c44 | .github/workflows/update-picks.yml |
| T7: Integration, line-by-line verification, PR to main, merge, Pages deployment confirmation | unclaimed | arena/6b271c44 | COORDINATION.md |

## Verified Sources (checked 2026-10-21)
- Hotspawn LoL Lobby: https://play.hotspawn.com/lol-pickems
- Hotspawn Main Lobby: https://play.hotspawn.com/lobby
- Hotspawn How It Works (pick lock 5 min pre-match): https://play.hotspawn.com/how-it-works
- Hotspawn Internal Fixtures API: https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures?sport_alias=lol&status=scheduled&tenantId=1
- Polymarket Gamma API (LoL prediction markets): https://gamma-api.polymarket.com/events?tag_slug=league-of-legends
- OddsPapi LoL Odds API (sportId 18, winner market 181, 100+ bookmakers incl. Pinnacle/bet365): https://oddspapi.io/sports/esports/lol
- Leaguepedia Cargo API (ScoreboardGames results for Elo model): https://lol.fandom.com/api.php?action=help&modules=cargoquery
- Leaguepedia LoL Esports Wiki: https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki
- Game of Legends (GOL.gg) Esports Database: https://gol.gg/tournament/list/
- Pinnacle Esports API Documentation: https://github.com/pinnacleapi/pinnacleapi-documentation

## Known Irregularities & Standing Flags (Published on Flagged page)
1. **Direct Sandbox Egress:** The local sandbox environment allows outbound traffic only to GitHub, NPM, and PyPI. Live scraping of Hotspawn, Polymarket, and Leaguepedia executes inside GitHub Actions runners (`ubuntu-latest`), which have unrestricted internet access.
2. **Waiting For Information Tier:** Many lower-tier and amateur matches on Hotspawn have tier or stage listed as "WAITING FOR INFORMATION". These matches are clearly flagged in the dataset and UI.
3. **Low-Tier Esportsbook Coverage:** Lower-tier regional leagues (e.g., PRM 3rd Division, amateur regional cups) are rarely quoted by commercial sportsbooks or Polymarket. Our pipeline originates its own line using historical Leaguepedia match results (Elo), and where no competitive history exists, assigns a 50/50 baseline with full disclosure.
4. **Hotspawn Crowd Percentage:** Hotspawn displays crowd pick percentages (e.g., "89% picked") on the lobby cards. In accordance with system instructions, crowd percentage is strictly treated as informational context and is **never** used as an indicator or input for match win probability.
