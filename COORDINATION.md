# Coordination board

Shared task board for parallel agent sessions working on this repo (see the
project brief for the protocol: claim before working, small frequent commits,
`git pull --rebase` before push, shared outputs only via a final integration
session).

| Task | Status | Session / owner | Files in scope | Notes |
|---|---|---|---|---|
| LoL Hotspawn pick desk — source research, collector, 4h refresh workflow, mobile GitHub Pages dashboard, audits | in progress | `arena/0a18d42d-lolhotspawn4` | `collector/`, `data/`, `.github/workflows/refresh.yml`, `index.html`, `picks.html`, `flagged.html`, `methodology.html`, `css/`, `js/`, `README.md`, this file | Claim logged 2026-10-21 ~20:20 UTC. Full pipeline: Hotspawn fixtures API + Polymarket/Kalshi/Pinnacle lines → `data/matches.json` → static site on GitHub Pages (main, path /). |
| "Build the LoL Hotspawn pick desk" (pre-existing broad claim) | in progress | `arena/1a78ec3b-lolhotspawn4` | claim text says "Repository files (new project; no existing site/data files)" | Claim commit 9314ecc (2026-10-21 20:15:28 UTC) predates this claim. See conflict note below. |

## Conflict / overlap note (logged 2026-10-21 ~20:20 UTC)

Two sessions received the same project brief and both claim the project. To
avoid clobbering each other:

- `arena/0a18d42d-lolhotspawn4` proceeds with the full implementation on its
  own branch using the file scope in the table above (all *new* files; no
  pre-existing site/data files exist to conflict on).
- If `arena/1a78ec3b-lolhotspawn4` publishes overlapping files to `main`
  before this session's PR merges, the final integration step (owned by
  `arena/0a18d42d-lolhotspawn4` per the user's instructions to that session:
  "create a pull request … then merge the pull request without waiting for
  approval") will rebase onto `main`, keep the other session's work wherever
  it is not broken, and re-verify the combined data line by line before the
  merge. No file owned by the other session is edited directly; any needed
  change is logged here instead.
- If either session's claim is >60 min old with no new commits, the other may
  take over per the protocol; this session will note any handoff here.

## Source research / verification log

All items below were fetched and inspected directly on 2026-10-21 (UTC)
via live HTTP requests (no inference). "Verified" = response content matched
the stated finding.

### Match list (Hotspawn)
- Verified: `https://play.hotspawn.com/lobby` — Pick'Em lobby; LoL tab; weekly
  reset; per-match "x% picked" crowd stats (NOT used as probability signal).
- Verified: `https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures`
  — public fixtures JSON (CS2+LoL+test rows). Host serves the lobby's team
  logos (unofficial backend; flagged I-2).
- Verified: `…/api/v1/fixtures?sport_alias=lol&status=scheduled` — returns
  exactly the LoL fixtures open for picks (schema: id, competition_id/name,
  sport_alias, status, scheduled_start_time, lock_time, tier, stage,
  offered_points, points_breakdown, participants0/1 id/name/picked_percent).
  Other status values observed: `ended`, `cancelled`. Unknown query params are
  rejected (400, strict validator).
- Verified: `…/api/v1/competitions` — tournament metadata (external_id maps to
  EsportsDB-style ids; includes LoL and CS2).

### Lines / probabilities (external only — Hotspawn never used)
- Verified: Polymarket gamma API
  - `https://gamma-api.polymarket.com/sports` — LoL sport: id 39, slug "lol",
    primaryTagId 65, resolution hint liquipedia.net/leagueoflegends.
  - `https://gamma-api.polymarket.com/events?tag_id=65&closed=false` — open LoL
    events (Worlds 2026, EMEA Masters; "Worlds 2026: Winner" team markets;
    per-match "Match Winner" markets).
  - `https://gamma-api.polymarket.com/public-search?q=…` — used for spot checks.
  - Verified: match market "LoL: G2 Esports vs Dplus KIA (BO1) — Worlds Group
    Stage" (`https://gamma-api.polymarket.com/events` slug
    `lol-g2-dk-2026-10-23`): outcomes [G2 Esports, Dplus KIA], mids 0.395/0.605;
    public page `https://polymarket.com/event/lol-g2-dk-2026-10-23` reachable,
    shows 40¢/61¢, resolves via gol.gg; event URL redirects to
    `/esports/league-of-legends/worlds/lol-g2-dk-2026-10-23`.
  - Quirk (I-5): `sport=lol` param ignored by /events; use `tag_id=65`.
- Verified: Kalshi public API
  - `https://api.elections.kalshi.com/trade-api/v2/series/KXLOL` — "League of
    Legends" series, category Sports, tag Esports, settlement via
    lolesports.com; scope "Future".
  - `https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXLOL&status=open`
    — open tournament futures (e.g., "Will T1 win League of Legends Worlds?"
    bid/ask 17¢/18¢; Team Liquid 1¢/2¢; Top Esports 1¢/2¢). No per-match
    markets found (I-6).
- Verified: Pinnacle guest Arcadia API
  - `https://guest.api.arcadia.pinnacle.com/0.1/sports` — "E Sports" id 12,
    43 matchups.
  - `…/0.1/sports/12/leagues` — LoL leagues with lines: "League of Legends —
    World Championship" (id 9587, 10 matchups), "League of Legends — EMEA
    Masters" (id 225201, 1 matchup).
  - `…/0.1/leagues/9587/matchups`, `…/0.1/leagues/225201/matchups` — LoL
    matchups with participants, start times, BoX (e.g., Solary vs Galions Bo5
    2026-10-22T16:00Z; G2 vs Dplus KIA 2026-10-23T20:00Z).
  - NOT available (verified 404s, I-3): `…/0.1/matchups/<id>/markets`,
    `…/0.1/markets?matchupId=<id>`, same on `api.arcadia.pinnacle.com`
    (non-guest). Web pages return HTTP 500 to the fetcher (bot protection).
    → Pinnacle used as coverage flag only; no numeric Pinnacle line published.
- Verified (reference only, I-8): `https://liquipedia.net/leagueoflegends/World_Championship/2026`
  and `https://liquipedia.net/leagueoflegends/Main_Page` — community wiki,
  linked for manual review only; no data values sourced from it.

### Data quality flags (see flagged.html on the site)
- I-1: unfiltered fixtures endpoint contains test rows (ids 1, 3, 999999).
- I-2: Hotspawn backend host is unofficial (phpstack-*.cloudwaysapps.com).
- I-3: Pinnacle has no public price endpoint (404s verified).
- I-4: Worlds 2026 in progress at first publication (Pinnacle + Polymarket
  agree on the Oct 23 matches; Polymarket runs through Nov 14, 2026).
- I-5: Polymarket /events `sport=` param quirk (use tag_id).
- I-6: Kalshi KXLOL currently futures-only.
- I-7: team-name matching is approximate; misses degrade to "unresolved".
- I-8: Liquipedia = reference links only.

## Handoff / completion

- Final integration (rebase onto main, re-verify combined data line by line,
  confirm no broken links, PR + merge to main, confirm GitHub Pages deploy,
  record PR link and merge result here) is owned by
  `arena/0a18d42d-lolhotspawn4` and will be recorded below when finished.
