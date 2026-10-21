# LoL Match Brief — source-backed picks, honest gaps

**Dashboard:** <https://karagemop466-tech.github.io/LOLHOTSPAWN4/>

A mobile-first GitHub Pages dashboard for the complete listed League of Legends
inventory on [Hotspawn](https://play.hotspawn.com/lobby). Hotspawn establishes
fixture identity and schedule **only**; its crowd percentages, scores and history
never enter probability calculations.

## Production publisher

The corrective publisher is **`verified_pipeline/` → `verified/`**. Its workflow,
[Verified LoL refresh and Pages](.github/workflows/verified-pages.yml), refreshes
at **`17 */4 * * *` (UTC)** and deploys only that tested directory using Pages
Actions. Schedules are best-effort GitHub schedules, not an availability SLA.
The repository root, seed ratings and earlier probability outputs are **not**
part of the Pages artifact. Other sessions' implementations remain in Git;
their prior publication records are preserved in [COORDINATION.md](COORDINATION.md).

### Evidence policy

1. **All listed fixture IDs are retained**, including stale/past “scheduled”
   rows. Inventory, upcoming, elapsed, supported and unresolved counts reconcile.
   Official inventory links appear on every card/table row; canonical match links
   are used when confirmed by the WordPress resolver.
2. **Bookmaker first:** public Pinnacle parent non-live LoL matchups and open
   period-0 full-series moneylines, joined by ID and de-vigged transparently.
3. **Prediction market second:** active/open Polymarket **Match Winner**
   moneylines with two exact team outcomes. Game 1, handicaps and futures cannot
   masquerade as a match-winner probability.
4. **Independent fallback:** a disclosed, uncalibrated Beta(2,2)/log5/shrink-10
   model over dated organizer/native community-wiki series observations. Both
   teams require causal same-season, same-format records in a comparable pool.
   No seeded ratings, synthetic per-game dates or league-average opponents.
5. **No supported input → both probabilities and the pick stay blank.** A
   supported equal estimate has no arbitrary team-A pick. Access restrictions,
   schedule/identity conflicts, uncertainty and incomplete research are visible
   in Unresolved, Flagged for Review and Method & Sources.

Exact identities, unique matching, source scope, explicit start times and
freshness are mandatory. Nonidentical starts remain flagged. Every accepted
calculation, raw price, order reversal, model input, source and timestamp is
inspectable. These are price implications/model estimates, **not calibrated
winning chances or guaranteed profitable picks**.

## Dashboard sections

The overview links to all matches, market-backed lines, independent history
models, unresolved cases, methodology/source health, and Flagged for Review.
Cards are phone-first; the optional table scrolls inside its own region. Search,
competition/status filters, pagination, direct fixture anchors and evidence
expansion work without any browser-to-localhost or external API dependency.
All inventory and source links remain in the static HTML without JavaScript;
JavaScript additionally hides expired snapshot probabilities/picks.

## Run and validate

No production Python packages, paid API keys or manual refresh input required.
Source restrictions may leave rows unresolved; they are never bypassed.

```sh
python -m verified_pipeline.refresh
python -m unittest discover -s verified_pipeline/tests -v
python -m verified_pipeline.check

npm install --prefix .arena/audit-tools --no-fund --no-audit \
  playwright-core@1.64.1 @sparticuz/chromium@153.0.0 axe-core@4.14.0
node verified_pipeline/browser_test.mjs --tools .arena/audit-tools \
  --out audit/d126dc4d/verified-browser.json
```

The gate includes **57 unit/artifact tests**, full inventory/source/calculation
and internal-link checks, **28 Chromium route/viewport/accessibility checks** at
360/390/768/1280 pixels, and **14 functional checks** including expiry and no-JS
inventory preservation. All must pass before Pages artifact upload/deployment.
A failed run cannot replace the last successful site. Caches retain their actual
observation dates; stale/unconfirmed values are not relabeled as freshly fetched.

For dated offline reproduction, cache semantics, source restrictions and model
limitations, see [the publisher guide](verified_pipeline/README.md).

## Deployment evidence

The public [`data/deployment.json`](https://karagemop466-tech.github.io/LOLHOTSPAWN4/data/deployment.json)
must identify **`artifact: "verified-only"`**, the generating commit/run and
reconciled summary. CI reports are attached to the workflow run. PR, production
run, public-site acceptance and historical implementation audits are recorded in
[COORDINATION.md](COORDINATION.md); a preview success alone is not a production
deployment claim.
