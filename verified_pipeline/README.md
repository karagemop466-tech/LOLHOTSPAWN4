# Verified-only LoL publisher

This namespace and `verified/` are an isolated corrective implementation. It does
**not** import the legacy `data/picks.json`, seed ratings, Hotspawn scores/crowd
statistics, or the other sessions' probability outputs. Existing work remains in
Git for provenance; the Pages artifact includes **only `verified/`**.

## Contract

- Every unique listed LoL fixture ID survives, including elapsed/locked or
  provisional listings. The summary reconciles those states explicitly.
- Hotspawn is an inventory/schedule source only, through an allow-list firewall.
  Canonical match URLs come from its official WordPress permalink resolver;
  unresolved canonical links use the actual inventory endpoint, never guessed
  match slugs.
- Public Pinnacle parent LoL matchups + open period-0 `s;0;m` moneylines are
  independently joined and de-vigged. Public Polymarket event discovery is
  paginated; only full-series `moneyline` / `Match Winner` is accepted. Game 1,
  futures, handicaps, live/closed quotes, unsafe source URLs and fuzzy aliases
  cannot become series probabilities.
- Exact teams, a unique inventory match, competition context, known nearby start
  times, and an observation no more than eight hours old are mandatory. When the provider
  supplies an update timestamp, that must also be fresh. Any
  nonidentical start is a visible review flag, not silently rewritten. Team order
  reversals and raw-price arithmetic are reproducible.
- Uncovered rows may use the disclosed, uncalibrated Beta(2,2)/log5/shrink-10
  model over partial, dated organizer and native community-wiki series results.
  Both exact teams need two causal results in the same independently confirmed
  competition, season, series format and comparable observed opponent pool. No history means nulls, not a neutral fill. Ties have no forced pick.
- `history.json` contains individually read official result observations, **not
  seeded ratings**. Local organizer dates retain an unknown timezone. Eligibility
  uses a conservative next-day-plus-20h bound, not an invented UTC result time.
  New organizer observations whose season cannot be established stay ineligible.
  Recognized native community-wiki MatchSchedule pages are retried each run;
  corrections replace old page observations. Non-Prime competitions require a
  fresh exact-team scheduled format. Team codes are not guessed, administrative
  outcomes are excluded, and duplicate reports cannot inflate sample counts.
  No synthetic per-game timestamps or league-average opponents are accepted.
- Source access restrictions are never bypassed. HTTP 200 is not a usable result
  table. Failures preserve actual last-good observation dates, disclose cache use,
  and eventually blank stale probabilities. A missing inventory is a hard failure.

## Run and test

Python 3.11+ and Node 22; no production Python packages or API secrets required.

```sh
# Normally run on a GitHub-hosted runner; local publisher egress is restricted.
python -m verified_pipeline.refresh
python -m unittest discover -s verified_pipeline/tests -p 'test_*.py' -v
python -m verified_pipeline.check

# Reproducible local build from original, dated audit receipts; timestamps do NOT
# become newly fetched. This is not a substitute for the live runner refresh.
python -m verified_pipeline.refresh --offline \
  --bootstrap-receipts research/d126dc4d/receipts

# Isolated browser tools: do not commit node_modules or downloaded Chromium.
npm install --prefix .arena/audit-tools --no-fund --no-audit \
  playwright-core@1.64.1 @sparticuz/chromium@153.0.0 axe-core@4.14.0
node verified_pipeline/browser_test.mjs --tools .arena/audit-tools \
  --out audit/d126dc4d/verified-browser.json
```

`browser_test.mjs` starts and closes its own test server. It runs 28 real
Chromium viewport/WCAG smoke checks plus functional checks for both views,
filtering, pagination, direct fixture fragments, source links, blank values,
evidence expansion, expiry hiding and no-JavaScript inventory preservation.
The UI uses relative assets only and requires no browser-to-localhost API.

## Autonomy and publication

`.github/workflows/verified-pages.yml` refreshes at `17 */4 * * *`, tests the
entire generated artifact, and uploads only `verified/`. The production job
publishes that artifact on `main` using Pages Actions. It never pushes to `main`
or another session's branch. A preview-only bot may retain tested receipts on
`arena/d126dc4d-lolhotspawn4`; it pulls with `--rebase=merges` before that push.
Source caches persist between refreshes without falsifying their dates.

The repository's Pages build type must be `workflow`, not legacy main/root.
Deployment is not complete until the actual production run succeeds and the
public `data/deployment.json` identifies `artifact: verified-only`. Source
restrictions, limited history and any settings-permission blocker must be
reported, never disguised as full price coverage or successful publication.

## Important limits

These are source-backed calculations, **not calibrated winning chances**.
Public bookmaker coverage is not exhaustive; organizer bot restrictions and
unconfirmed identities leave many amateur matches unresolved. The partial
history archive can be selection-biased and does not adjust for strength of
schedule, roster, draft or patch. These limits are visible in the executive
summary, every model card, methodology, and Flagged for Review.
