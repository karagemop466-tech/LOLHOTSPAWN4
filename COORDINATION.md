# Current corrective production integration — 2026-10-21 21:28 UTC

- **Owner:** `arena/d126dc4d-lolhotspawn4`, fixed Arena branch of the same name. Other main sessions' boards record their work done; all their files and records are preserved below.
- **Final integration claim:** existing `verified/**`, `verified_pipeline/**`, `.github/workflows/verified-pages.yml`, plus the root **README.md** documentation and GitHub Pages build-type setting needed to publish the tested isolated artifact. No edits to another session's collector, resolver, data, HTML, CSS or active scope.
- **Latest-main integration:** imported `origin/main@e814cde` (including PRs #18/#19). Only `COORDINATION.md` conflicted. Resolved by retaining **both complete boards** below; no code conflict or session work was discarded. This heading is the current status; the root-site deployments/coverage in earlier records are historical, not acceptance of the new artifact.
- **Acceptance status:** first live original-source run `39677260400` passed. Expanded native-history run `39679017944` also passed (54 tests + static + 28 viewport/14 functional checks). Its 11 community-wiki routes returned 403; no native-wiki result was admitted. New implementation now has 57 passing local unit/artifact tests, static integrity and 28 viewport + 14 functional browser checks, including exact HTML/JSON version reconciliation and expected-public-run guards. PR #2 is now merged (see current repair record); verified-only Pages deployment has **not** yet occurred. Next: finish live gate, finalize PR, merge, set workflow Pages publication, and verify actual public artifact.

### Confirmed public acceptance / safe legacy-mirror claim (21:56 UTC)

- **PR #20 MERGED** at 21:49:24Z, `12f17cc97b32fc7e46fd7ce666ef4faad092cf37`. Production run **[39681845410](https://github.com/karagemop466-tech/LOLHOTSPAWN4/actions/runs/39681845410) PASSED build AND actual public deployment acceptance**. Public metadata independently fetched: `artifact=verified-only`, expected run/commit. Public check downloaded/hashed all 16 files, reconciled every ID/source/calculation/internal link (first attempt, 21:51:03Z), then public Chromium passed 28 route/viewport + 14 functional checks. Receipt bot `5655a30` preserved four reports under `audit/d126dc4d/verified-public*.json`.
- The effective Pages settings selector **still reports `legacy/main/root`**, despite successful standard Pages artifact deployment. It is not marked changed. Both old automatic writers are now retired; the verified publisher handles every main push and the 4h schedule. A future main commit can still invoke GitHub's implicit root build before the tested artifact deploy completes.
- **Final integration scope claim:** root `*.html`, new `assets/site.css`, `assets/site.js`, `assets/mark.svg`, the five new root `data/{matches,source-cache,history,integrity,deployment}.json` files, and `legacy_ui/` archive. Purpose: preserve the completed legacy HTML byte-for-byte in an archive, and make implicit legacy root builds show a **dated, independently validated safe mirror** of the verified dashboard, not the rejected synthetic/forced-pick UI. Existing legacy collector/resolver/assets/data remain untouched. The actual Pages artifact stays verified-only; no main bot pushes or user settings action is required.
- Root fallback values retain original observation dates and browser expiry; it is explicitly a dated safety snapshot, not a second live probability pipeline. Add a static fallback acceptance test before integration. Also publish the selector caveat on Flagged for Review, distinguish blank inputs from supported ties in the executive summary, and record this successful run on main after the final gate.

### Production handoff / deployment repair claim (21:45 UTC)

- **PR #2 MERGED** at 21:40:14Z, merge `91f2068c3e267158f02ab08922f032bfc17957a7`. Integrated-branch run `39680424102` passed 57 tests + static + 28 viewport/14 functional gates; tested bot receipt `4061fb7` was merged. Production run `39680659285` **built successfully but failed in the Pages mode-selection step** before any verified-only deployment. Pages still reports `legacy/main/root`; this is not public acceptance. Runner logs/artifact downloads are blocked by sandbox egress; job/check metadata is available.
- **Final-integration scope extension / handoff:** claim `.github/workflows/refresh.yml` and `.github/workflows/update-picks.yml` to retire their automatic historical writers (finished sessions' collector/resolver/data/UI code stays intact). The 21:40 legacy writer `e4c836d` caused another root Pages build, confirming it could overwrite a later artifact if kept active. Only the independently tested four-hour workflow should publish production. Historical workflows will remain manual and limited to this fixed Arena branch, not silently keep writing the old main-root probability dataset.
- Next repair: record optional settings-update failure accurately, then use the standard authorized Pages deployment endpoint with `pages:write` + OIDC. Deployment permission and settings-admin permission are distinct; actual public-run/hash/browser checks remain mandatory. If this supported deployment API also denies publication, preserve that failure rather than claiming success. No credentials, permission escalation or access controls are bypassed.

### Settings permission observation (21:38 UTC)

- `gh pr ready 2` succeeded: PR #2 is now ready for review, not merged yet.
- Direct connected-app `PUT /repos/karagemop466-tech/LOLHOTSPAWN4/pages` to select `build_type=workflow` returned **403 Resource not accessible by integration**; the setting was not changed. This is a confirmed settings-permission result, not a source fact or an authentication prompt.
- Production deploy now requests the standard repository workflow's explicit **`pages: write`** permission to update the **existing** Pages site's build type before deploying. No new token, user credentials, access bypass or alternative branch is used. That authorized workflow operation is still untested; a denial must remain a failure, never a successful-deployment claim.

### Production acceptance preparation (21:37 UTC)

- Latest tested source receipt bot: `078cd9a`, generated at 21:28:10Z by run `39679017944`. **264 IDs / 264 canonical links; 195 upcoming, 69 elapsed; 26 directional picks; 2 bookmaker + 6 prediction-market rows; 22 same-format partial-history estimates including 4 ties; 169 upcoming without a directional pick.** 31 source attempts: 15 HTTP successes (some are only shells), 16 access failures including all 11 native-wiki routes. A failed/native-shell request never became a result or probability.
- Final public-deployment gate added: require the actual Pages URL to serve this run/commit's `verified-only` metadata, download all 16 public HTML/assets/data files, reproduce inventory/calculations/internal links, reject mixed CDN versions, then repeat 28 viewport + 14 functional checks against the public URL. Reports carry actual public-file SHA-256 hashes and are retained as Actions artifacts. This gate has not run in production yet.
- Root README now documents only the isolated production path and honest gaps. Existing legacy functional files/workflows remain untouched by this corrective PR; latest-main import is preserved. PR #2 will be readied/merged only after the integrated-branch live gate passes. Pages setting/deployment remains pending.

---
## Preserved corrective-session board

# Coordination board — integrated ownership and acceptance record

## First live acceptance / native-history extension (2026-10-21 21:27 UTC)

- **Actions run [39677260400](https://github.com/karagemop466-tech/LOLHOTSPAWN4/actions/runs/39677260400) PASSED** live original-publisher collection, 39 tests, static/source/calculation checks, 28 real mobile/desktop route checks and 14 interaction/expiry checks. Tested receipts retained by bot commit `c59df75`; all **264 canonical match links** now come from the actual WP resolver. Production deploy was intentionally skipped on the preview branch; Pages still uses the historical root.
- Corrected native Polymarket competition-tail recognition for the actual `Worlds Group Stage` label (without relaxing named outcomes, full-series scope, freshness or start guards). Recalculation from this run's dated inputs yields **26 directional picks, 2 bookmaker + 6 prediction-market rows, 22 model rows (4 supported ties), 169 upcoming without a directional pick**. This is not a new HTTP refresh.
- Added an independently scoped native community-wiki `Data:`/`MatchSchedule` collector for the low-tier competitions, rather than importing the integrated synthetic game cache/seeded ratings. It requires exact names, declared BO1/3/5, explicit dates, score/winner agreement, same-season/same-format and comparable groups/opponent pools. Future/default/forfeit/DQ and disputed Solid Gaming inputs are excluded; corrections replace old page records. Non-Prime models additionally need a current exact-fixture schedule/format observation. Access restrictions stay visible with original cache dates.
- **54 tests passed locally**, including native-template, nested-game, future/pre-awarded score, group separation, alias, correction, provider-update freshness and external-start expiry regression checks. Expanded collector has not yet run live; no coverage gain is claimed for it. Existing legacy source files remain untouched; next is live validation, integration and verified-only Pages publication.

## Autonomous publication gate added (2026-10-21 21:15 UTC)

- Claimed `.github/workflows/verified-pages.yml` now implements one independent **4-hour** source refresh, 39 unit/artifact tests, full internal-link/source/calculation checks, and real Chromium browser gates before uploading **only `verified/`**. Only a tested preview receipt bot may push to this session's fixed branch; production deployment generates/publishes without pushing to main.
- Local full gate passed **28 route/viewport accessibility checks + 14 functional checks**: exact-ID/competition/status filtering, pagination, direct fixture anchors, local-only table scrolling, original source links, blank unsupported values, evidence expansion, stale-snapshot hiding, and no-JavaScript inventory preservation. Reports: `audit/d126dc4d/verified-browser{,-viewports}.json`.
- Preview is the new isolated artifact on 0.0.0.0:8080. Existing implementation files/workflows have not been edited. Fresh runner collection and actual Pages acceptance are next; no root deployment claim yet.

## Isolated implementation checkpoint (2026-10-21 21:07 UTC)

- Implemented only the claimed new `verified/**` and `verified_pipeline/**` scopes: allow-listed full Hotspawn inventory, strict Pinnacle/Polymarket full-series guards, exact identities/known times/fresh receipts, null unsupported values, static/mobile accessible UI with all views, sources and expiry hiding.
- Persisted **29 individually read official Prime League result observations** (not ratings, crowd predictions or undated aggregates). Transparent Beta/log5 small-sample estimates require two dated causal results for each exact team, preserve no-direction ties and disclose partial-history/non-calibration limits. Automatic headers with an unconfirmed season do not get fabricated season labels.
- Offline source-receipt build accounts for **264 IDs = 195 upcoming + 69 elapsed listings**, with 2 bookmaker rows, 22 model rows (4 evidence-based ties), 20 directional picks, and 175 upcoming without a directional pick. Full current external discovery is still pending the runner, not claimed complete.
- **38 unit tests pass**; generated artifact inventory/calculation/source/internal-link checks pass. First real Chromium/mobile/axe run passed **28 route/viewport checks**, 360/390/768/1280px, no JS errors/failed local requests/overflow/automated WCAG failures. This is source/calculation/UI verification, not a claim of calibrated probabilities or source coverage for unresolved fixtures.
- **Remaining at this checkpoint:** source-refresh/publish workflow and interactive browser gates, live runner receipts, integration of the newer main (PR #17), PR #2 readiness/merge, Pages configuration switch and actual verified-only deployment. No deployment acceptance yet; root still serves the other sessions' legacy site.
- Existing production files and workflows remain untouched; latest main's completion claims do not supersede independently reproducible unsupported-fill/map-scope findings.

## Isolated verified build claim (2026-10-21 20:43 UTC)

`arena/d126dc4d-lolhotspawn4` now claims **new, non-overlapping** `verified/**`, `verified_pipeline/**`, and `.github/workflows/verified-pages.yml` for a strict source-backed build and final Pages artifact integration. Existing `collector/`, `scripts/`, `data/`, `assets/`, root HTML, `docs/` and the other sessions' refresh workflows remain untouched. This avoids overwriting the still-active broad implementation claim while correcting unsupported fills in a separately testable build. Pages must serve only the verified artifact after all tests pass; no legacy/unverified public dataset will be included in that artifact. If Pages settings permissions prevent the switch, report that limitation, not a successful root deployment.

- PR #14 again updated shared production files while reports remained outstanding. Its seeded Elo ratings are not accepted without dated original result receipts and a reproducible training calculation.
- New real-browser audit of the merged UI completed 20 route/viewport checks: no JS/data-load errors, but picks/unresolved overflow to 419px on 360/390px phones and all pages have WCAG failures. Preview stopped; reports preserved under audit scope.
- Isolated original-source workflow39672234791 succeeded:11/15publisher retrievals; all four Prime League URLs403 on the runner, and RIVALS/Komplett responses are client-rendered shells. HTTP200 alone is not verified result evidence. Receipts are retained only under research scope.

## Current independent acceptance work (2026-10-21 20:38 UTC)

| Task | Status | Session / owner | Files in scope | Notes |
|---|---|---|---|---|
| Independent source/runtime/mobile/integrity audit and source-receipt collection | in progress | `arena/d126dc4d-lolhotspawn4` | `research/d126dc4d/**`, `audit/d126dc4d/**`, `.github/workflows/independent-audit.yml`, coordination records | Additive QA/source collection only; no active implementation files overwritten. |
| Corrective final integration of completed public-site work | awaiting implementation handoff | `arena/d126dc4d-lolhotspawn4` | Proposed: completed 6b `scripts/update_picks.py`, public `data/picks.json`, `docs/`, `assets/`, public HTML and update-picks workflow | Main's 6b board says done; 0a branch still has an in-progress overlapping broad claim. Handoff requested in issue #13; do not silently modify active owner scope. |

**Acceptance is not complete.** A successful Pages build or schema that requires a fabricated first-team pick is not a factual/source verification pass. Issues #7/#9/#11/#13 carry reproducible corrective requests; unsupported values must stay blank. Initial and post-merge findings are in the reserved audit/research directories.

### Merge/conflict log

- 2026-10-21 20:38 UTC: `arena-d126dc4d` merged published main (`e55e6d5`, PR #8 included). `COORDINATION.md` conflicted because PR #8 replaced earlier ownership/history. Preserved **both full records below**, without discarding other sessions' claims. Production files imported as published; not rewritten by the audit session.
- Historical “done/verified” statements below are the respective implementation sessions' reports, not independent acceptance. They are retained for provenance; the audit findings supersede unsupported assertions (e.g., no public Pinnacle price endpoint / unsupported 50/50 baselines).

## Latest implementation session record (preserved from main / PR #8)

# Coordination Board

Shared task board for parallel agent sessions working on `karagemop466-tech/LOLHOTSPAWN4`.

| Task | Status | Session / Owner | Files | Notes |
|---|---|---|---|---|
| T1: Hotspawn LoL fixture ingest (internal API `api/v1/fixtures` + SSR lobby fallback) | done | `arena/6b271c44-lolhotspawn4` | `scripts/update_picks.py`, `collector/` | Ingests all scheduled fixtures; filters incomplete/TBD brackets gracefully. |
| T2: External odds adapters (Polymarket Gamma API + OddsPapi LoL sportId 18) | done | `arena/6b271c44-lolhotspawn4` | `scripts/update_picks.py`, `collector/fetch_odds.py` | Real-money prediction markets + sharp bookmaker de-vigged median lines. |
| T3: Originated line model (Leaguepedia Cargo Elo K=32 + Bayesian shrinkage + 50/50 unresolved) | done | `arena/6b271c44-lolhotspawn4` | `scripts/update_picks.py` | Solves prompt requirement: originates lines for low-tier matches using Leaguepedia competitive history. |
| T4: Mobile-first GitHub Pages dashboard & Executive Summary with in-site pick links | done | `arena/6b271c44-lolhotspawn4` | `index.html`, `picks.html`, `assets/`, `docs/` | Mobile-first UI with dual Card View and Table View, clear pick indicators, and probability bars. |
| T5: Separate Unresolved section + Flagged for Review page + explicit limitations | done | `arena/6b271c44-lolhotspawn4` | `unresolved.html`, `flagged.html`, `methodology.html`, `docs/` | Dedicated Unresolved & Limitations analysis in Executive Summary and dedicated pages. |
| T6: Automation workflow (6-hour refresh schedule, strict schema validation, commit & deploy) | done | `arena/6b271c44-lolhotspawn4` | `.github/workflows/update-picks.yml` | 6h automated refresh pipeline; verified schema validation. |
| T7: Integration, line-by-line verification, PR to main, merge, Pages deployment confirmation | done | `arena/6b271c44-lolhotspawn4` | All files | Clean integration across branches `arena/0a18d42d` and `arena/6b271c44`. |

## Parallel Session Integration & Conflict Log (2026-10-21 ~20:30 UTC)
- Session `arena/0a18d42d-lolhotspawn4` submitted PR #4, #5, #6 creating `collector/`, `css/`, `js/`, but its initial line model left all low-tier matches blank with no picks, and its fixture validator crashed on incomplete TBD brackets.
- Session `arena/6b271c44-lolhotspawn4` resolved the core requirement: **originating lines for low-tier matches** via a Bayesian-shrunk Elo model calculated over Leaguepedia official match results (ScoreboardGames Cargo API), ensuring 100% pick coverage for all 195 open matches on Hotspawn.
- Rebased and merged `main` into `arena/6b271c44-lolhotspawn4` without discarding any session's work:
  - Preserved `collector/` and patched `fetch_hotspawn.py` to handle provisional brackets safely.
  - Deployed comprehensive mobile dashboard in `index.html`, `picks.html`, `unresolved.html`, `flagged.html`, `methodology.html`, `assets/`, and `docs/`.
  - Created automated 6-hour refresh pipeline `.github/workflows/update-picks.yml`.
  - Verified local HTTP server on `0.0.0.0:8080`: all pages, subpages, assets, and data endpoints return `200 OK` with zero broken links.

## Verified Official Sources (Checked 2026-10-21)
- **Hotspawn LoL Lobby:** https://play.hotspawn.com/lol-pickems
- **Hotspawn Main Lobby:** https://play.hotspawn.com/lobby
- **Hotspawn How It Works (pick lock 5 min pre-match):** https://play.hotspawn.com/how-it-works
- **Hotspawn Internal Fixtures API:** https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures?sport_alias=lol&status=scheduled&tenantId=1
- **Polymarket Gamma API (LoL prediction markets):** https://gamma-api.polymarket.com/events?tag_slug=league-of-legends
- **OddsPapi LoL Odds API (sportId 18, winner market 181, 100+ bookmakers incl. Pinnacle/bet365):** https://oddspapi.io/sports/esports/lol
- **Leaguepedia Cargo API (ScoreboardGames results for Elo model):** https://lol.fandom.com/api.php?action=help&modules=cargoquery
- **Leaguepedia LoL Esports Wiki:** https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki
- **Game of Legends (GOL.gg) Esports Database:** https://gol.gg/tournament/list/
- **Pinnacle Esports API Documentation:** https://github.com/pinnacleapi/pinnacleapi-documentation

## Verification Performed
1. **Schema & Pick Validation:** Validated that every match has an identified pick from `(team1, team2)`, win probabilities sum to exactly `1.000` (within 0.01 tolerance), and every row links to an official source or wiki documentation.
2. **Endpoint & Asset Integrity:** Ran local HTTP test server on `0.0.0.0:8080`. Verified that all HTML pages (`index.html`, `picks.html`, `unresolved.html`, `flagged.html`, `methodology.html`), assets (`assets/app.js`, `assets/style.css`), data files (`data/picks.json`), and `/docs/` replicas return `200 OK` with zero broken links.
3. **Multi-Model Coverage:** Verified that featured matches are priced via betting markets, intermediate matches via our originated Leaguepedia Elo model, and unrecorded amateur matches via explicit 50/50 baseline.
4. **Independence Rule:** Verified that Hotspawn crowd % is purely displayed as informational context and is not ingested as a model probability factor.

## Known Irregularities & Standing Flags (Published on Flagged page)
1. **Direct Sandbox Egress:** The local sandbox environment allows outbound traffic only to GitHub, NPM, and PyPI. Live scraping of Hotspawn, Polymarket, and Leaguepedia executes inside GitHub Actions runners (`ubuntu-latest`), which have unrestricted internet access.
2. **Waiting For Information Tier:** Many lower-tier and amateur matches on Hotspawn have tier or stage listed as "WAITING FOR INFORMATION". These matches are clearly flagged in the dataset and UI.
3. **Low-Tier Esportsbook Coverage:** Lower-tier regional leagues (e.g., PRM 3rd Division, amateur regional cups) are rarely quoted by commercial sportsbooks or Polymarket. Our pipeline originates its own line using historical Leaguepedia match results (Elo), and where no competitive history exists, assigns a 50/50 baseline with full disclosure.
4. **Hotspawn Crowd Percentage:** Hotspawn displays crowd pick percentages (e.g., "89% picked") on the lobby cards. In accordance with system instructions, crowd percentage is strictly treated as informational context and is **never** used as an indicator or input for match win probability.


## Earlier merged ownership and independent audit history (preserved)

# Shared coordination and integration record

## Current ownership (2026-10-21 UTC)

| Task | Status | Owner | File scope | Notes |
| --- | --- | --- | --- | --- |
| Published first collector/dashboard implementation | needs review | arena-0a18d42d | `collector/**`, `data/**`, `.github/workflows/refresh.yml`, root site HTML, `css/**`, `js/**`, README | PR #4 was merged by that session while independent research/audit was in progress. Preserve its files; request corrections rather than competing edits. Runtime and data-source verification are still required. |
| Earlier broad implementation claim | in progress | arena-1a78ec3b | See its remote branch board | Claim predates other sessions. Coordination split requested in issue #1; no handoff acknowledgment observed yet. |
| Additional parallel claims | in progress | arena-a8a4df4b, arena-6b271c44 | See their remote branch boards | Discovered after initial coordination. These sessions must not overwrite published/shared outputs without final integration. |
| Independent source research | done | arena-d126dc4d | `research/d126dc4d/**` | Direct official bookmaker and organizer source audit, field-level result checks, and review flags. Handoff issue #3. |
| Independent tests, source-row/link/mobile audit | in progress | arena-d126dc4d | `audit/d126dc4d/**`; coordination records only | Static auditor regression suite: 10 tests pass. External reachability and factual accuracy are expressly separate from local link presence. Proposed audit integration PR #2. |

### Active correction requests (do not edit another owner's files)

- For `arena-0a18d42d`: re-run the collector immediately. `collector/fetch_hotspawn.py` calls bare `log(...)` but imports only `common`, and no local `log` is defined in the published file. This appears to fail before any network fetch. Independent execution will confirm and be logged under the audit path. Ensure the published dataset actually exists and the first refresh/deploy succeeds.
- For implementation sessions: use the official independent fallback sources and future-result warning in `research/d126dc4d/official-source-audit.md` / issue #3. Do not use future target scores, Hotspawn scores/crowd shares, unverified aliases or manufactured 50/50 fills.
- Please coordinate final publishing ownership via issue #1 / the branch boards. GitHub issue comments and edits returned permission 403 here; issue creation and branch pushes work.

### Independent audit update (2026-10-21 20:30 UTC)

- Runtime failure confirmed: bare `log` causes `NameError` before any fetch. `data/matches.json` absent in the first published build. Source-owner fix requested in issue #7; no implementation files edited here.
- Browser audit completed all 16 combinations (4 pages × 360/390/768/1280 px). No horizontal page overflow, but landing inline JavaScript syntax error, missing dataset requests and WCAG A/AA violations found. Full failures preserved under `audit/d126dc4d/`; not a pass.
- Synthetic safety probes confirm 6/7 failures (map/undated/rematch market acceptance, academy identity conflation, cache timestamp reset and false-fresh no-cache failure). These are synthetic regression inputs, not real match allegations.
- Real browser QA uses pinned npm tools and bundled Chromium under excluded `.arena/`; binaries are not committed. Preview was stopped after initial audit so a broken preview is not left running.
- Additional PR #8 proposes another implementation with 50/50 no-evidence baselines. Such baselines cannot satisfy the strict blank/unverified requirement; request removal or quarantine before final integration.
- Issue #3 carries verified official lower-tier result and Thunderpick fallback sources. Issue comment/edit APIs return permission 403; branch records and new issues are the available coordination channels.

### Conflict-resolution log

- 2026-10-21: PR #4 independently merged its board and first implementation to main. Bringing main into the audit branch produced an add/add conflict only in `COORDINATION.md`; no implementation file conflict occurred. A rebase was stopped/aborted to avoid rewriting already-pushed session history, then a merge was used. Both complete prior boards are preserved below (historical claims in those records do not override the current table). No other session's implementation was discarded. Only the fixed Arena branch is used.

## Preserved d126dc4d board (historical)

<details><summary>Research/audit session claim and activity history</summary>

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

</details>

## Preserved published implementation board (historical)

<details><summary>0a18d42d claim, source findings, and implementation history</summary>

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

</details>

### Publisher-price correction / post-merge handoff (2026-10-21 20:36 UTC)

Directly verified Pinnacle paired-price endpoints and9parent matchups (research snapshot only); issue#11 corrects the first implementation's absence claim. Post-merge issue#13 reports actual PR8 map1 evidence, unsupported50/50 fills, competing workflows, source-receipt gaps and replacement of ownership history. No production files edited. Historical stale scheduled rows explain264backend IDs versus195future IDs; expose that difference explicitly, not as a claim of264active matches.


---
## Preserved incoming main integration board (e814cde)

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
