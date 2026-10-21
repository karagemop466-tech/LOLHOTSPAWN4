"""Accessible, static-first Pages output. Every row includes original sources."""
from __future__ import annotations

from datetime import timedelta
from html import escape
import json
from pathlib import Path
from urllib.parse import urlparse

from .core import dt, iso, MAX_QUOTE_AGE

REPO = "https://github.com/karagemop466-tech/LOLHOTSPAWN4"
NAV = [("index.html", "Overview"), ("picks.html", "All matches"), ("featured.html", "Market-backed"),
       ("fallback.html", "History models"), ("unresolved.html", "Unresolved"),
       ("flagged.html", "Flagged for Review"), ("methodology.html", "Method & sources")]
METHODS = {"bookmaker": "Bookmaker", "prediction_market": "Prediction market", "model": "History model", "unresolved": "Unverified"}


def e(value):
    return escape(str(value if value is not None else ""), quote=True)


def link(url, text, cls=""):
    return f'<a class="{e(cls)}" href="{e(url)}" rel="noopener noreferrer">{e(text)}</a>'


def when(value):
    parsed = dt(value)
    return parsed.strftime("%d %b %Y · %H:%M UTC") if parsed else "Time unconfirmed"


def percentage(value):
    return f"{value * 100:.1f}%" if value is not None else "—"


def valid_until(row):
    times = [dt(row.get("start_utc")), dt(row.get("lock_utc"))]
    inventory = dt(row.get("inventory_at"))
    if inventory:
        times.append(inventory + MAX_QUOTE_AGE)
    for ev in row.get("evidence", [])[:1]:
        observed = dt(ev.get("observed_at"))
        times.append(observed + MAX_QUOTE_AGE if observed else None)
        times.append(dt(ev.get("start_utc")))
    return iso(min(t for t in times if t)) if any(times) else ""


def sources_for(row, *, compact=False):
    links = [link(row["hotspawn_url"], "Hotspawn match" if row["canonical_match_link"] else "Hotspawn inventory · ID " + row["id"])]
    if row["canonical_match_link"] and not compact:
        links.append(link(row["inventory_source"], "Original inventory feed"))
    if row["evidence"]:
        for ev in row["evidence"][:1 if compact else len(row["evidence"])]:
            links.append(link(ev["source_url"], ev["provider"] + " series price · " + ev["id"]))
            if not compact:
                links.append(link(ev["metadata_url"], ev["provider"] + " event metadata"))
    if row["model"]:
        rs = row["model"]["training_results"]
        chosen = []
        for team in (row["team_a"], row["team_b"]):
            from .core import norm
            chosen += [r for r in rs if norm(team) in {norm(r["team_a"]), norm(r["team_b"])}][:1]
        for result in {r["id"]: r for r in (chosen if compact else rs)}.values():
            links.append(link(result["source_url"], result["id"] + " · " + result["source_date"]))
    return '<div class="source-links">' + "".join(links) + "</div>"


