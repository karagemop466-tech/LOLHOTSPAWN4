# Coordination Board

Shared task board and integration record for parallel agent sessions working on
`karagemop466-tech/LOLHOTSPAWN4`. Final state recorded by the integration session
`arena/0a18d42d-lolhotspawn4` on 2026-10-21.

## Task Board (final)

| Task | Status | Session / Owner | Notes |
|---|---|---|---|
| T1: Hotspawn LoL fixture ingest (internal fixtures API + SSR fallback) | done | both sessions (integrated) | `collector/fetch_hotspawn.py` (verified raw layer) + SSR fallback kept in `scripts/update_picks.py`. |
| T2: External odds adapters (Polymarket, Kalshi, Pinnacle, OddsPapi) | done | both sessions (integrated) | `collector/fetch_odds.py` (Polymarket + Kalshi + Pinnacle, verified); OddsPapi path kept (dormant without key); Kalshi futures added as a first-class derived-line tier. |
| T3: Originated line model for uncovered matches | done | both sessions (integrated) | Kalshi-futures ratio model + Leaguepedia Elo (K=32, 180d, sample-size shrinkage) + explicit 50/50 no-edge baseline. Elo fetch made rate-limit-safe (one batch per run, persistent cache). |
| T4: Mobile-first GitHub Pages dashboard & Executive Summary | done | `arena/6b271c44` site adopted, enhanced by integration | 5 pages (index/picks/unresolved/flagged/methodology), card + table views, filters, stale-data banner, locked-out register, Pinnacle coverage badge. |
| T5: Unresolved section + Flagged for Review + limitations | done | both sessions (integrated) | Dedicated pages + executive-summary section; flagged page now also lists locked-out fixtures, Game-1-market proxies, verified aliases, time discrepancies. |
| T6: Automation (4–8h refresh, schema validation, safe commit, deploy) | done | both sessions (integrated) | `refresh.yml` (4h primary) + `update-picks.yml` (6h backup) run the identical chain; shared concurrency group; rebase-before-push; validation gate; check-annotation fallback for log outages. |
| T7: Integration, line-by-line verification, PRs, merge, Pages confirmation | done | `arena/0a18d42d` (this session) | See Handoff / completion below. |

## Cross-Session Log (2026-10-21)

- `arena/0a18d42d-lolhotspawn4` (this session) shipped the verified raw-data layer
  (`collector/`), the first site iteration, and `refresh.yml` (PRs #4, #5, #6).
  Debug harness for log-endpoint outages: PR #10. Collector `NameError` fix + first
  successful live data run + offline smoke test: PR #12 (merged; run 39671286429
  succeeded, first `data/` commit b7be56d at 20:33Z).
- `arena/6b271c44-lolhotspawn4` (other session) shipped a parallel implementation:
  5-page mobile site, `scripts/update_picks.py` (Leaguepedia Elo originator), and
  `update-picks.yml` (6h). Merged as PR #8 at 20:34Z, replacing the root site files
  with its design and adding its resolver step to `refresh.yml`.
- **Overlap assessment (integration decision):** the two implementations agreed on
  all 8 market lines (independent cross-verification, see I-9). The other session's
  site was adopted as the live design (it covers every match with an explicit pick
  or a no-edge 50/50, and was already merged/live). This session's `collector/`
  raw layer (verified endpoints + manifest + audit) was kept as the data foundation;
  `collector/build.py`/`data/matches.json` (orphaned duplicate dataset) and the
  duplicate `docs/` site copy + orphaned `css/`+`js/` assets were removed. No other
  session's functional work was discarded; everything removed was dead or duplicated
  code, listed here for the audit trail.
- **PR #14 (`arena/6b271c44`, merged 20:40Z, concurrent with this integration):**
  added `data/seeded_ratings.json` — a snapshot of the Elo model (20 teams, 2–9
  games each) used to bootstrap ratings while the rate-limited Leaguepedia cache
  fills. **Integrated:** the resolver now loads the seed and fills gaps in the
  live cache (cache values always win; seeded teams keep their small sample
  counts → "Low confidence" labels). PR #14 also re-wrote `data/matches.json`
  (4-way output duplication incl. `docs/data/`) — those regenerated files are
  superseded by `data/picks.json` in this integration and the duplicate outputs
  were removed (documented under Integration decisions).
