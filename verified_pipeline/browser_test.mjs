#!/usr/bin/env node
/** Real Chromium + axe + interactive expiry/filter/link acceptance gate.
 * npm install --prefix .arena/audit-tools --no-fund --no-audit \
 *   playwright-core@1.64.1 @sparticuz/chromium@153.0.0 axe-core@4.14.0
 * node verified_pipeline/browser_test.mjs --tools .arena/audit-tools \
 *   --out audit/d126dc4d/verified-browser.json
 * With no --url this creates a temporary, bounded test server and closes it.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';

const args = process.argv.slice(2);
const value = (flag, fallback) => {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : fallback;
};
const tools = path.resolve(value('--tools', '.arena/audit-tools'));
const out = path.resolve(value('--out', 'audit/d126dc4d/verified-browser.json'));
const root = path.resolve('verified');
const routes = 'index.html,picks.html,featured.html,fallback.html,unresolved.html,flagged.html,methodology.html';
let server;
let base = value('--url', '');
if (!base) {
  const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
  server = http.createServer((request, response) => {
    try {
      const requestPath = decodeURIComponent(new URL(request.url, 'http://test.invalid').pathname);
      const target = path.resolve(root, '.' + (requestPath.endsWith('/') ? requestPath + 'index.html' : requestPath));
      if (!target.startsWith(root + path.sep)) { response.writeHead(403); response.end(); return; }
      const body = fs.readFileSync(target);
      response.writeHead(200, { 'Content-Type': mime[path.extname(target)] || 'application/octet-stream' });
      response.end(body);
    } catch { response.writeHead(404); response.end('Not found'); }
  });
  await new Promise((resolve) => server.listen(0, '0.0.0.0', resolve));
  base = `http://127.0.0.1:${server.address().port}/`;
}
const report = { checked_at: new Date().toISOString(), base_url: base, tests: [], failures: [], publisher_accuracy_guaranteed: false };
const check = async (name, fn) => {
  try { const detail = await fn(); report.tests.push({ name, passed: true, detail }); }
  catch (error) { const issue = { name, passed: false, error: String(error.stack || error) }; report.tests.push(issue); report.failures.push(issue); }
};
let browser;
try {
  const data = await (await fetch(new URL('data/matches.json', base), { cache: 'no-store' })).json();
  const expectedRun = value('--expected-run', '');
  if (expectedRun) assert.equal(String(data.build?.run_id), String(expectedRun), 'Public JSON is not the expected deployed run');
  // The static server needs its Node event loop. Spawn asynchronously rather
  // than blocking it while the audit browser requests the site.
  const { spawn } = await import('node:child_process');
  const viewportOut = out.replace(/\.json$/, '-viewports.json');
  const child = spawn(process.execPath, ['audit/d126dc4d/check_mobile.mjs', '--url', base,
    '--pages', routes, '--out', viewportOut, '--tools', tools, '--expect-data', '--generated-at', data.generated_at], { stdio: 'inherit' });
  const code = await new Promise((resolve) => child.on('exit', resolve));
  const viewports = JSON.parse(fs.readFileSync(viewportOut, 'utf8'));
  report.viewport_checks = viewports.viewports.length;
  report.viewport_report = path.basename(viewportOut);
  if (code !== 0 || !viewports.passed) report.failures.push({ name: 'Responsive / axe checks', error: viewports.failures });

  const require = createRequire(path.join(tools, 'package.json'));
  const mod = require('@sparticuz/chromium');
  const chromium = mod.default || mod;
  const { chromium: playwright } = require('playwright-core');
  const libs = await mod.inflate(path.resolve(path.dirname(require.resolve('@sparticuz/chromium')), '../bin/al2023.tar.br'));
  browser = await playwright.launch({ executablePath: await chromium.executablePath(),
    args: chromium.args.filter((arg) => arg !== '--single-process'), headless: true,
    env: { ...process.env, LD_LIBRARY_PATH: path.join(libs, 'lib') + ':' + (process.env.LD_LIBRARY_PATH || '') } });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(new URL('picks.html', base).href, { waitUntil: 'networkidle' });
  await check('Every inventory fixture exists in static card and table representations', async () => {
    assert.equal(await page.locator('#match-cards > article').count(), data.matches.length);
    assert.equal(await page.locator('#match-table tbody > tr').count(), data.matches.length);
    assert.equal(await page.locator('body').getAttribute('data-generated-at'), data.generated_at);
    const rendered = await page.locator('#match-cards > article').evaluateAll((items) => items.map((r) => ({
      id: r.dataset.matchId, invalidated: r.dataset.invalidated === 'true',
      probabilities: [...r.querySelectorAll('.current-probability')].map((p) => p.textContent)
    })));
    const byId = new Map(data.matches.map((r) => [r.id, r]));
    for (const row of rendered) {
      const expected = byId.get(row.id);
      assert.ok(expected, 'Unexpected fixture ' + row.id);
      for (const [index, key] of ['probability_a', 'probability_b'].entries()) {
        if (expected[key] === null || row.invalidated) assert.equal(row.probabilities[index], '—');
        else assert.ok(Math.abs(parseFloat(row.probabilities[index]) - expected[key] * 100) <= 0.051, 'Rendered probability differs from snapshot: ' + row.id);
      }
    }
    return { fixtures: data.matches.length };
  });
  await check('Each rendered card and table row has an original HTTPS source', async () => {
    const missing = await page.locator('[data-match-id]').evaluateAll((rows) => rows.filter((r) => !r.querySelector('a[href^="https://"]')).map((r) => r.dataset.matchId));
    assert.deepEqual(missing, []);
  });
  await check('Fixture ID search is functional and precise', async () => {
    const match = data.matches[0];
    await page.getByLabel('Find a team, competition or fixture ID').fill(match.id);
    assert.equal(await page.locator('#match-cards > article:not([hidden])').count(), 1);
    assert.equal(await page.locator('#match-cards > article:not([hidden])').getAttribute('data-match-id'), match.id);
    assert.match(await page.locator('#result-count').innerText(), /of 1 matches/);
  });
  await check('Empty search has a readable no-results state', async () => {
    await page.getByLabel('Find a team, competition or fixture ID').fill('__definitely_no_such_fixture__');
    assert.equal(await page.locator('#match-cards > article:not([hidden])').count(), 0);
    assert.equal(await page.locator('#no-results').isVisible(), true);
  });
  await check('Competition filter counts reconcile to dataset', async () => {
    await page.getByLabel('Find a team, competition or fixture ID').fill('');
    const competition = data.matches[0].competition;
    await page.getByLabel('Competition', { exact: true }).selectOption(competition);
    const count = data.matches.filter((r) => r.competition === competition).length;
    assert.match(await page.locator('#result-count').innerText(), new RegExp(`of ${count} matches`));
    const values = await page.locator('#match-cards > article:not([hidden])').evaluateAll((items) => items.map((r) => r.dataset.competition));
    assert.ok(values.every((v) => v === competition));
  });
  await check('Elapsed listings are separately filterable and have blank prematch values', async () => {
    await page.getByLabel('Competition', { exact: true }).selectOption('');
    await page.getByLabel('Listing status').selectOption('elapsed');
    assert.match(await page.locator('#result-count').innerText(), new RegExp(`of ${data.summary.elapsed} matches`));
    const values = await page.locator('#match-cards > article:not([hidden]) .current-probability').allTextContents();
    assert.ok(values.every((v) => v === '—'));
  });
  await check('Pagination reaches additional fixtures without losing source links', async () => {
    await page.getByLabel('Listing status').selectOption('');
    const first = await page.locator('#match-cards > article:not([hidden])').first().getAttribute('data-match-id');
    if (data.matches.length > 24) {
      await page.getByRole('button', { name: 'Next →', exact: true }).click();
      const second = await page.locator('#match-cards > article:not([hidden])').first().getAttribute('data-match-id');
      assert.notEqual(first, second);
      assert.match(await page.locator('#page-count').innerText(), /Page 2 of/);
    }
  });
  await check('A direct fixture fragment reveals a fixture on a later page', async () => {
    const target = data.matches[data.matches.length - 1].id;
    await page.goto(new URL('picks.html#match-' + target, base).href, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('#match-' + target).isVisible(), true);
  });
  await check('Mobile table switches correctly and scrolls locally, not the entire page', async () => {
    await page.getByRole('button', { name: 'Table', exact: true }).click();
    assert.equal(await page.locator('#match-table').isVisible(), true);
    assert.equal(await page.getByRole('button', { name: 'Table', exact: true }).getAttribute('aria-pressed'), 'true');
    const sizes = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, width: innerWidth,
      table: document.getElementById('match-table').scrollWidth, region: document.getElementById('match-table').clientWidth }));
    assert.ok(sizes.page <= sizes.width + 1, JSON.stringify(sizes));
    assert.ok(sizes.table > sizes.region);
    await page.addScriptTag({ path: require.resolve('axe-core/axe.min.js') });
    const violations = await page.evaluate(async () => (await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } })).violations.map((v) => v.id));
    assert.deepEqual(violations, []);
  });
  await check('Unconfirmed probabilities render as dashes, never neutral fills', async () => {
    const row = data.matches.find((r) => r.method === 'unresolved');
    assert.ok(row);
    await page.goto(new URL('picks.html#match-' + row.id, base).href, { waitUntil: 'networkidle' });
    const values = await page.locator('#match-' + row.id + ' .current-probability').allTextContents();
    assert.deepEqual(values, ['—', '—']);
    assert.equal(await page.locator('#match-' + row.id + ' .prob-bar').count(), 0);
  });
  await check('Evidence expands to the original sources and review notes', async () => {
    const row = data.matches.find((r) => r.evidence.length || r.model);
    if (!row) return 'No currently supported line/model; no placeholders used';
    await page.goto(new URL('picks.html#match-' + row.id, base).href, { waitUntil: 'networkidle' });
    await page.locator('#match-' + row.id + ' summary').click();
    assert.equal(await page.locator('#match-' + row.id + ' details').getAttribute('open'), '');
    assert.ok(await page.locator('#match-' + row.id + ' details a[href^="https://"]').count() >= 1);
  });
  await check('No interactive JavaScript errors', async () => assert.deepEqual(errors, []));
  await context.close();

  await check('Expired snapshot hides probabilities and picks in the browser', async () => {
    const stale = await browser.newContext({ viewport: { width: 360, height: 800 } });
    await stale.addInitScript(({ time }) => { Date.now = () => time; }, { time: Date.parse(data.inventory_observed_at) + 9 * 60 * 60 * 1000 });
    const p = await stale.newPage();
    await p.goto(new URL('picks.html', base).href, { waitUntil: 'networkidle' });
    assert.equal(await p.locator('#freshness-warning').isVisible(), true);
    const values = await p.locator('[data-has-probability="true"] .current-probability').allTextContents();
    assert.ok(values.every((v) => v === '—'));
    const picks = await p.locator('[data-has-probability="true"] .current-pick').allTextContents();
    assert.ok(picks.every((v) => v.includes('no current pick')));
    await stale.close();
    return { invalidated_probability_fields: values.length };
  });
  await check('No-JavaScript view retains all inventory rows and source evidence', async () => {
    const plain = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
    const p = await plain.newPage();
    await p.goto(new URL('picks.html', base).href, { waitUntil: 'networkidle' });
    assert.equal(await p.locator('#match-cards > article').count(), data.matches.length);
    assert.equal(await p.locator('#match-cards > article:not([hidden])').count(), data.matches.length);
    assert.equal(await p.locator('noscript').isVisible(), true);
    const missing = await p.locator('#match-cards > article').evaluateAll((items) => items.filter((r) => !r.querySelector('a[href^="https://"]')).length);
    assert.equal(missing, 0);
    await plain.close();
  });
} catch (error) {
  report.failures.push({ name: 'Test infrastructure', error: String(error.stack || error) });
} finally {
  if (browser) await browser.close();
  if (server) await new Promise((resolve) => server.close(resolve));
  report.passed = report.failures.length === 0;
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ passed: report.passed, viewport_checks: report.viewport_checks,
    functional_checks: report.tests.length, failures: report.failures, report: out }, null, 2));
  if (!report.passed) process.exitCode = 1;
}