def evidence_details(row):
    chunks = []
    for ev in row["evidence"]:
        order = f"{ev['team_a']} / {ev['team_b']}"
        chunks.append(f'<div class="evidence-item"><h4>{e(ev["provider"])} · full-series winner</h4>'
                      f'<dl class="detail-grid"><div><dt>Observed</dt><dd>{e(when(ev["observed_at"]))}</dd></div>'
                      f'<div><dt>Publisher updated</dt><dd>{e(when(ev.get("provider_updated_at"))) if ev.get("provider_updated_at") else "Not supplied"}</dd></div>'
                      f'<div><dt>Publisher start</dt><dd>{e(when(ev["start_utc"]))}</dd></div>'
                      f'<div><dt>Publisher order</dt><dd>{e(order)}</dd></div>'
                      f'<div><dt>Raw prices</dt><dd>{e(json.dumps(ev.get("raw_prices"), ensure_ascii=False))}</dd></div>'
                      f'<div><dt>Team order reversed?</dt><dd>{"Yes, aligned to Hotspawn" if ev["reversed_to_inventory"] else "No"}</dd></div></dl></div>')
    if row["model"]:
        model = row["model"]
        chunks.append(f'<h4>Partial-series history model</h4><p>{e(model["limitations"])}</p>'
                      f'<p>Audited series records: <strong>{e(row["team_a"])} {model["wins"][0]}W–{model["losses"][0]}L</strong>; '
                      f'<strong>{e(row["team_b"])} {model["wins"][1]}W–{model["losses"][1]}L</strong>. '
                      f'Training cutoff: {e(when(model["cutoff_utc"]))}. These are partial observed records, not complete season standings.</p>'
                      f'<p>{link("methodology.html#model", "Formula, assumptions & limitations")} · '
                      f'{link("methodology.html#history", "All dated organizer observations")}</p>')
    flag_list = "".join(f"<li>{e(flag)}</li>" for flag in row["flags"])
    if flag_list:
        chunks.append('<h4>Review notes</h4><ul class="review-notes">' + flag_list + "</ul>")
    chunks.append(sources_for(row))
    return '<details class="evidence"><summary>Evidence, timestamps & review notes</summary><div class="evidence-body">' + "".join(chunks) + "</div></details>"


def attributes(row):
    search = " ".join([row["team_a"], row["team_b"], row["competition"], row["id"], row["reason"]]).casefold()
    return (f'data-match-id="{e(row["id"])}" data-search="{e(search)}" '
            f'data-competition="{e(row["competition"])}" data-state="{e(row["state"])}" '
            f'data-valid-until="{e(valid_until(row))}" data-has-probability="{str(row["probability_a"] is not None).lower()}"')


def pick_text(row):
    if row["pick"]:
        return "Pick: " + row["pick"]
    if row["probability_a"] is not None:
        return "No directional edge · supported tie"
    return "No current prematch pick" if row["state"] != "upcoming" else "Unresolved · no supported pick"


def important_note(row):
    for prefix in ("Schedule conflict", "Inventory observation", "Unconfirmed", "Uncalibrated", "Stale-listed", "Evidence-based tie"):
        found = next((flag for flag in row["flags"] if flag.startswith(prefix)), None)
        if found:
            return found
    return row["flags"][0] if row["flags"] else ""


def card(row):
    badge = METHODS[row["method"]] if row["state"] == "upcoming" else "Elapsed listing" if row["state"] == "elapsed" else "Locked / unconfirmed"
    time = f'<time datetime="{e(row["start_utc"])}">{e(when(row["start_utc"]))}</time>' if row["start_utc"] else "Time unconfirmed"
    value = row["probability_a"]
    bar = f'<div class="prob-bar" aria-hidden="true"><span style="width:{value * 100:.4f}%"></span></div>' if value is not None else '<p class="blank-note">Blank by design · no verified probability input</p>'
    probabilities = "".join(f'<div><span class="team-label">{e(row["team_" + side])}</span><strong class="prob-value current-probability">{percentage(row["probability_" + side])}</strong></div>' for side in ("a", "b"))
    notice = f'<p class="tiny-note"><strong>Needs review:</strong> {e(important_note(row))}</p>' if row["flags"] else ""
    first_source = sources_for(row, compact=True)
    return (f'<article class="match-card {e(row["method"])}" id="match-{e(row["id"])}" {attributes(row)}>'
            f'<div class="card-top"><span class="badge {e(row["method"])}">{e(badge)}</span><span class="fixture-id">#{e(row["id"])}</span></div>'
            f'<p class="competition">{e(row["competition"])}</p>'
            f'<h3>{e(row["team_a"])} <span class="versus">vs</span> {e(row["team_b"])}</h3>'
            f'<p class="match-time">{time} <span>· Hotspawn schedule</span></p>'
            f'<div class="prob-grid">{probabilities}</div>{bar}'
            f'<p class="pick current-pick">{e(pick_text(row))}</p>'
            f'<p class="match-reason">{e(row["reason"])}</p>{notice}{first_source}{evidence_details(row)}</article>')


