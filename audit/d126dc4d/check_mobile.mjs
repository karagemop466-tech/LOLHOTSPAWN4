#!/usr/bin/env node
/**
 * Independent responsive/browser/accessibility QA. Tools are kept out of Git:
 * npm install --prefix .arena/audit-tools --no-fund --no-audit \
 *   playwright-core@1.64.1 @sparticuz/chromium@153.0.0 axe-core@4.14.0
 * node audit/d126dc4d/check_mobile.mjs --url http://127.0.0.1:8080/ \
 *   --out audit/d126dc4d/browser-audit.json --expect-data
 *
 * Tests rendered behavior only; this does not verify publisher facts or prices.
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const args = process.argv.slice(2);
const value = (flag, fallback) => {
  const pos = args.indexOf(flag);
  return pos >= 0 && args[pos + 1] ? args[pos + 1] : fallback;
};
const base = new URL(value('--url', 'http://127.0.0.1:8080/'));
const out = value('--out', 'audit/d126dc4d/browser-audit.json');
const pages = value('--pages', 'index.html,picks.html,flagged.html,methodology.html').split(',');
const widths = value('--widths', '360,390,768,1280').split(',').map(Number);
const expectData = args.includes('--expect-data');
const generatedAt = value('--generated-at', '');
const require = createRequire(path.resolve(value('--tools', '.arena/audit-tools'), 'package.json'));
const mod = require('@sparticuz/chromium');
const chromium = mod.default || mod;
const { chromium: playwright } = require('playwright-core');
const libs = await mod.inflate(path.resolve(path.dirname(require.resolve('@sparticuz/chromium')), '../bin/al2023.tar.br'));
const browser = await playwright.launch({
  executablePath: await chromium.executablePath(),
  args: chromium.args.filter(arg => arg !== '--single-process'),
  headless: true,
  env: { ...process.env, LD_LIBRARY_PATH: path.join(libs, 'lib') + ':' + (process.env.LD_LIBRARY_PATH || '') },
});
const result = {
  audit: 'Independent rendered responsive and WCAG A/AA smoke test',
  checked_at: new Date().toISOString(),
  base_url: base.href,
  browser: browser.version(),
  publisher_facts_verified: false,
  viewports: [],
  failures: [],
};

try {
  for (const width of widths) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
    for (const route of pages) {
      const page = await context.newPage();
      const pageErrors = [];
      const failedLocalRequests = [];
      page.on('pageerror', error => pageErrors.push(error.message));
      page.on('response', response => {
        if (response.status() >= 400 && new URL(response.url()).origin === base.origin) {
          failedLocalRequests.push({ url: response.url(), status: response.status() });
        }
      });
      const url = new URL(route, base).href;
      const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      await page.evaluate(() => document.fonts.ready);
      const metrics = await page.evaluate(() => ({
        title: document.title,
        generated_at: document.body.dataset.generatedAt,
        h1_count: document.querySelectorAll('h1').length,
        viewport_width: window.innerWidth,
        document_width: document.documentElement.scrollWidth,
        body_width: document.body.scrollWidth,
        link_to_picks_count: [...document.querySelectorAll('a[href]')].filter(a => /picks(?:\.html|\/|\?|#|$)/i.test(a.getAttribute('href'))).length,
        rendered_match_count: document.querySelectorAll('article.match, article.match-card, [data-match-id]').length,
        visible_text: document.body.innerText.slice(0, 10000),
      }));
      await page.addScriptTag({ path: require.resolve('axe-core/axe.min.js') });
      const accessibility = await page.evaluate(async () => {
        const r = await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } });
        return r.violations.map(v => ({ id: v.id, impact: v.impact, description: v.description, help_url: v.helpUrl, nodes: v.nodes.map(n => ({ target: n.target, summary: n.failureSummary })) }));
      });
      const record = {
        route, width, status: response?.status(),
        title: metrics.title,
        generated_at: metrics.generated_at,
        h1_count: metrics.h1_count,
        document_width: metrics.document_width,
        body_width: metrics.body_width,
        rendered_match_count: metrics.rendered_match_count,
        link_to_picks_count: metrics.link_to_picks_count,
        page_errors: pageErrors,
        failed_local_requests: failedLocalRequests,
        accessibility_violations: accessibility,
      };
      result.viewports.push(record);
      const fail = (issue) => result.failures.push({ route, width, issue });
      if (response?.status() !== 200) fail('Page response is not 200');
      if (metrics.document_width > width + 1 || metrics.body_width > width + 1) fail('Page-wide horizontal overflow');
      if (generatedAt && metrics.generated_at !== generatedAt) fail('HTML/JSON snapshot version mismatch');
      if (metrics.h1_count !== 1) fail('Expected one rendered primary heading');
      if (pageErrors.length) fail('JavaScript runtime error');
      if (failedLocalRequests.length) fail('Failed same-site asset/data request');
      if (accessibility.length) fail('WCAG A/AA automated accessibility violations');
      if (route === 'index.html' && metrics.link_to_picks_count === 0) fail('Executive summary has no direct picks link');
      if (expectData && /(?:could not load|failed to load|unable to load|no data available|data unavailable)/i.test(metrics.visible_text)) fail('Rendered data-load failure');
      if (args.includes('--screenshots') && route === 'index.html' && [390, 1280].includes(width)) {
        const filename = path.join(path.dirname(out), `landing-${width}.png`);
        fs.mkdirSync(path.dirname(filename), { recursive: true });
        await page.screenshot({ path: filename, fullPage: true });
        record.screenshot = filename;
      }
      await page.close();
    }
    await context.close();
  }
} finally {
  await browser.close();
  result.passed = result.failures.length === 0;
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ passed: result.passed, viewport_checks: result.viewports.length, failures: result.failures, report: out }, null, 2));
}
if (!result.passed) process.exitCode = 1;
