# Independent official-source audit

Owner: `arena-d126dc4d`. Observed on **2026-10-21 UTC** using direct publisher-page retrieval (`fetch_page`), not search snippets. This is an independent research handoff, **not a live odds feed**. The observation date is our retrieval date, not a claimed provider update time. Exact provider quote timestamps were not exposed and remain unconfirmed.

## Important integration requests

1. Try direct bookmakers first, then esportsbook lines/prediction markets, then a reproducible model from independent organizer results. Only invoke the lower-tier result fallback for matches still lacking acceptable market evidence.
2. Do not substitute Hotspawn community pick shares, Hotspawn historical results, an invented 50/50 prior, or a different market (map winner/outright) for evidence of a series winner.
3. Preserve every current Hotspawn LoL fixture even if its probability is unresolved. Keep explicit discovery/coverage status separate from pick-resolution status.
4. Organizer result pages can already contain scores for future scheduled matches. **Never train on a result whose event date is in the future or on the target match itself**, even if the organizer displays a score. Quarantine status conflicts and publish them for review.
5. Official organizer pages below make useful lower-tier data available. Do not conclude that all minor leagues must be blank merely because Polymarket does not list them.

## Directly checked providers

| Publisher / category | Direct official source | What was actually observed | Use / limitation |
| --- | --- | --- | --- |
| Hotspawn LoL inventory | <https://play.hotspawn.com/lol-pickems> | Dedicated League of Legends lobby; tier/tournament filters display 264 entries in this retrieval. The separate weekly banner says 138 matches. Cards include dated teams, tournament, points and match links. | This is inventory evidence only. The displayed filter count is not, by itself, proof that 264 unique active fixtures have been ingested. Do not use crowd shares for probabilities. |
| Hotspawn public route schema | <https://www.hotspawn.com/wp-json/pickem/v1> | Public read routes include fixture-by-ID and `fixtures`. | Inspect public GET requests only; no account or write endpoints are needed. |
| Hotspawn permalink resolver | <https://www.hotspawn.com/wp-json/pickem/v1/fixtures?ids=1081205,1071214> | `success:true`; exact match-card permalinks returned for the requested IDs. | Useful authoritative URL mapping, **not** an inventory or odds feed. No-ID requests return a `missing_ids` error. |
| Hotspawn fixture route schema | <https://www.hotspawn.com/wp-json/fixtures/v1> | Public GET `fixtures/v1/get`; other routes are writes. The GET requires `external_id`. | Do not call update/create/receive routes. |
| Hotspawn frontend fixture service | <https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures> | Very large JSON response begins with historical/test fixtures, CS2 and football, and includes `sport_alias`, `scheduled_start_time`, `lock_time`, teams and scores. | Must filter game/status and reconcile current LoL lobby IDs. Entire feed is not the current lobby. Historical Hotspawn scores must not drive probabilities. |
| Pinnacle public esports matchups | <https://guest.api.arcadia.pinnacle.com/0.1/sports/12/matchups> | Public JSON endpoint retrievable; includes mixed esports, parent/child matchups and special markets. | A parent matchup and exact full-series moneyline must be identified; do not accept yes/no specials or map lines as series prices. This audit has not verified a LoL quote from this endpoint. |
| Thunderpick LoL category | <https://thunderpick.io/esports/league-of-legends> | Accessible official sportsbook page links Worlds 2026, EMEA Masters 2026 Summer and a European Circuit event. | Actual non-Polymarket coverage exists. Match prices must be re-fetched, time-limited and matched by participants/date/market. No account or wagering is required. |
| Thunderpick exact EMEA series | <https://thunderpick.io/esports/league-of-legends/emea-masters-2026-summer/10747/solary-vs-galions/2829674> | **Main → Match Winner: Solary -122 / Galions -114**, American odds. BO5; October 22. Same page has separate Map 1–5 tabs. | Direct bookmaker evidence for Hotspawn 1081205 (whose team order is reversed). Source also renders a generic “Live” label despite the future date; validate market/fixture state before accepting automatically. These are snapshot quotes, not guaranteed executable odds. |
| GG.bet LoL | <https://gg.bet/en/esports/league-of-legends> | Explicit “This internet site is not accepting visitors from your region.” | **Access restricted**, not “no market.” No odds accepted. Do not bypass the restriction. |
| bwin LoL | <https://www.bwin.com/en/sports/league-of-legends-106> | Extracted page includes market headers, login/captcha/UI and US-location notice, but no usable paired match prices in this direct retrieval. | **No usable extracted line**, not proof of absent markets. Search snippets were not accepted as prices. |
| Prime League division 3 | <https://www.primeleague.gg/en/liga3> | Current Fall 26/27 standings, four groups, completed score links and upcoming match links; individual official match pages include date, teams, series result and Bo3. | Strong official-organizer result source for PRM low-tier model fallback. Do not mistake page “Predictions” crowd percentages for statistics or odds. Audit identity aliases and deduplicate widgets. |
| Prime League division 2 | <https://www.primeleague.gg/en/liga2> | Current Fall 26/27 standings, completed score links and upcoming match links for division 2. | Same requirements. Series count `R` and league points `P` are different; points are not win/loss counts. |
| Prime League season | <https://www.primeleague.gg/en/leagues/prm/3227-fall-split-202627> | Official current season and group links; rules explain match rescheduling and lineup checks. | Direct results, not assumed default dates, should determine historical cutoff. |
| Komplettligaen standings | <https://www.komplettligaen.no/lol/tabeller> | Official Division 1 table with played/won/drawn/lost for twelve teams. Solid Gaming has 0 played / 0 won / 0 lost in this snapshot. | Official result source for minor-league fallback; **zero history is not an evidence-backed pick**. Current standings may incorporate prematurely entered scores; prefer dated historical result pages. |
| Komplettligaen result list | <https://www.komplettligaen.no/lol/resultater?season=13909&division=18859> | This exact URL is linked from an official match page as Division 1 results. | Discovery lead from an official link; the list itself was not independently retrieved in the initial audit. Fetch/validate before using. |
| RIVALS organizer | <https://www.rivalsleague.gg/lol> | Official League of Legends competition page and season/team links. | Organizer source rather than community odds. Distinguish division, group, season and country suffixes. |
| RIVALS team directory | <https://www.rivalsleague.gg/lol/teams> | Official Season 2 directory displays 146 teams, with UUID team links and division/group columns. | Contains multiple divisions and similarly named teams; never use fuzzy identity alone. |
| RIVALS result example | <https://www.rivalsleague.gg/lol/team/2e5c8bdc-1254-4bb7-a44c-168d1c8830f0> | Bardicted to U official Season 2 page displays 4W/0L and direct links to four completed series. | Candidate identity for Hotspawn “B2U”; alias is **not yet verified** in this audit. B2U Old Timers is a separate official team and must not be merged. |