def table_row(row):
    model = "<br><span class=\"muted\">Uncalibrated estimate</span>" if row["method"] == "model" else ""
    return (f'<tr {attributes(row)}><th scope="row">{link("#match-" + row["id"], row["team_a"] + " vs " + row["team_b"], "table-match-link")}<small>#{e(row["id"])}</small></th>'
            f'<td>{e(row["competition"])}</td><td>{e(when(row["start_utc"]))}<small>{e(row["state"])}</small></td>'
            f'<td><span class="current-probability">{percentage(row["probability_a"])}</span></td>'
            f'<td><span class="current-probability">{percentage(row["probability_b"])}</span></td>'
            f'<td class="current-pick">{e(pick_text(row))}</td><td>{e(METHODS[row["method"]])}{model}</td>'
            f'<td>{e(row["reason"])}<small>{e(important_note(row))}</small></td>'
            f'<td>{sources_for(row, compact=True)}</td></tr>')


def listing(rows, *, name="matches", intro=""):
    if not rows:
        return '<div class="empty-state"><h2>No current matches in this view</h2><p>No placeholder probabilities have been inserted. ' + link("picks.html", "See the full inventory") + ' or ' + link("methodology.html#sources", "review source access") + '.</p></div>'
    competitions = sorted({r["competition"] for r in rows})
    options = '<option value="">Every competition</option>' + "".join(f'<option value="{e(c)}">{e(c)}</option>' for c in competitions)
    return (f'<section class="match-browser" aria-label="{e(name)}"><p class="section-intro">{e(intro)}</p>'
            '<div class="toolbar"><div class="search-field"><label for="match-search">Find a team, competition or fixture ID</label>'
            '<input id="match-search" type="search" placeholder="Search matches…" autocomplete="off"></div>'
            f'<div><label for="competition-filter">Competition</label><select id="competition-filter">{options}</select></div>'
            '<div><label for="state-filter">Listing status</label><select id="state-filter"><option value="">All listed</option><option value="upcoming">Upcoming / unlocked</option><option value="elapsed">Elapsed / stale-listed</option><option value="locked">Locked</option><option value="unknown_time">Time unknown</option></select></div></div>'
            '<div class="list-topline"><p id="result-count" role="status" aria-live="polite">' + str(len(rows)) + ' matches</p>'
            '<div class="view-switch" role="group" aria-label="Match display"><button type="button" id="cards-view" aria-pressed="true">Cards</button><button type="button" id="table-view" aria-pressed="false">Table</button></div></div>'
            '<p id="no-results" class="empty-state" hidden>No matches fit these filters. Try another team or clear the filters.</p>'
            '<div id="match-cards" class="match-grid">' + "".join(card(r) for r in rows) + '</div>'
            '<div id="match-table" class="table-region" tabindex="0" role="region" aria-label="Match table, scroll horizontally within this area" hidden><table>'
            '<caption>All source-linked matches in this view. A dash means unconfirmed, never 50%. Percentages are rounded; full precision is in the JSON download.</caption>'
            '<thead><tr><th scope="col">Fixture</th><th scope="col">Competition</th><th scope="col">Hotspawn start (UTC)</th><th scope="col">Team A</th><th scope="col">Team B</th><th scope="col">Pick</th><th scope="col">Method</th><th scope="col">Reason / review</th><th scope="col">Original sources</th></tr></thead><tbody>'
            + "".join(table_row(r) for r in rows) + '</tbody></table></div>'
            '<div class="pagination"><button type="button" id="previous-page">← Previous</button><span id="page-count">All matches</span><button type="button" id="next-page">Next →</button></div>'
            '<noscript><p>JavaScript is off. All matches and evidence remain readable as this dated static snapshot. Filtering, pagination and between-refresh expiry hiding require JavaScript; check source timestamps before using any number.</p></noscript></section>')


