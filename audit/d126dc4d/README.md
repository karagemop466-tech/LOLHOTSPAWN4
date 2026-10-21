# Independent audit tools and findings

Owner: `arena-d126dc4d`. These files are separate from every implementation session's scope. They do not alter the production collector or dashboard.

## What was tested

- `check_static_site.py`: local HTML/assets/fragments, repository-base URLs, document language/title/viewport/heading and optional per-table-row original-publisher link presence. **It does not verify the contents or availability of external pages.** Ten regression tests exercise the auditor itself.
- `check_mobile.mjs`: real Chromium rendering at 360, 390, 768 and 1280 CSS pixels; JavaScript errors, same-site failed data/assets, horizontal overflow, executive-summary picks link, and axe WCAG A/AA smoke tests. Automated accessibility testing is not a substitute for human assistive-technology testing.
- `probe_pipeline_safety.py`: synthetic adversarial probes of the first published collector (market type/date/identity and cache evidence age). **Its test values are synthetic, never source data or real picks.** This probe adapter must be updated if the legacy `collector/` pipeline is replaced.
- `serve_preview.py`: simple preview server bound to `0.0.0.0`, with hidden paths and directory listings blocked. No credentials or external services are needed.

## Initial published-build findings (historical, not final acceptance)

Audited first implementation inherited from PR #4, around 2026-10-21 20:26–20:30 UTC. These reports intentionally preserve failures so that “site builds” cannot be mistaken for “working picks dashboard.”

| Check | Initial outcome | Evidence |
| --- | --- | --- |
| Collector execution | Fails before fetching: `NameError: name 'log' is not defined` at `collector/fetch_hotspawn.py:34`; same bare log calls appear in `fetch_odds.py` | Reproduced locally without network; correction request in [issue #7](https://github.com/karagemop466-tech/LOLHOTSPAWN4/issues/7) |
| Dataset | `data/matches.json` absent; browser gets 404 | `browser-audit-initial.json` |
| Landing page JavaScript | `Invalid or unexpected token` from malformed inline script; a separate bare `$` call is also not exported by `js/app.js` | `browser-audit-initial.json`; direct source inspection |
| Local file/fragment targets | No missing static file/fragment targets found | `static-audit-initial.json` (excludes dynamic data fetch, which browser audit checks) |
| Static data-row source links | 14/21 rows lack a link to the auditor's recognized original-publisher hosts; hosts can be extended for legitimate publishers | `static-audit-initial.json`; presence-only, not factual accuracy |
| Browser / responsive / accessibility | All 16 route/viewport checks completed. No page-wide horizontal overflow; JavaScript/data and accessibility failures remain | `browser-audit-initial.json` |
| Synthetic pipeline safety | Six of seven probes fail: map market accepted as series, undated market accepted, two-day-later same-pair event accepted, academy/main identity conflation, cached evidence time overwritten, failed source with no cache marked not stale | `pipeline-safety-initial.json` |

Accessibility issues in the initial build include white/gold branding on a pale header, inline links distinguishable only by color, buttons inside `role=tablist` without tab roles, and unfocusable horizontally scrolling table containers. Publish updated reports after fixes; do not claim the initial build passes.

## Re-run

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s audit/d126dc4d -p 'test_*.py' -v
python audit/d126dc4d/check_static_site.py . --check-row-sources \
  --report audit/d126dc4d/static-audit-final.json
python audit/d126dc4d/probe_pipeline_safety.py audit/d126dc4d/pipeline-safety-final.json
```

For real-browser QA, tools/binaries stay in the ignored/excluded `.arena/` directory, not Git:

```sh
npm install --prefix .arena/audit-tools --no-fund --no-audit \
  playwright-core@1.64.1 @sparticuz/chromium@153.0.0 axe-core@4.14.0
# Run the server using the platform process tool (not a background bash job):
# python audit/d126dc4d/serve_preview.py --port 8080 --directory .
node audit/d126dc4d/check_mobile.mjs --url http://127.0.0.1:8080/ \
  --out audit/d126dc4d/browser-audit-final.json --expect-data --screenshots
```

The localhost URL above is **inside the audit tool only**. Browser-facing site code must continue to use relative same-site URLs. The preview itself binds to all interfaces so the platform proxy can reach it.

## Independent publisher checks

Original-publisher research, directly checked quotes/results and specific provenance limitations are in `research/d126dc4d/official-source-audit.md` and `review-findings.json`. Search snippets, another session's claims and a source URL's mere presence are not verification.