- **PR #16 (`arena/6b271c44`, merged 20:43Z):** COORDINATION.md finalization by
  that session (264-fixture audit, 64 Elo lines under the pre-integration
  pipeline, Pages deploy check). Superseded by this record; its raw-data refresh
  commit (aaffbc0, 20:43Z) supplied the freshest raw snapshots, which this
  integration's dataset is built from.

## Verified Source Log (all checked 2026-10-21, from this session unless noted)

- **I-1 Hotspawn fixtures API:** `https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures?sport_alias=lol&status=scheduled` — 27 chunks, all scheduled LoL fixtures, no pagination. Status tokens: scheduled/ended/cancelled (others return `[]`). `tenantId=1` param also accepted (verified for the other session's URL). Fixture schema includes `lock_time` (ms epoch) — picks lock 5 min pre-match.
- **I-2 Hotspawn match pages/logos:** `https://www.hotspawn.com/matches/<slug>-<fixtureId>`; logos `…/teams/<teamId>.svg` (same host as the fixtures API).
- **I-3 Pinnacle:** guest API structure verified (`/sports` E-Sports id 12; LoL leagues 9587 Worlds, 225201 EMEA Masters; `/leagues/<id>/matchups` with `has_markets: true`). **No public price endpoint** (all `/matchups/<id>/markets` and `/markets?matchupId=` variants → 404 on guest and non-guest hosts; pinnacle.com web pages bot-blocked). Pinnacle is therefore a coverage flag only.
- **I-4 Polymarket gamma:** LoL primary tag id 65 (sport "lol", id 39). `/events?tag_id=65&closed=false` → open LoL markets incl. per-match "Match Winner" markets for Worlds 2026 + EMEA Masters; `sport=` param is ignored (use tag_id). G2/DK event `lol-g2-dk-2026-10-23` verified at 0.395/0.605 (page shows 40¢/61¢). Public URL pattern `https://polymarket.com/event/<slug>`.
- **I-5 Kalshi:** `https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXLOL&status=open` → open KXLOL Worlds-2026 futures for all 16 teams (T1 0.175, Gen.G 0.315… MKOI 0.005 at 20:15Z). `/series/<ticker>/markets` is 404 (wrong shape).
- **I-6 Hotspawn "picked %"** is the crowd percentage — **forbidden as a probability input** (project rule). Stored as context only.
- **I-7 First live run failures (this session's debugging):** PR #5/#6 runs failed in 0s → unquoted `if:` expression containing `: ` broke the workflow YAML (fixed by quoting; validate with pyyaml). Run 39670357627 failed in the collector step → `NameError: name 'log' is not defined` (bare `log()`; fixed in PR #12). `gh run view --log` endpoint EOF → tracebacks now re-emitted as `::error` check annotations + step summary.
- **I-8 Fandom/Leaguepedia:** Cargo API works and returns real results (`SG.DateTime_UTC >= '…' AND SG.Winner IS NOT NULL`), but **rate-limits datacenter clients** — the other session's 12-batch pagination from the runner returned 0 rows (observed `elo_teams: 0`). Integration fix: one 500-game batch per run, persistent cache `data/raw/leaguepedia_games.json`, cache reuse on failure.
- **I-9 Cross-verification of market lines (two independent implementations):** this session's 20:33Z build and the other session's 20:34Z run produced identical 8 Polymarket lines (Galions/Solary 51.5/48.5; Gen.G/IG 77.5/22.5; HLE/TES 77.5/22.5; BLG/MKOI 82.5/17.5; AL/KC 65.5/34.5; G2/DK 39.5/60.5; TL/CTBC 71.5/28.5; TSW/LYON 41.5/58.5).
- **I-10 Start-time discrepancies:** Hotspawn's scheduled start differs from market-listed starts by 1–4h on several Worlds matches (e.g. T1/LØS: Hotspawn 23:00Z vs Polymarket "6:00 PM ET" = 22:00Z, verified on the event page). Matching uses same-day/36h windows; the discrepancy is flagged on the Flagged page.
- **I-11 Locked-out fixtures:** the API returns 264 "scheduled" fixtures but 69 have `lock_time` in the past (e.g. Aug/Sep fixtures never resolved). Only fixtures with `lock_time >= now` are available picks (195 at 20:40Z). Locked-out fixtures are excluded from the board and listed on the Flagged page (`excluded_stale`), never silently dropped.
- **I-12 Verified alias LØS = LOS:** Hotspawn "LØS" (Nordic spelling) = Polymarket "LOS" (event `lol-los-t1-2026-10-23`, page verified: LOS 13¢/T1 88¢, "6:00 PM ET" 2026-10-23) = Kalshi "LOS" (`KXLOL-WORLDS26-LOS`). The only alias in the matcher's table; added after verification, documented here and on the Flagged page.
- **I-13 Game-1 vs series markets:** Polymarket lists only a "Game 1 Winner" market for Galions/Solary (Bo5). Series/moneyline markets are preferred; when only a Game-1 market exists the row is labeled "(Game-1 market only — no series market found; flagged)" and filterable on the Flagged page.

## Integration Decisions (made 2026-10-21 by `arena/0a18d42d`, final integrator)

1. **Single canonical dataset:** `data/picks.json` (rendered by the site). `collector/build.py` + `data/matches.json` (duplicate dataset, no longer rendered) removed; `collector/` fetchers + `common.py` kept as the verified raw layer feeding `scripts/update_picks.py` (snapshots-first, direct fetch only as fallback).
2. **Five-stage resolution waterfall** in `update_picks.py`: MARKET_BOOKS (OddsPapi, with key) → MARKET_POLYMARKET (exact mids, series preferred, Game-1 flagged) → KALSHI_FUTURES (our ratio line) → MODEL_ELO (Leaguepedia, rate-limit-safe) → UNRESOLVED 50/50 with `no_edge` (rendered "⚖️ No Edge").
3. **Available-pick filter:** only `lock_time >= now` fixtures on the board; locked-out fixtures published in `excluded_stale`.
4. **Workflows:** `refresh.yml` (4h) is primary; `update-picks.yml` (6h) kept as backup cadence but now runs the identical full chain; shared concurrency group `lol-pick-refresh`; commit step rebases before push (the previous `git pull --rebase … || true` silently dropped pushes — root cause of the failed "Commit updated data" step in run 39671452009); both workflows push-trigger guards exclude each other's data-commit messages; schema validation gate before every commit; failure keeps previous data but fails loudly with check annotations.
5. **Site enhancements (other session's design kept):** KALSHI_FUTURES badge + filter, Pinnacle coverage badge, no-edge rendering in table views, STALE DATA banner (driven by `stale_sources` from the raw manifest), locked-out register on the Flagged page, methodology updated to the five-stage model with the Kalshi + Pinnacle source rows.
6. **Removed (dead/duplicated only):** `docs/` (duplicate site copy — Pages serves the main-branch root), `css/` + `js/` (orphaned first-iteration assets), `collector/build.py`, `data/matches.json`, tracked `__pycache__` artifacts (re-added by the other session's merge despite `.gitignore`).

## Open Items / Maintenance Notes

- **OddsPapi key:** `ODDSPAPI_KEY` secret not configured → Tier 1 (commercial books) dormant; Polymarket + Kalshi cover the priced tier.
- **Leaguepedia cache:** starts empty in the repo and grows one batch per successful run (Fandom rate limit); until it fills, matches with wiki history fall through to UNRESOLVED rather than inventing lines.
- **Pinnacle prices:** if a public price endpoint ever appears, Tier 3 (Kalshi) can be promoted below it — currently coverage flag only.
- **`play.hotspawn.com/lol-pickems`** redirects/serves the shared lobby; the canonical lobby URL used in the UI is `https://play.hotspawn.com/lobby`.

## Handoff / completion

- **Live site:** https://karagemop466-tech.github.io/LOLHOTSPAWN4/ (Pages source: `main`, root).
- **Merged PRs to main (all by the two sessions):**
  - #4 — site + collector + `refresh.yml` (`arena/0a18d42d`)
  - #5 — push-to-main trigger with loop guard (`arena/0a18d42d`)
  - #6 — quoted `if:` expression (fixed 0s-failure YAML) (`arena/0a18d42d`)
  - #8 — Elo originator + 5-page mobile site + `update-picks.yml` (`arena/6b271c44`)
  - #10 — check-annotation debug harness for log-endpoint outages (`arena/0a18d42d`)
  - #12 — collector `NameError` fix + offline smoke test (`arena/0a18d42d`; first successful live data run 39671286429)
  - #14 — Elo seed ratings + 264-match audit (`arena/6b271c44`)
  - #16 — COORDINATION finalization + raw-data refresh (`arena/6b271c44`)
  - #17 — **final integration**: canonical `update_picks.py` five-stage resolver (incl. seeded Elo bootstrap), available-pick filter + locked-out register, rate-limit-safe Leaguepedia Elo, Kalshi futures tier, LØS/LOS alias, workflow concurrency/rebase/validation fixes, site enhancements, README + this record.
  - #18 — sibling-conflict-safe commit step (both workflows) + this record update.
  - #19 (`https://github.com/karagemop466-tech/LOLHOTSPAWN4/pull/19`, `arena/a8a4df4b-lolhotspawn4`) — Leaguepedia `Data:<Tournament>?action=raw` full-split origination expansion & deep-dive subpages:
    - Fixed `load_seed_ratings()` in `scripts/update_picks.py` to normalize multi-word team keys via `canon(v.get("team") or k)` and populated `data/raw/leaguepedia_games.json` (1,069 verified games) + `data/seeded_ratings.json` (250 teams) from official Leaguepedia `Data:` pages across all 13 active tournaments (`Komplettligaen`, `RIVALS LEAGUE`, `4 Nations Halloween Heist`, `PRM 2nd/3rd Division`, `Arabian League 2nd Division`, `ARC 2026`, `LigaGG CELOL B Playoffs`, `LCP 2027 Promotion`, `LGC Rising Playoffs`).
    - Upgraded `data/picks.json` coverage from `59 MODEL_ELO / 127 UNRESOLVED` to **`170 MODEL_ELO / 9 MARKET_POLYMARKET / 16 UNRESOLVED`** (where the 16 `UNRESOLVED` rows are exclusively `0-0` opening-week `Tunisian Super League 2026` municipal teams with zero prior Leaguepedia games).
    - Added static Leaguepedia & bookmaker deep-dive subpages (`featured.html`, `originated.html`, `automation.html`) and audit datasets (`data/matches_active_213.json`, `data/matches_active_213.csv`, `data/filter_bar_reconciliation_264.json`, `data/flagged_irregularities.json`) documenting the `264 (filter bar) - 53 (stale/locked) + 2 (PRM 2nd Div Oct 23 duplicates) = 213 active DOM cards` reconciliation and `Solid Gaming`'s official `0-2` disqualification forfeit (`#1059956`).
- **Merge result #17:** MERGED at 20:44Z (merge commit 4e6762c). Both refresh
  workflows fired on the merge push: the 6h run (39672980151) succeeded and
  committed the first live dataset of the integrated pipeline (a86572e,
  20:45:08Z: 195 pickable, 9 market lines incl. the LØS/T1 alias recovery,
  59 seeded Elo lines — the runner's polite Leaguepedia fetch succeeded on the
  first attempt —, 127 no-edge, 69 locked-out excluded). The 4h run
  (39672980094) failed only in its commit step: its rebase hit a
  timestamp-only conflict against the sibling run's identical data commit.
  Pages deploy of the integrated site: **success** (20:45:11Z).
- **Follow-up #18 (MERGED 20:49Z, 05a0b9c):** commit step made
  sibling-conflict-safe (on rebase conflict of two same-chain data commits, the
  version already on `main` wins and the losing run exits cleanly without
  pushing). Post-merge validation: both refresh workflows SUCCESS on the
  20:46Z trigger; latest committed dataset 366868f (20:50:54Z: 195 pickable /
  9 market lines / 59 Elo / 127 no-edge / 69 excluded, `stale_sources` empty);
  Pages deploy SUCCESS; live pages + `data/picks.json` fetch-verified.
- **Pages status:** deployed and verified live at
  https://karagemop466-tech.github.io/LOLHOTSPAWN4/ (pages + `data/picks.json`
  fetch-checked post-merge).
- **Handoff:** complete. No open work items; the desk runs autonomously.
- **Maintenance cadence:** `refresh.yml` every 4h (primary), `update-picks.yml` every 6h (backup); both auto-deploy to Pages via the `main` data commit. Smoke test: `python3 test/offline_smoke.py` (offline, no network).