def shell(data, page, title, body, subtitle=""):
    nav = "".join(f'<a href="{href}"' + (' aria-current="page"' if href == page else '') + f'>{label}</a>' for href, label in NAV)
    inventory = data["inventory_observed_at"] or ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark"><meta name="description" content="Independent LoL picks across the Hotspawn inventory. External full-series prices, dated organizer-history models, and honestly unresolved matches."><title>{e(title)} · Rift Ledger</title><link rel="icon" href="assets/mark.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script></head>
<body data-inventory-at="{e(inventory)}" data-generated-at="{e(data['generated_at'])}"><a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="header-inner"><a class="brand" href="index.html"><img src="assets/mark.svg" width="38" height="38" alt=""><span>RIFT LEDGER<small>Hotspawn LoL · independent picks</small></span></a><div class="header-meta"><span class="cadence"><span aria-hidden="true">●</span> 4h refresh target</span><span class="snapshot-label">Inventory observed {e(when(inventory))}</span></div></div><nav class="main-nav" aria-label="Primary">{nav}</nav></header>
<div id="freshness-warning" class="freshness-warning" role="status" {'hidden' if data['inventory_fresh'] else ''}>Inventory snapshot is over 8 hours old or unconfirmed. New fixtures cannot be guaranteed; expired probabilities and picks are hidden. Check the source/run receipts.</div>
<main id="main" class="page"><div class="page-heading"><p class="eyebrow">LEAGUE OF LEGENDS / SOURCE-BACKED ANALYSIS</p><h1>{e(title)}</h1>{f'<p class="lede">{e(subtitle)}</p>' if subtitle else ''}</div>{body}</main>
<footer class="site-footer"><p><strong>Evidence over false certainty.</strong> Informational estimates, not betting advice. No outcome guarantees. Independent of Hotspawn and the source providers.</p><div>{link('data/matches.json', 'Download current snapshot (JSON)')}{link('data/integrity.json', 'Integrity receipt')}{link(REPO + '/actions/workflows/verified-pages.yml', 'Refresh & deployment runs')}{link(REPO, 'Source code')}</div><p class="fine-print">Built {e(when(data['generated_at']))}. Counts describe this snapshot, not a live betting feed. Sources can restrict access; blank values stay blank. GitHub schedules are best-effort.</p></footer></body></html>'''


def overview(data):
    s = data["summary"]
    market = [r for r in data["matches"] if r["method"] in {"bookmaker", "prediction_market"}]
    stats = [(s["listed"], "listed fixtures", "picks.html"), (s["picks"], "supported directional picks", "picks.html"),
             (s["unresolved"], "upcoming without a pick", "unresolved.html"), (s["elapsed"], "elapsed, still listed", "picks.html#inventory-accounting")]
    stats_html = "".join(f'<a class="stat" href="{url}"><strong>{count}</strong><span>{e(label)}</span><span class="stat-arrow" aria-hidden="true">↗</span></a>' for count, label, url in stats)
    body = f'''<section class="hero-split" aria-label="Executive summary"><div class="hero-copy"><span class="edition">THE INDEPENDENT MATCH BRIEF</span><h2>An edge needs<br><span>evidence.</span></h2><p>All listed matches. Only supported numbers. Full-series external prices and auditable history estimates — never Hotspawn crowd picks.</p><div class="hero-actions"><a class="button primary" href="picks.html">Explore all {s['listed']} matches <span aria-hidden="true">↗</span></a><a class="button secondary" href="unresolved.html">What's unresolved?</a></div></div><aside class="brief-card"><span class="eyebrow">EXECUTIVE SUMMARY</span><h2>{s['upcoming']} upcoming listings.<br>Not {s['upcoming']} certain picks.</h2><p><strong>{s['bookmaker'] + s['prediction_market']} market-backed rows</strong> and <strong>{s['model']} history-model rows</strong> pass the stated evidence guards. {s['unresolved']} upcoming rows have no directional pick; unsupported inputs remain blank.</p><p>Models use partial, very small samples and are <strong>not calibrated</strong>. Exact-name history is missing for many teams. Restricted sources, aliases, unknown formats and schedule conflicts limit coverage.</p><a href="flagged.html">Open Flagged for Review →</a></aside></section>
