# LOL Hotspawn Pick Desk

Win probabilities and picks for **every League of Legends match open for picks
on the [Hotspawn Pick'Em lobby](https://play.hotspawn.com/lobby)** — sourced
from **external betting / prediction markets only** (Polymarket, Kalshi,
Pinnacle). Hotspawn's own crowd percentages are never used as a probability
signal.

**Live site (GitHub Pages, serves `main`):**
<https://karagemop466-tech.github.io/LOLHOTSPAWN4/>

- **Executive summary** — <https://karagemop466-tech.github.io/LOLHOTSPAWN4/index.html>
- **All matches & picks** (mobile-friendly) — <https://karagemop466-tech.github.io/LOLHOTSPAWN4/picks.html>
- **Flagged for Review** (unresolved picks, limitations, irregularities) — <https://karagemop466-tech.github.io/LOLHOTSPAWN4/flagged.html>
- **Methodology & sources** — <https://karagemop466-tech.github.io/LOLHOTSPAWN4/methodology.html>

## How it works

1. **Match list** — the refresh job fetches Hotspawn's public fixtures API
   (`sport_alias=lol&status=scheduled`), which is the same data the lobby's
   LoL tab renders (teams, tournament, start/lock times, tier, stage, points).
2. **Lines** — the same job fetches external markets:
   - **Polymarket** (gamma API, LoL tag 65): per-match "Match Winner" markets
     where they exist (Worlds 2026, EMEA Masters) → probability = market mid.
   - **Kalshi** (`KXLOL` series): tournament futures mids, used as labeled
     inputs to our derived line where no per-match market exists.
   - **Pinnacle** (guest Arcadia API): LoL matchup coverage check only — its
     public API exposes no prices (verified 404s, see COORDINATION.md).
3. **Picks** — market-line pick (higher market mid) > derived estimate
   (transparent futures ratio model, labeled, low confidence) > unresolved
   (no verified market → pick left blank, listed on the Flagged page).
   Nothing is ever invented.
4. **Publish** — the job commits `data/` back to the branch it runs on;
   GitHub Pages serves `main`, so the site updates automatically.

## Refresh schedule

GitHub Actions (`.github/workflows/refresh.yml`) runs **every 4 hours**
(cron `0 */4 * * *`) plus on manual dispatch:

```
gh workflow run refresh.yml --ref <branch>
```

## Repo layout

| Path | Purpose |
|---|---|
| `collector/common.py` | Shared helpers (HTTP, snapshots, team-name matching) |
| `collector/fetch_hotspawn.py` | Fetch + validate the Hotspawn LoL fixture list |
| `collector/fetch_odds.py` | Fetch Polymarket / Kalshi / Pinnacle lines |
| `collector/build.py` | Match fixtures→lines, produce picks, write `data/matches.json` |
| `data/matches.json` | Canonical dataset the site renders |
| `data/raw/` | Raw/normalized API snapshots + `manifest.json` (URL, time, SHA-256) |
| `index.html`, `picks.html`, `flagged.html`, `methodology.html` | GitHub Pages site (mobile-first) |
| `css/style.css`, `js/app.js` | Site assets (no external dependencies) |
| `COORDINATION.md` | Shared coordination board for parallel agent sessions |

## Verification policy

- Every table row carries a source link to the official site/API it came from.
- Every number carries a fetch timestamp (`data/raw/manifest.json`).
- If a value cannot be confirmed from a verified source it is left blank and
  flagged (see the site's Flagged for Review page) — never inferred or filled in.