## Row-level official-result spot checks

These are observed publisher values, not forecasts. Times without an explicit zone remain unconverted. A future score is deliberately excluded from model evidence.

| Official event | Observed date (publisher display) | Teams / result | Direct official source | Field verification / exclusions |
| --- | --- | --- | --- | --- |
| Prime League 601780 | 2026-10-07 13:00; zone unconfirmed | MT1 Vision **1–2** Babos Gaming Academy; best of three | <https://www.primeleague.gg/en/matches/601780-mt1-vision-vs-babos-gaming-academy> | Result, pairing, displayed date and series format directly checked. UTC time not inferred. |
| Prime League 601784 | 2026-10-11 13:00; zone unconfirmed | Glacial Guardians **1–2** BlackDivision; best of three | <https://www.primeleague.gg/en/matches/601784-glacial-guardians-vs-blackdivision> | Result, pairing, displayed date and series format directly checked. UTC time not inferred. |
| RIVALS 08083633-9115-4db9-95de-19940a62b738 | “lör 26 sep. - 21:38 CEST”; official page labels RIVALS LOL s2 | DMG SE **0–2** Bardicted to U; BO3 | <https://www.rivalsleague.gg/lol/match/08083633-9115-4db9-95de-19940a62b738> | Pairing, result, season label, day/month and explicit zone checked. Year not printed in the retrieved match header; do not silently infer it without season metadata. |
| Komplettligaen 258067 / Hotspawn 1071212 | **23 Oct 2026**, a future date at the 21 Oct audit | Organizer displays Rich Gang **2–0** Phenti XD; Hotspawn still lists Rich Gang vs Phenti as upcoming | <https://www.komplettligaen.no/lol/kamp/258067> · <https://www.hotspawn.com/matches/rich-gang-vs-phenti-komplettligaen-2026-autumn-1071212> | **Flagged status/timing conflict**. Identity “Phenti” vs “Phenti XD” requires confirmation. Do not include the future displayed result in training or claim the match is settled. |

## Fallback design supported by this research

- Market selection: only accept a fresh two-sided full-series winner market for the identical fixture; remove overround from each book before combining books. Keep prediction-market shares separate from decimal bookmaker odds. Reversed team ordering must be explicitly handled.
- Result fallback: collect dated completed results from **independent organizer** match pages, not from Hotspawn. Limit to the correct game, season and competition; reject future/target results and ambiguous team aliases. Require evidence for both participants. A small-sample model should be labelled **model estimate / low confidence**, with source-linked historical inputs, documented assumptions and reproducible calculation.
- Example model families: series-level Elo with shrinkage, or a shrinkage-adjusted Bradley–Terry fit. These are proposed analytical choices, not verified factual probabilities. No numeric model estimate was fabricated in this audit.
- Calibration: distinguish a model output from empirical accuracy. Do not claim predictive validation without a held-out chronological backtest and sample counts. Future fall fixtures may change roster/form before start.
- Unresolved reasons should be specific: provider access restriction; no matching accepted series market after attempted sources; unverified participant identity; insufficient independent history; source status conflict; stale evidence; inventory retrieval failure. “No market exists” is too strong unless actually established.

## Not accepted as evidence

- Search snippets, other repositories' dashboards/PR claims, or another agent's unverified report.
- Crowd-pick percentages on Hotspawn **or** Prime League prediction widgets.
- A bookmaker logo on a third-party page without the exact contemporaneous two-way line and attribution.
- Outright Worlds winner prices used as if they were a match moneyline.
- A raw API response without matching identity, event time, full-series market scope and freshness.
- A future or target-series score, even if present on an official organizer page.

## Scope / access limitations

The sandbox's direct outbound access is limited to GitHub/package hosts. Public publisher pages were checked with the provided page-retrieval tool; a deployed refresh runner must independently retrieve and validate its own source responses. No claim is made that every provider URL is accessible from every region or at every scheduled refresh. No geographic controls, authentication or paywalls were bypassed.