<section aria-labelledby="coverage-heading"><div class="section-heading"><div><p class="eyebrow">ACCOUNT FOR THE WHOLE LOBBY</p><h2 id="coverage-heading">Coverage at a glance</h2></div><a href="methodology.html#sources">Source health & freshness →</a></div><div class="stats-grid">{stats_html}</div><p class="snapshot-note">Inventory observations establish listings and schedules only. {s['locked_or_unknown']} additional rows are locked or time-unconfirmed. All counts reconcile to unique source IDs; {link('data/matches.json', 'inspect the snapshot')}.</p></section>
<section class="route-panel" aria-labelledby="browse-heading"><h2 id="browse-heading">Choose your evidence level</h2><div class="route-grid"><a href="featured.html"><strong>Market-backed</strong><span>Full-series bookmaker & prediction-market lines</span><b aria-hidden="true">↗</b></a><a href="fallback.html"><strong>Independent fallback</strong><span>Dated organizer history, formula and every input</span><b aria-hidden="true">↗</b></a><a href="unresolved.html"><strong>Unresolved</strong><span>What is missing and why the numbers are blank</span><b aria-hidden="true">↗</b></a><a href="methodology.html"><strong>Methodology & sources</strong><span>Matching rules, assumptions, timestamps and receipts</span><b aria-hidden="true">↗</b></a></div></section>
<section aria-labelledby="featured-heading"><div class="section-heading"><div><p class="eyebrow">EXTERNAL FULL-SERIES EVIDENCE</p><h2 id="featured-heading">Market-backed watchlist</h2></div><a href="featured.html">See every market-backed match →</a></div><p class="section-intro">Price-implied probabilities, not known outcomes. Review any start-time conflict before using a pick.</p><div class="match-grid">{''.join(card(r) for r in market[:3]) if market else '<p class="empty-state">No current eligible full-series line. No placeholders inserted.</p>'}</div></section>
<section class="limitations-panel" aria-labelledby="limitations-heading"><div><p class="eyebrow">THE HONEST BOTTOM LINE</p><h2 id="limitations-heading">Coverage ≠ confidence.</h2></div><div><p><strong>No source, no number.</strong> A missing market is not a 50/50 prediction. Amateur results, team aliases, unknown timezones and inaccessible sources cannot be filled by inference.</p><p><strong>Fallback is a model, not a fact.</strong> The small, partial organizer archive is independently sourced, but there is no out-of-sample calibration. Equal model rates produce no arbitrary team-A pick.</p><p><strong>Nothing is silently dropped.</strong> Past “scheduled” rows stay in the full inventory, separate from upcoming picks. Every row links to original inventory evidence and any probability inputs.</p><p>{link('unresolved.html', 'Read all unresolved cases')} · {link('flagged.html', 'Review source irregularities')} · {link('methodology.html#model', 'Understand the fallback')}</p></div></section>'''
    return shell(data, "index.html", "The match brief", body, "Independent LoL picks. Transparent sources. Honest gaps.")


def history_table(history):
    rows = []
    for r in history["records"]:
        rows.append(f'<tr><th scope="row">{e(r["team_a"])} vs {e(r["team_b"])}</th><td>{e(r["source_date"])}</td><td>{r["score_a"]}–{r["score_b"]} · BO3</td><td>{e(r["competition"])}</td><td>{e(r.get("observed_on"))}</td><td>{link(r["source_url"], r["id"] + " · organizer result")}</td></tr>')
    return '<div class="table-region" tabindex="0" role="region" aria-label="Organizer result observations, horizontally scrollable"><table><caption>Partial original-organizer archive. Displayed dates have no verified timezone; fan predictions and profile aggregates are excluded.</caption><thead><tr><th scope="col">Teams</th><th scope="col">Displayed date</th><th scope="col">Series result</th><th scope="col">Division</th><th scope="col">Observed on</th><th scope="col">Official source</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'


def method_page(data, history):
    source_rows = []
    for source in data["sources"]:
        state = source.get("status", "Unconfirmed")
        if source.get("cache_used"):
            state += " · last-good cache used"
        source_rows.append(f'<tr><th scope="row">{link(source["source_url"], source["source_id"])}</th><td>{e(state)}<small>{e(source.get("error"))}</small></td><td>{e(when(source.get("attempted_at")))}</td><td>{e(when(source.get("observed_at")))}</td><td>{e(source.get("http_status") if source.get("http_status") is not None else "Not confirmed")}</td></tr>')
    body = f'''<section class="prose-panel" id="rules"><h2>What the numbers mean</h2><ol><li><strong>Inventory only:</strong> the public Hotspawn LoL fixtures response defines the complete list of unique IDs, teams, competition and listed UTC start/lock time. Crowd percentages, pick counts and Hotspawn results are dropped before caching or modeling.</li><li><strong>Bookmaker first:</strong> Pinnacle public LoL league discovery, parent pending/non-live matchup metadata and open full-series moneylines are joined by exact matchup ID. Required price scope: moneyline, period 0, key <code>s;0;m</code>, home and away. Map, handicap, correct-score and outright markets are rejected.</li><li><strong>Prediction market second:</strong> paginated Polymarket LoL events are searched for active, open, order-accepting <em>Match Winner</em> markets with <code>sportsMarketType=moneyline</code>, two named team outcomes and an explicit game/event start. <code>child_moneyline</code> and Game 1 are rejected even when prices happen to equal the series market.</li><li><strong>Exact match:</strong> both team names must agree after typography/case normalization, with the same competition family, a unique inventory match and explicit starts within six hours. No fuzzy team/academy aliases. Any nonidentical start remains prominently flagged; quoted and inventory times are both retained. Unknown or distant timestamps fail closed.</li><li><strong>No accepted market:</strong> only the independently dated organizer-history model below may provide a fallback. If either team lacks eligible inputs, both probabilities and the pick stay null. An evidence-based equal estimate has no directional pick.</li></ol><p>Other original sportsbook/esportsbook pages (GG.bet, Thunderpick, bwin) and organizer results (Komplett/RIVALS) are retried for access and listed for manual review. Restricted pages and client shells supply no accepted prices or results. This is not exhaustive bookmaker discovery, and access failure never means “market absent.”</p></section>
<section class="prose-panel" id="prices"><h2>Reproduce an external line</h2><p>For American odds <var>x</var>, implied chance is <code>100/(x+100)</code> when positive, or <code>−x/(−x+100)</code> when negative. Remove the two-way overround: <code>pA = qA/(qA+qB)</code>, <code>pB = 1−pA</code>. Polymarket's paired outcome prices are normalized by their sum.</p><p>Each card retains the original publisher order, any reversal into Hotspawn order, raw quotes, both source URLs, observation time and provider-update time where supplied. Pinnacle does not supply a quote-change timestamp in this endpoint; retrieval time is not mislabeled as one. The first eligible bookmaker is primary; otherwise the prediction market is primary. Other evidence is displayed, not blindly averaged. Picks choose the strictly greater probability; ties never default to the first team.</p><p>These are normalized price implications, not a claim about the true chance of winning or profitability.</p></section>
<section class="prose-panel" id="model"><h2>The independent fallback — and its limits</h2><p><strong>Model version:</strong> <code>{e(data['model_version'])}</code>. Uses only source-linked completed BO3 series results for the same Prime League division and 2026/27 season. It does not use seed ratings, Hotspawn crowd/history, undated team-profile records, fan predictions, future scores or championship-futures ratios.</p><ol><li>Require at least <strong>two causal completed series for each exact team</strong>, in the trailing 60 days. The last confirmed result of each team must be within 14 days of the build. Profiles, similarly named academy teams and unconfirmed aliases cannot satisfy this requirement.</li><li>With a Beta(2,2) prior, calculate each partial record's smoothed series rate: <code>r = (wins + 2)/(series + 4)</code>.</li><li>Apply the log5 matchup formula: <code>q = (rA − rA×rB)/(rA + rB − 2×rA×rB)</code>.</li><li>Conservatively shrink the edge toward one half: <code>w = min(nA,nB)/(min(nA,nB)+10)</code>; <code>pA = 0.5 + w×(q−0.5)</code>, <code>pB = 1−pA</code>. No input history means no estimate, not a neutral fill.</li></ol><p><strong>Assumptions, not verified facts:</strong> Beta(2,2), log5 and the shrinkage constant 10 are fixed, transparent model choices, not fitted or validated parameters. The partial audited archive can be selection-biased; it is not a complete season record. There is no strength-of-schedule, roster, draft or patch adjustment and no out-of-sample calibration. Treat all estimates as low-confidence illustrations, especially far-future fixtures.</p><p><strong>No invented UTC:</strong> organizer pages print a local date/time without a confirmed timezone. The training eligibility rule uses the next UTC day plus 20 hours as an intentionally late bound (timezone/series buffer), and requires it to be before both build time and fixture start. This is a modeling cutoff rule, not the actual completion timestamp.</p><p><strong>Automatic source restriction:</strong> newly parsed result headers with no confirmed season are retained as observations but cannot satisfy same-season training eligibility. Audited observations remain dated observations. If the runner cannot retrieve new organizer results, the archive does not pretend to refresh; the last-result freshness rule eventually removes estimates. No manual maintenance is required to stop unsupported values from appearing.</p></section>
<section class="prose-panel" id="freshness"><h2>Freshness, automation & failure behavior</h2><p>The canonical verified publisher runs on GitHub Actions every <strong>4 hours</strong> (best-effort scheduling), with strict tests before publication. It publishes only the <code>verified/</code> artifact and never consumes the legacy dashboard's picks or seeded ratings.</p><p>A last-good inventory/quote may survive a failed fetch, but its original observation timestamp is preserved. Quotes older than 8 hours cannot price a match. Elapsed, locked, provisional or unknown-time rows remain listed without a current prematch pick. The browser also hides stale/locked probabilities between refreshes. If the inventory cannot be established at all, publication fails and preserves the last-good site.</p><p>HTTP 200 means retrieval, not data validation. Failed sources, cache use and unknown timestamps are visible below. {link(REPO + '/actions/workflows/verified-pages.yml', 'Inspect actual refresh and deployment runs')}; {link('data/integrity.json', 'read the latest calculation-integrity receipt')}.</p></section>
<section id="sources"><div class="section-heading"><div><p class="eyebrow">ORIGINAL PUBLISHERS, ACTUAL ATTEMPTS</p><h2>Source health & receipts</h2></div>{link('data/source-cache.json', 'Dated receipt payloads')}</div><p class="section-intro">A source can be reachable yet yield no usable full-series evidence. External market coverage is not exhaustive. Attempt time and last successful observation are deliberately separate.</p><div class="table-region" tabindex="0" role="region" aria-label="Source health table, horizontally scrollable"><table><caption>Current refresh attempts and retained original observation dates.</caption><thead><tr><th scope="col">Original source</th><th scope="col">Retrieval status</th><th scope="col">Last attempted (UTC)</th><th scope="col">Observed (UTC)</th><th scope="col">HTTP status</th></tr></thead><tbody>{''.join(source_rows)}</tbody></table></div></section>
<section id="history"><div class="section-heading"><div><p class="eyebrow">AUDIT THE MODEL INPUTS</p><h2>Dated organizer observations</h2></div>{link('data/history.json', 'Download history JSON')}</div><p class="section-intro">{len(history['records'])} individually source-linked observations in the current partial archive. Eligibility is evaluated per target, not assumed for every observation. Every model card identifies exactly which rows it used.</p>{history_table(history)}</section>'''
    return shell(data, "methodology.html", "Methodology & sources", body, "Trace every number. Understand every assumption. See every failed source, too.")


def flagged_page(data):
    findings = ""
    for f in data["findings"]:
        findings += (f'<article class="finding" id="finding-{e(f["id"])}"><span class="badge review">Needs review · nonblocking</span><h3>{e(f["title"])}</h3>'
                     f'<p>{e(f["description"])}</p>' + (f'<p>{e(f["required_handling"])}</p>' if f.get("required_handling") else "")
                     + (f'<p class="tiny-note">{e(f["context"])}</p>' if f.get("context") else "")
                     + '<div class="source-links">' + "".join(link(s, "Original source " + str(i + 1)) for i, s in enumerate(f.get("sources", []))) + '</div></article>')
    body = ('<div class="notice-panel"><h2>Review is visible, not buried.</h2><p>“Needs review” is nonblocking. It never turns unconfirmed facts into verified values. Historical audit findings below are dated observations, not a claim that this build still uses the rejected inputs. Current row-level flags follow.</p></div>'
            '<section aria-labelledby="findings-heading"><h2 id="findings-heading">Source irregularities & historical corrections</h2><div class="finding-grid">' + findings + '</div></section>'
            '<section aria-labelledby="row-flags-heading"><h2 id="row-flags-heading">Current flagged inventory rows</h2>'
            + listing([r for r in data["matches"] if r["flags"]], name="Flagged inventory rows", intro="Includes missing formats, schedule disagreements, partial history limitations and elapsed listings. Expand each card for every note and original source.") + '</section>')
    return shell(data, "flagged.html", "Flagged for Review", body, "Uncertainty is part of the product — not a reason to invent a number.")


def render_site(data, history, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    pages = {"index.html": overview(data), "methodology.html": method_page(data, history), "flagged.html": flagged_page(data)}
    routes = {
        "picks.html": ("All listed matches", data["matches"], "Every source ID is accounted for, including elapsed listings. Unsupported probabilities are blank, not 50/50."),
        "featured.html": ("Market-backed picks", [r for r in data["matches"] if r["method"] in {"bookmaker", "prediction_market"}], "Full-series external lines only. Bookmaker prices are preferred; prediction-market evidence is labeled separately."),
        "fallback.html": ("Independent history models", [r for r in data["matches"] if r["method"] == "model"], "Low-confidence, uncalibrated estimates from dated organizer series results. Partial records, not complete standings or bookmaker quotes."),
        "unresolved.html": ("Unresolved picks", [r for r in data["matches"] if r["state"] == "upcoming" and r["pick"] is None], "No accepted line or sufficient independent history means no number. Evidence-based ties also have no directional pick.")}
    for page, (title, rows, subtitle) in routes.items():
        extra = ''
        if page == "picks.html":
            s = data["summary"]
            extra = f'<div class="notice-panel" id="inventory-accounting"><strong>Inventory accounting</strong><p>{s["listed"]} listed = {s["upcoming"]} upcoming + {s["elapsed"]} elapsed + {s["locked_or_unknown"]} locked/time-unconfirmed. Elapsed listings are not claimed as completed results or current betting opportunities.</p></div>'
        if page == "unresolved.html":
            extra = '<div class="notice-panel"><h2>Why a pick can be unresolved</h2><p>Missing public full-series quotes; restricted/unreadable source pages; unverified participant aliases; fewer than two dated causal series for either exact team; stale history; or an evidence-based tie. A page shell or generic wiki link is not probability evidence.</p><p>' + link("methodology.html#sources", "Review current source access") + ' · ' + link("flagged.html", "Open source irregularities") + '</p></div>'
        pages[page] = shell(data, page, title, extra + listing(rows, name=title), subtitle)
    pages["404.html"] = shell(data, "404.html", "That page is not in the ledger", '<div class="empty-state"><p>' + link("index.html", "Return to the match brief") + ' or ' + link("picks.html", "browse all listed matches") + '.</p></div>')
    for name, content in pages.items():
        (output / name).write_text(content + "\n", encoding="utf-8")
    (output / ".nojekyll").write_text("")
    (output / "data/deployment.json").write_text(json.dumps({"generated_at": data["generated_at"], "build": data.get("build"), "summary": data["summary"], "artifact": "verified-only"}, indent=2) + "\n")
