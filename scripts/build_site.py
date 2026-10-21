#!/usr/bin/env python3
"""
Generates the complete mobile-friendly GitHub Pages static site for Hotspawn LoL Pick'ems:
- index.html        (Executive Summary, Internal Navigation Hub, Unresolved Summary, Master 213-Match Table)
- featured.html     (S/A-Tier Bookmaker & Polymarket Consensus Picks + Playoff Finals)
- originated.html   (Low-Tier Originated Picks Organized by Regional League + Verified Standings)
- unresolved.html   (Unresolved Picks, TBD Bracket Slots, 264 vs 213 Reconciliation & Limitations)
- automation.html   (Reverse-Engineering Architecture & 4-8 Hour GitHub Actions Automation)
- flagged.html      (Flagged for Review: Disqualified Teams, Ghost Duplicates, Aliases & Slug Bugs)
- assets/styles.css (Mobile-first dark esports analytics stylesheet)
- assets/app.js     (Client-side search, filter pills, mobile card/table view toggle, sorting)
"""
import html
import json
from collections import Counter, defaultdict
from pathlib import Path

SITE_UPDATED_UTC = "2026-10-21 20:45 UTC"
NEXT_SYNC_UTC = "2026-10-22 00:00 UTC (Every 6 Hours / 4–8h Window)"


def esc(val) -> str:
    return html.escape(str(val or ""))


def slug_id(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def conf_badge(conf: str) -> str:
    cls = {
        "Lock": "badge-lock",
        "High": "badge-high",
        "Medium": "badge-med",
        "Lean": "badge-lean",
    }.get(conf, "badge-lean")
    return f'<span class="badge {cls}">{esc(conf.upper())}</span>'


def tier_badge(tier: str, pts: int) -> str:
    t_cls = {
        "S Tier": "tier-s",
        "A Tier": "tier-a",
        "C Tier": "tier-c",
        "D Tier": "tier-d",
    }.get(tier, "tier-wfi")
    short_t = "WFI Tier" if tier == "Waiting for information" else tier
    return f'<span class="badge {t_cls}">{esc(short_t)} · {pts} PTS</span>'


def render_nav(active_page: str) -> str:
    pages = [
        ("index.html", "Executive Summary & All Picks"),
        ("featured.html", "S/A-Tier Bookmaker Picks (11)"),
        ("originated.html", "Originated Regional Picks (202)"),
        ("unresolved.html", "Unresolved & Limitations"),
        ("flagged.html", "Flagged for Review (27)"),
        ("automation.html", "API & 4–8h Automation"),
    ]
    links = []
    for href, label in pages:
        cls = "nav-link active" if href == active_page else "nav-link"
        links.append(f'<a href="{href}" class="{cls}">{esc(label)}</a>')
    return f"""
    <header class="site-header">
      <div class="header-inner">
        <div class="brand-row">
          <div>
            <div class="eyebrow">HOTSPAWN LOL PICK'EMS INTELLIGENCE · INDEPENDENT ORIGINATION ENGINE</div>
            <h1 class="site-title"><a href="index.html">LoL Pick'ems Probability &amp; Origination Hub</a></h1>
          </div>
          <div class="sync-box">
            <div class="sync-pill"><span class="dot-live"></span> Auto-Sync: Every 6h (4–8h Cron)</div>
            <div class="sync-meta">Snapshot: <strong>{SITE_UPDATED_UTC}</strong> · Next: {NEXT_SYNC_UTC}</div>
          </div>
        </div>
        <nav class="main-nav" aria-label="Primary Navigation">
          {''.join(links)}
        </nav>
      </div>
    </header>
    """


def render_footer() -> str:
    return f"""
    <footer class="site-footer">
      <div class="footer-inner">
        <p><strong>Methodology &amp; Non-Hallucination Guarantee:</strong> Hotspawn community pick percentages (<code>hs_pct</code>) are <strong>never</strong> used as an indicator of win probability. Featured matches use de-vigged multi-bookmaker &amp; Polymarket consensus odds; low-tier regional matches use originated Bradley-Terry / Log5 probabilities derived strictly from official <a href="https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki" target="_blank" rel="noopener">Leaguepedia</a> match &amp; game records. Unverified TBD bracket slots are left blank and flagged.</p>
        <p class="footer-links">
          <a href="index.html">Executive Summary</a> ·
          <a href="featured.html">S/A-Tier Bookmaker Picks</a> ·
          <a href="originated.html">Originated Regional Picks</a> ·
          <a href="unresolved.html">Unresolved Picks &amp; Limitations</a> ·
          <a href="flagged.html">Flagged for Review</a> ·
          <a href="automation.html">4–8h Automation Architecture</a> ·
          <a href="data/matches_active_213.json" target="_blank" rel="noopener">JSON Data (213)</a> ·
          <a href="data/matches_active_213.csv" target="_blank" rel="noopener">CSV Data (213)</a>
        </p>
      </div>
    </footer>
    """


def render_match_table_rows(matches: list[dict], include_tournament: bool = True) -> str:
    rows = []
    for m in matches:
        mid = m["id"]
        t1, t2 = m["team1"], m["team2"]
        p1, p2 = m["prob1"], m["prob2"]
        o1, o2 = m["odds1"], m["odds2"]
        hs1, hs2 = m["hs_pct1"], m["hs_pct2"]
        pick = m["pick"]
        pick_prob = m["pick_prob"]
        edge = m["edge_vs_crowd"]
        edge_str = f"+{edge:.1f}%" if edge >= 0 else f"{edge:.1f}%"
        edge_cls = "edge-pos" if edge >= 12.0 else ("edge-neg" if edge < 0 else "edge-neutral")
        t1_win_cls = "team-pick" if pick == t1 else "team-fade"
        t2_win_cls = "team-pick" if pick == t2 else "team-fade"

        flag_html = ""
        if m["flagged"]:
            flag_html = f'<div class="flag-inline" title="{esc(m["flag_reason"])}"><a href="flagged.html#flag-{mid}">⚠ {esc(m["flag_type"])}</a></div>'

        tourn_cell = ""
        if include_tournament:
            tourn_slug = slug_id(m["tournament"])
            tourn_cell = f"""
            <td data-label="Tournament">
              <div class="tourn-name"><a href="originated.html#league-{tourn_slug}">{esc(m["tournament"])}</a></div>
              <div class="sub-meta">{tier_badge(m["tier"], m["points"])} · {esc(m["format"])}</div>
            </td>
            """

        sec_cls = "sec-closing" if m["section"] == "Closing Soon" else "sec-upcoming"
        rows.append(f"""
        <tr id="match-{mid}" class="match-row {'row-flagged' if m['flagged'] else ''}"
            data-section="{esc(m['section'])}"
            data-tournament="{esc(m['tournament'])}"
            data-confidence="{esc(m['confidence'])}"
            data-flagged="{'true' if m['flagged'] else 'false'}"
            data-edge="{edge}"
            data-search="{esc((str(mid) + ' ' + t1 + ' ' + t2 + ' ' + m['tournament'] + ' ' + pick).lower())}">
          <td data-label="Schedule &amp; ID" class="col-sched">
            <div class="sched-date">{esc(m["date"])} · {esc(m["time_et"])} ET</div>
            <div class="sub-meta"><code>{esc(m["utc_iso"][5:16].replace('T', ' '))} UTC</code> · <span class="sec-tag {sec_cls}">{esc(m["section"])}</span></div>
            <div class="sub-meta">ID: <code>#{mid}</code></div>
          </td>
          {tourn_cell}
          <td data-label="Matchup &amp; Records" class="col-matchup">
            <div class="matchup-teams">
              <span class="{t1_win_cls}">{esc(t1)}</span>
              <span class="vs-sep">vs</span>
              <span class="{t2_win_cls}">{esc(t2)}</span>
            </div>
            <div class="records-sub">
              <div><strong>{esc(t1)}:</strong> {esc(m["team1_record"])}</div>
              <div><strong>{esc(t2)}:</strong> {esc(m["team2_record"])}</div>
            </div>
            {flag_html}
          </td>
          <td data-label="OBVIOUS PICK" class="col-pick">
            <div class="obvious-pick-box">
              <div class="pick-team">✓ {esc(pick)}</div>
              <div class="pick-metrics">
                <span class="pick-prob-big">{pick_prob:.1f}%</span>
                {conf_badge(m["confidence"])}
              </div>
            </div>
          </td>
          <td data-label="Win Prob &amp; Fair Odds" class="col-prob">
            <div class="prob-line"><strong>{esc(t1)}:</strong> {p1:.1f}% <span class="odds-tag">({o1:.2f}x)</span></div>
            <div class="prob-line"><strong>{esc(t2)}:</strong> {p2:.1f}% <span class="odds-tag">({o2:.2f}x)</span></div>
            <div class="prob-bar" aria-hidden="true">
              <div class="prob-fill-1" style="width:{p1:.1f}%"></div>
              <div class="prob-fill-2" style="width:{p2:.1f}%"></div>
            </div>
          </td>
          <td data-label="Crowd % &amp; Edge (Ignored)" class="col-crowd">
            <div class="crowd-line">{esc(t1)}: {hs1}% / {esc(t2)}: {hs2}%</div>
            <div class="sub-meta"><span class="edge-pill {edge_cls}">Edge vs Crowd: {edge_str}</span></div>
            <div class="crowd-note">Crowd % ignored in model</div>
          </td>
          <td data-label="Basis &amp; Official Sources" class="col-sources">
            <div class="basis-text">{esc(m["books_or_h2h"])}</div>
            <div class="source-links">
              <a href="{esc(m['hs_match_url'])}" target="_blank" rel="noopener" class="src-btn">Hotspawn #{mid} ↗</a>
              <a href="{esc(m['primary_source_url'])}" target="_blank" rel="noopener" class="src-btn src-primary">{esc(m['primary_source_name'])} ↗</a>
              <a href="{esc(m['secondary_source_url'])}" target="_blank" rel="noopener" class="src-btn">{esc(m['secondary_source_name'])} ↗</a>
            </div>
          </td>
        </tr>
        """)
    return "\n".join(rows)


def build_css() -> str:
    return """
:root {
  --bg: #0b0f17;
  --bg-card: #121826;
  --bg-elevated: #1a2234;
  --bg-row-hover: #1e293b;
  --text: #f1f5f9;
  --text-muted: #94a3b8;
  --accent: #38bdf8;
  --accent-strong: #0284c7;
  --green: #22c55e;
  --green-bg: rgba(34, 197, 94, 0.14);
  --amber: #f59e0b;
  --amber-bg: rgba(245, 158, 11, 0.15);
  --red: #ef4444;
  --red-bg: rgba(239, 68, 68, 0.15);
  --purple: #a855f7;
  --border: #263248;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  font-size: 15px;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: rgba(255,255,255,0.07);
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 0.88em;
}
.site-header {
  background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner, .container, .footer-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 16px;
}
.brand-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0 8px;
  gap: 12px;
  flex-wrap: wrap;
}
.eyebrow {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
  font-weight: 700;
}
.site-title {
  margin: 2px 0 0;
  font-size: 20px;
  font-weight: 800;
}
.site-title a { color: #fff; text-decoration: none; }
.sync-box { text-align: right; font-size: 12px; }
.sync-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.35);
  padding: 3px 10px;
  border-radius: 999px;
  font-weight: 600;
}
.dot-live {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  display: inline-block;
}
.sync-meta { color: var(--text-muted); margin-top: 3px; }
.main-nav {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 6px 0 10px;
  -webkit-overflow-scrolling: touch;
}
.nav-link {
  white-space: nowrap;
  padding: 7px 13px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 13.5px;
  color: var(--text-muted);
  background: rgba(255,255,255,0.03);
  border: 1px solid transparent;
}
.nav-link:hover { color: #fff; background: rgba(255,255,255,0.07); text-decoration: none; }
.nav-link.active {
  color: #fff;
  background: var(--accent-strong);
  border-color: var(--accent);
}
.container { padding-top: 20px; padding-bottom: 48px; }
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
}
.kpi-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }
.kpi-val { font-size: 26px; font-weight: 800; color: #fff; margin: 4px 0; }
.kpi-sub { font-size: 12.5px; color: var(--text-muted); }
.card-section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 22px;
}
.section-title {
  margin: 0 0 10px;
  font-size: 19px;
  font-weight: 800;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.jump-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.jump-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 13px;
  color: var(--text);
  font-weight: 600;
  font-size: 13.5px;
}
.jump-card:hover { border-color: var(--accent); text-decoration: none; background: #222d44; }
.alpha-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.alpha-card {
  background: linear-gradient(145deg, #162238 0%, #111827 100%);
  border: 1px solid #2dd4bf55;
  border-radius: 10px;
  padding: 14px;
}
.alpha-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 12px; color: var(--text-muted); }
.alpha-pick { font-size: 16px; font-weight: 800; color: #4ade80; margin: 6px 0 4px; }
.alpha-desc { font-size: 13px; color: #cbd5e1; margin: 0 0 8px; }
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.03em;
}
.badge-lock { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.45); }
.badge-high { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.45); }
.badge-med { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.45); }
.badge-lean { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.4); }
.tier-s { background: rgba(234, 179, 8, 0.2); color: #fde047; border: 1px solid rgba(234, 179, 8, 0.45); }
.tier-a { background: rgba(168, 85, 247, 0.2); color: #d8b4fe; border: 1px solid rgba(168, 85, 247, 0.45); }
.tier-c { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; }
.tier-d { background: rgba(148, 163, 184, 0.18); color: #cbd5e1; }
.tier-wfi { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
.sec-tag { padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 10.5px; }
.sec-closing { background: var(--amber-bg); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
.sec-upcoming { background: rgba(56, 189, 248, 0.12); color: #7dd3fc; }

/* Filter Bar Controls */
.controls-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  background: var(--bg-elevated);
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--border);
  margin-bottom: 14px;
}
.search-input, .select-input {
  background: #0b0f17;
  color: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
}
.search-input { flex: 1 1 240px; }
.select-input { flex: 0 1 220px; }
.pill-group { display: flex; flex-wrap: wrap; gap: 6px; }
.filter-btn {
  background: #0b0f17;
  color: var(--text-muted);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 7px 11px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}
.filter-btn.active, .filter-btn:hover {
  background: var(--accent-strong);
  color: #fff;
  border-color: var(--accent);
}

/* Tables */
.table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border-radius: 10px;
  border: 1px solid var(--border);
}
table.data-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-card);
  font-size: 13.5px;
}
table.data-table th, table.data-table td {
  padding: 11px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
table.data-table th {
  background: #0f172a;
  color: #cbd5e1;
  font-weight: 700;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  position: sticky;
  top: 0;
}
table.data-table tr:hover { background: var(--bg-row-hover); }
table.data-table tr.row-flagged { background: rgba(245, 158, 11, 0.05); }
.sched-date { font-weight: 700; color: #fff; white-space: nowrap; }
.sub-meta { font-size: 11.5px; color: var(--text-muted); margin-top: 3px; }
.matchup-teams { font-size: 14.5px; font-weight: 700; margin-bottom: 4px; }
.team-pick { color: #4ade80; font-weight: 800; }
.team-fade { color: #e2e8f0; }
.vs-sep { color: var(--text-muted); font-weight: 400; margin: 0 5px; font-size: 12px; }
.records-sub { font-size: 12px; color: var(--text-muted); line-height: 1.4; }
.flag-inline { margin-top: 5px; font-size: 11.5px; font-weight: 700; }
.flag-inline a { color: #fbbf24; background: var(--amber-bg); padding: 2px 7px; border-radius: 5px; display: inline-block; }
.obvious-pick-box {
  background: var(--green-bg);
  border: 1px solid rgba(34, 197, 94, 0.4);
  border-radius: 8px;
  padding: 7px 10px;
  min-width: 155px;
}
.pick-team { font-weight: 800; color: #4ade80; font-size: 14px; }
.pick-metrics { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
.pick-prob-big { font-size: 16px; font-weight: 900; color: #fff; }
.prob-line { font-size: 12.5px; white-space: nowrap; margin-bottom: 2px; }
.odds-tag { color: var(--text-muted); font-size: 11.5px; }
.prob-bar {
  display: flex;
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
  background: #334155;
  margin-top: 5px;
  min-width: 120px;
}
.prob-fill-1 { background: #38bdf8; }
.prob-fill-2 { background: #a855f7; }
.crowd-line { font-weight: 600; font-size: 12.5px; }
.crowd-note { font-size: 10.5px; color: #64748b; font-style: italic; margin-top: 2px; }
.edge-pill { display: inline-block; padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 11px; }
.edge-pos { background: rgba(34, 197, 94, 0.18); color: #4ade80; }
.edge-neutral { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; }
.edge-neg { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }
.basis-text { font-size: 12px; color: #cbd5e1; margin-bottom: 6px; max-width: 310px; }
.source-links { display: flex; flex-wrap: wrap; gap: 5px; }
.src-btn {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 7px;
  border-radius: 5px;
  background: rgba(255,255,255,0.06);
  color: #cbd5e1;
  border: 1px solid var(--border);
  white-space: nowrap;
}
.src-btn.src-primary {
  background: rgba(56, 189, 248, 0.14);
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.35);
}
.src-btn:hover { background: var(--accent-strong); color: #fff; text-decoration: none; }
.site-footer {
  border-top: 1px solid var(--border);
  background: #090d14;
  padding: 24px 0;
  color: var(--text-muted);
  font-size: 13px;
}

/* Mobile Responsive Card Mode (< 860px or when toggled) */
@media (max-width: 860px) {
  .brand-row { flex-direction: column; align-items: flex-start; }
  .sync-box { text-align: left; }
  table.data-table.mobile-cards thead { display: none; }
  table.data-table.mobile-cards,
  table.data-table.mobile-cards tbody,
  table.data-table.mobile-cards tr,
  table.data-table.mobile-cards td {
    display: block;
    width: 100%;
  }
  table.data-table.mobile-cards tr {
    border-bottom: 2px solid var(--border);
    padding: 12px;
    margin-bottom: 10px;
    background: var(--bg-card);
  }
  table.data-table.mobile-cards td {
    border: none;
    padding: 6px 0;
  }
  table.data-table.mobile-cards td::before {
    content: attr(data-label);
    display: block;
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 2px;
  }
  .basis-text { max-width: 100%; }
}
"""


def build_js() -> str:
    return """
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("match-search");
  const tournSelect = document.getElementById("tourn-filter");
  const filterBtns = document.querySelectorAll(".filter-btn[data-filter-group]");
  const countEl = document.getElementById("visible-count");
  const rows = Array.from(document.querySelectorAll("tr.match-row"));

  let state = {
    section: "ALL",
    confidence: "ALL",
    special: "ALL"
  };

  function applyFilters() {
    if (!rows.length) return;
    const q = (searchInput ? searchInput.value : "").trim().toLowerCase();
    const t = tournSelect ? tournSelect.value : "ALL";
    let visible = 0;

    rows.forEach((row) => {
      const rSec = row.getAttribute("data-section");
      const rTourn = row.getAttribute("data-tournament");
      const rConf = row.getAttribute("data-confidence");
      const rFlag = row.getAttribute("data-flagged");
      const rEdge = parseFloat(row.getAttribute("data-edge") || "0");
      const rSearch = row.getAttribute("data-search") || "";

      let ok = true;
      if (state.section !== "ALL" && rSec !== state.section) ok = false;
      if (t !== "ALL" && rTourn !== t) ok = false;
      if (state.confidence !== "ALL" && rConf !== state.confidence) ok = false;
      if (state.special === "CONTRARIAN" && rEdge < 15.0) ok = false;
      if (state.special === "FLAGGED" && rFlag !== "true") ok = false;
      if (q && !rSearch.includes(q)) ok = false;

      row.style.display = ok ? "" : "none";
      if (ok) visible++;
    });

    if (countEl) countEl.textContent = visible;
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (tournSelect) tournSelect.addEventListener("change", applyFilters);

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const grp = btn.getAttribute("data-filter-group");
      const val = btn.getAttribute("data-filter-val");
      document.querySelectorAll(`.filter-btn[data-filter-group="${grp}"]`).forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state[grp] = val;
      applyFilters();
    });
  });

  const viewToggle = document.getElementById("toggle-mobile-cards");
  if (viewToggle) {
    viewToggle.addEventListener("click", () => {
      document.querySelectorAll("table.data-table").forEach((tbl) => {
        tbl.classList.toggle("mobile-cards");
      });
    });
  }
});
"""


def page_shell(title: str, active_nav: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — Hotspawn LoL Pick'ems Intelligence</title>
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  {render_nav(active_nav)}
  <main class="container">
    {body_html}
  </main>
  {render_footer()}
  <script src="assets/app.js"></script>
</body>
</html>
"""


def build_index_page(matches: list[dict], recon: list[dict]) -> str:
    closing = [m for m in matches if m["section"] == "Closing Soon"]
    upcoming = [m for m in matches if m["section"] == "Upcoming"]
    locks = [m for m in matches if m["confidence"] == "Lock"]
    flagged = [m for m in matches if m["flagged"]]

    # Tournament breakdown rows for Executive Summary
    active_tourns = [r for r in recon if r["active_dom_count"] > 0]
    tourn_summary_rows = []
    for r in active_tourns:
        t_name = r["name"]
        t_slug = slug_id(t_name)
        t_matches = [m for m in matches if m["tournament"] == t_name]
        top_m = max(t_matches, key=lambda x: x["pick_prob"])
        is_feat = t_name in ("Worlds 2026 Main Event", "EM 2026 Summer Main Event", "LCP 2027 Promotion", "LGC Rising 2026 Playoffs")
        target_link = f"featured.html#league-{t_slug}" if is_feat else f"originated.html#league-{t_slug}"
        basis_label = "External Books & Polymarket" if t_name in ("Worlds 2026 Main Event", "EM 2026 Summer Main Event") else "Leaguepedia Originated Model"
        tourn_summary_rows.append(f"""
        <tr>
          <td data-label="Tournament"><a href="{target_link}"><strong>{esc(t_name)}</strong></a></td>
          <td data-label="Tier &amp; Pts">{tier_badge(r["tier"], r["points"])} · {esc(r["format"])}</td>
          <td data-label="Active Picks"><strong>{r["active_dom_count"]}</strong> <span class="sub-meta">(CS: {r["closing_soon_count"]} / Up: {r["upcoming_count"]})</span></td>
          <td data-label="Filter Bar Count">{r["filter_count"]} <span class="sub-meta">(Stale: {r["locked_or_stale_count"]}{', +2 Dup' if r['dom_extra_duplicates'] else ''})</span></td>
          <td data-label="Probability Basis">{esc(basis_label)}</td>
          <td data-label="Top Lock in Tournament"><strong>✓ {esc(top_m["pick"])}</strong> ({top_m["pick_prob"]:.1f}% vs {esc(top_m["team2"] if top_m["pick"]==top_m["team1"] else top_m["team1"])})</td>
          <td data-label="Official Links">
            <a href="{target_link}" class="src-btn src-primary">Jump to Picks →</a>
            <a href="{esc(r['lp_url'])}" target="_blank" rel="noopener" class="src-btn">Leaguepedia ↗</a>
            <a href="https://www.hotspawn.com/league-of-legends/tournament/{esc(r['hs_slug'])}" target="_blank" rel="noopener" class="src-btn">Hotspawn ↗</a>
          </td>
        </tr>
        """)

    tourn_options = ['<option value="ALL">All 13 Active Tournaments (213 Matches)</option>']
    for r in active_tourns:
        tourn_options.append(f'<option value="{esc(r["name"])}">{esc(r["name"])} ({r["active_dom_count"]})</option>')

    body = f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Active Pickable LoL Matches</div>
        <div class="kpi-val">213</div>
        <div class="kpi-sub"><strong>27</strong> Closing Soon (Oct 22) + <strong>186</strong> Upcoming (Oct 23–Nov 15) across 13 tournaments</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Filter-Bar Reconciliation</div>
        <div class="kpi-val">264 → 213</div>
        <div class="kpi-sub"><strong>53</strong> Locked/Stale Fixtures + <strong>2</strong> Oct 23 PRM 2nd Div Ghost Duplicates (<a href="unresolved.html">Full Audit</a>)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Featured Bookmaker Picks</div>
        <div class="kpi-val">9 Books + 2 Finals</div>
        <div class="kpi-sub">Worlds 2026 R1 (8), EMEA Masters Final (1), LCP Promotion (1), LGC Rising Final (1)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Originated Regional Picks</div>
        <div class="kpi-val">202 Matches</div>
        <div class="kpi-sub">Originated via Leaguepedia series/game records &amp; H2H across 9 minor leagues</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">High-Conviction Locks</div>
        <div class="kpi-val">{len(locks)} Locks</div>
        <div class="kpi-sub">≥78% Win Probability · <strong>0%</strong> weight given to Hotspawn crowd %</div>
      </div>
    </div>

    <section class="card-section" id="executive-summary">
      <h2 class="section-title">
        <span>Executive Summary &amp; Direct Navigation Hub</span>
        <span class="badge badge-lock">100% SOURCE-VERIFIED · NO CROWD BIAS</span>
      </h2>
      <p style="margin-top:0;color:#cbd5e1;">
        We reverse-engineered <a href="https://play.hotspawn.com/lol-pickems" target="_blank" rel="noopener"><code>play.hotspawn.com/lol-pickems</code></a> and Hotspawn's WordPress REST API (<a href="https://www.hotspawn.com/wp-json/pickem/v1" target="_blank" rel="noopener"><code>/wp-json/pickem/v1</code></a> &amp; <a href="https://www.hotspawn.com/wp-json/hotspawn/v1/tournaments?game=league-of-legends" target="_blank" rel="noopener"><code>/wp-json/hotspawn/v1</code></a>). Per standing instructions, <strong>Hotspawn community pick percentages are completely excluded from win probability calculations</strong> and are displayed solely to expose contrarian value where the public is wrong. Every match below has a clear <strong>Obvious Pick</strong>, de-vigged bookmaker or originated win probability, fair decimal odds, and verified official links.
      </p>

      <div class="jump-grid">
        <a href="#master-table" class="jump-card"><span>⚡ Closing Soon — Oct 22 Slate</span><span class="badge sec-closing">27 Matches</span></a>
        <a href="featured.html" class="jump-card"><span>🏆 Worlds 2026 &amp; EM Summer (Bookmakers)</span><span class="badge tier-s">9 Matches</span></a>
        <a href="featured.html#league-lcp-2027-promotion" class="jump-card"><span>🌏 LCP 2027 Promotion &amp; LGC Finals</span><span class="badge tier-a">2 Matches</span></a>
        <a href="originated.html#league-komplettligaen-2026-autumn" class="jump-card"><span>🇳🇴 Komplettligaen 2026 Autumn</span><span class="badge tier-c">6 Matches</span></a>
        <a href="originated.html#league-prm-2nd-division-26-27-fall" class="jump-card"><span>🇩🇪 PRM 2nd Division 26-27 Fall</span><span class="badge tier-c">42 Matches</span></a>
        <a href="originated.html#league-prm-3rd-division-26-27-fall" class="jump-card"><span>🇩🇪 PRM 3rd Division 26-27 Fall</span><span class="badge tier-wfi">75 Matches</span></a>
        <a href="originated.html#league-rivals-league-season-2" class="jump-card"><span>🇸🇪 RIVALS LEAGUE Season 2</span><span class="badge tier-wfi">21 Matches</span></a>
        <a href="originated.html#league-4-nations-2026-halloween-heist" class="jump-card"><span>🇬🇧 4 Nations 2026 Halloween Heist</span><span class="badge tier-wfi">18 Matches</span></a>
        <a href="originated.html#league-tunisian-super-league-2026" class="jump-card"><span>🇹🇳 Tunisian Super League 2026</span><span class="badge tier-wfi">25 Matches</span></a>
        <a href="originated.html#league-arabian-league-2nd-division-2026-summer" class="jump-card"><span>🇲🇪 Arabian League 2nd Div &amp; ARC</span><span class="badge tier-d">11 Matches</span></a>
        <a href="originated.html#league-ligagg-celol-b-2026-split-2-playoffs" class="jump-card"><span>🇧🇷 LigaGG CELOL B Split 2 Playoffs</span><span class="badge tier-wfi">4 Matches</span></a>
        <a href="unresolved.html" class="jump-card"><span>⚠️ Unresolved Picks &amp; Limitations</span><span class="badge badge-med">53 Stale + TBDs</span></a>
      </div>

      <h3 style="margin:18px 0 8px;font-size:15.5px;color:#fff;">Top 5 Contrarian Value &amp; Disqualification Locks (Where Hotspawn Crowd % Is Wrong)</h3>
      <div class="alpha-grid">
        <div class="alpha-card">
          <div class="alpha-head"><span>Komplettligaen · Oct 22 15:00 UTC · #1059956</span><span class="badge badge-lock">+66.0% EDGE</span></div>
          <div class="alpha-pick">✓ Pick: DMG Esports (99.0% Forfeit Lock)</div>
          <p class="alpha-desc"><strong>Solid Gaming was officially removed from Komplettligaen</strong> after Round 2 (<a href="https://lol.fandom.com/wiki/Data:Komplettligaen/2026_Season/Autumn_Split" target="_blank" rel="noopener">Leaguepedia Data</a> already records this Oct 22 match as a <code>0-2</code> forfeit win for DMG NO, <code>ff=1</code>). Yet <strong>67% of Hotspawn users picked Solid Gaming</strong>!</p>
          <a href="#match-1059956" class="src-btn src-primary">Jump to #1059956 →</a>
        </div>
        <div class="alpha-card">
          <div class="alpha-head"><span>ARC 2026 Grand Final · Oct 23 16:00 UTC · #1082839</span><span class="badge badge-med">+34.8% EDGE</span></div>
          <div class="alpha-pick">✓ Pick: Levelers (67.8% Originated)</div>
          <p class="alpha-desc"><strong>67% of Hotspawn users picked MTN ESPORTS TEAM</strong>, unaware that <strong>Levelers is 4-0 (5-0 in games)</strong> and already swept MTN ESPORTS TEAM <code>2-0</code> in the Upper Bracket Final on Oct 16 (<a href="https://lol.fandom.com/wiki/Data:Arabian_Regional_Championship_2026/Qualifiers/LB-Li-SY-PS" target="_blank" rel="noopener">Leaguepedia</a>).</p>
          <a href="#match-1082839" class="src-btn src-primary">Jump to #1082839 →</a>
        </div>
        <div class="alpha-card">
          <div class="alpha-head"><span>Worlds 2026 R1 · Oct 23 20:00 UTC · #1067675</span><span class="badge badge-med">+28.2% EDGE</span></div>
          <div class="alpha-pick">✓ Pick: Anyone's Legend (66.2% Bookmaker Consensus)</div>
          <p class="alpha-desc">European fan bias drove <strong>62% of Hotspawn users to Karmine Corp</strong>, whereas Polymarket (<code>66¢</code> on <code>$147.2K</code> volume) and 6 sportsbooks (<code>1.37–1.50</code>) price LPL #3 <strong>Anyone's Legend at 66.2%</strong>.</p>
          <a href="#match-1067675" class="src-btn src-primary">Jump to #1067675 →</a>
        </div>
        <div class="alpha-card">
          <div class="alpha-head"><span>4 Nations Stage 2 · Oct 22 18:00 UTC · #1081630</span><span class="badge badge-lock">+52.6% EDGE</span></div>
          <div class="alpha-pick">✓ Pick: Inari Esports (85.6% Originated)</div>
          <p class="alpha-desc"><strong>Inari Esports is 3-0 in Stage 2 Group B</strong> (and already beat Abyssal Randoms <code>1-0</code> on Oct 19 while Abyssal Randoms is <code>0-3</code> in Group B), yet <strong>67% of Hotspawn users picked Abyssal Randoms</strong>!</p>
          <a href="#match-1081630" class="src-btn src-primary">Jump to #1081630 →</a>
        </div>
      </div>
    </section>

    <section class="card-section" id="unresolved-summary">
      <h2 class="section-title">
        <span>Unresolved Picks &amp; Limitations Summary (Executive Overview)</span>
        <a href="unresolved.html" class="src-btn src-primary">Open Full Unresolved &amp; Limitations Page →</a>
      </h2>
      <p style="margin-top:0;color:#cbd5e1;">
        Not every fixture listed in Hotspawn's tournament counters or schedule feeds can or should receive a conventional pre-match line. Our audit identified four distinct categories of unresolved or constrained fixtures (<a href="unresolved.html">full breakdown on the Unresolved &amp; Limitations subpage</a>):
      </p>
      <div class="kpi-grid" style="margin-bottom:0;">
        <div class="kpi-card">
          <div class="kpi-label">1. 53 Locked / Stale Filter-Bar Fixtures</div>
          <div class="kpi-sub" style="margin-top:6px;">Hotspawn's filter sidebar sums to <strong>264</strong> across 24 tournaments because <strong>53 completed/past fixtures</strong> (from Oct 1–21, including 12 in <em>Icelandic Esports League</em> and 6 in <em>Superstrike League</em>) never had their DB counter decremented after locking 5 minutes prior to start.</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">2. Unpromoted TBD vs TBD Bracket Slots</div>
          <div class="kpi-sub" style="margin-top:6px;">On <code>www.hotspawn.com/matches</code>, downstream playoff/group slots (e.g., <em>CELOL B</em> R2–Finals Oct 31–Nov 8, <em>LCP Promotion</em> FFA bracket Nov 10–13, <em>4 Nations</em> bye slots) list <code>Waiting for information vs Waiting for information</code>. Per our non-hallucination rule, probabilities are left blank until teams advance.</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">3. Disqualified &amp; Ghost Duplicate Cards</div>
          <div class="kpi-sub" style="margin-top:6px;"><code>#1059956</code> (<em>Solid Gaming vs DMG</em>) involves a disqualified team (0-2 FF lock); <code>#1079026</code> (<em>Reveal vs ex-A41G</em>) &amp; <code>#1079143</code> (<em>Pegasus vs Team Reds</em>) were already played earlier in the split; <code>#1079024</code> is a pre-reschedule duplicate of <code>#1082746</code>. All are documented on <a href="flagged.html">Flagged for Review</a>.</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">4. Structural Low-Tier Limitations</div>
          <div class="kpi-sub" style="margin-top:6px;">Tier-3/4 amateur ERLs (<em>PRM 3rd Div</em>, <em>4 Nations</em>, <em>RIVALS</em>, <em>Tunisian Super League</em>) have zero regulated sportsbook liquidity due to integrity/walkover risk, frequent unannounced sub stand-ins, and high Bo1 draft variance.</div>
        </div>
      </div>
    </section>

    <section class="card-section" id="tournament-directory">
      <h2 class="section-title">
        <span>Active Tournament Breakdown &amp; Quick Links (13 Active Leagues · 213 Matches)</span>
      </h2>
      <div class="table-wrap">
        <table class="data-table mobile-cards">
          <thead>
            <tr>
              <th>Tournament</th>
              <th>Tier &amp; Format</th>
              <th>Active DOM Cards</th>
              <th>Filter Bar Count</th>
              <th>Probability Source</th>
              <th>Highest-Probability Pick</th>
              <th>Navigation &amp; Official Links</th>
            </tr>
          </thead>
          <tbody>
            {''.join(tourn_summary_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="card-section" id="master-table">
      <h2 class="section-title">
        <span>All 213 Active Hotspawn LoL Pick'em Matches — Interactive Master Table</span>
        <span style="font-size:13px;color:var(--text-muted);">Showing <strong id="visible-count" style="color:#fff;">213</strong> of 213 matches</span>
      </h2>

      <div class="controls-bar">
        <input type="search" id="match-search" class="search-input" placeholder="Search team, tournament, or match ID (e.g., Gen.G, Solid Gaming, 1067878)...">
        <select id="tourn-filter" class="select-input" aria-label="Filter by Tournament">
          {''.join(tourn_options)}
        </select>
        <div class="pill-group">
          <button type="button" class="filter-btn active" data-filter-group="section" data-filter-val="ALL">All (213)</button>
          <button type="button" class="filter-btn" data-filter-group="section" data-filter-val="Closing Soon">Closing Soon · Oct 22 (27)</button>
          <button type="button" class="filter-btn" data-filter-group="section" data-filter-val="Upcoming">Upcoming · Oct 23–Nov 15 (186)</button>
        </div>
        <div class="pill-group">
          <button type="button" class="filter-btn active" data-filter-group="confidence" data-filter-val="ALL">All Tiers</button>
          <button type="button" class="filter-btn" data-filter-group="confidence" data-filter-val="Lock">Locks ≥78% ({len(locks)})</button>
          <button type="button" class="filter-btn" data-filter-group="confidence" data-filter-val="High">High 68–77%</button>
        </div>
        <div class="pill-group">
          <button type="button" class="filter-btn active" data-filter-group="special" data-filter-val="ALL">All</button>
          <button type="button" class="filter-btn" data-filter-group="special" data-filter-val="CONTRARIAN">Contrarian Edge ≥15%</button>
          <button type="button" class="filter-btn" data-filter-group="special" data-filter-val="FLAGGED">Flagged ({len(flagged)})</button>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table mobile-cards">
          <thead>
            <tr>
              <th>Schedule &amp; ID</th>
              <th>Tournament</th>
              <th>Matchup &amp; Official Records</th>
              <th>Obvious Pick</th>
              <th>Win Prob &amp; Fair Odds</th>
              <th>Hotspawn Crowd % (Ignored)</th>
              <th>Basis &amp; Official Source Links</th>
            </tr>
          </thead>
          <tbody>
            {render_match_table_rows(matches, include_tournament=True)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Executive Summary & All 213 LoL Picks", "index.html", body)


def build_featured_page(matches: list[dict]) -> str:
    feat_tourns = [
        "Worlds 2026 Main Event",
        "EM 2026 Summer Main Event",
        "LCP 2027 Promotion",
        "LGC Rising 2026 Playoffs",
    ]
    sections_html = []
    for t_name in feat_tourns:
        t_slug = slug_id(t_name)
        t_matches = [m for m in matches if m["tournament"] == t_name]
        sections_html.append(f"""
        <section class="card-section" id="league-{t_slug}">
          <h2 class="section-title">
            <span>{esc(t_name)} ({len(t_matches)} {'Match' if len(t_matches)==1 else 'Matches'})</span>
            {tier_badge(t_matches[0]['tier'], t_matches[0]['points'])}
          </h2>
          <div class="table-wrap">
            <table class="data-table mobile-cards">
              <thead>
                <tr>
                  <th>Schedule &amp; ID</th>
                  <th>Matchup &amp; Official Seed / Record</th>
                  <th>Obvious Pick</th>
                  <th>Win Prob &amp; Fair Odds</th>
                  <th>Hotspawn Crowd % (Ignored)</th>
                  <th>Bookmaker / Polymarket Lines &amp; Verified Sources</th>
                </tr>
              </thead>
              <tbody>
                {render_match_table_rows(t_matches, include_tournament=False)}
              </tbody>
            </table>
          </div>
        </section>
        """)

    body = f"""
    <section class="card-section">
      <h2 class="section-title">
        <span>S &amp; A Tier Featured Matches — External Bookmaker &amp; Polymarket Consensus (11 Matches)</span>
        <span class="badge tier-s">30 PTS &amp; 20 PTS HIGH-VALUE SLATE</span>
      </h2>
      <p style="margin-top:0;color:#cbd5e1;">
        Tier S (30 points per correct pick) and Tier A (20 points per correct pick) carry <strong>2x to 3x the leaderboard weight</strong> of standard regional matches on Hotspawn Pick'ems. For all 8 <strong>Worlds 2026 Swiss Round 1</strong> matches and the <strong>EMEA Masters 2026 Summer Grand Final</strong>, probabilities are derived directly from de-vigged multi-bookmaker decimal odds (<a href="https://egamersworld.com/lol/bets" target="_blank" rel="noopener">Vave, Thunderpick, Rainbet, Underdog, CocoBet</a>, <a href="https://tips.gg/article/worlds-championship-2026-play-in-recap-swiss-stage-round-1-betting-predictions-tournament-winner-event-story/" target="_blank" rel="noopener">SpinBetter, GG.bet</a>) and live prediction market orderbooks (<a href="https://polymarket.com/esports/league-of-legends/worlds" target="_blank" rel="noopener">Polymarket Worlds 2026</a>). For the November 11 <strong>LCP 2027 Promotion</strong> and October 27 <strong>LGC Rising 2026 Grand Final</strong>, lines are originated from official Riot Championship Points and playoff map differentials.
      </p>
    </section>
    {''.join(sections_html)}
    """
    return page_shell("S & A Tier Featured Bookmaker Picks (11)", "featured.html", body)


def build_originated_page(matches: list[dict], recon: list[dict]) -> str:
    orig_tourns = [
        "Komplettligaen 2026 Autumn",
        "4 Nations 2026 Halloween Heist",
        "Arabian League 2nd Division 2026 Summer",
        "Arabian Regional Championship 2026: Lebanon-Libya-Syria-Palestine",
        "LigaGG CELOL B 2026 Split 2 Playoffs",
        "RIVALS LEAGUE Season 2",
        "Tunisian Super League 2026",
        "PRM 2nd Division 26-27 Fall",
        "PRM 3rd Division 26-27 Fall",
    ]
    nav_pills = []
    sections_html = []
    for t_name in orig_tourns:
        t_slug = slug_id(t_name)
        t_matches = [m for m in matches if m["tournament"] == t_name]
        nav_pills.append(f'<a href="#league-{t_slug}" class="jump-card"><span>{esc(t_name)}</span><span class="badge tier-c">{len(t_matches)} Picks</span></a>')
        sections_html.append(f"""
        <section class="card-section" id="league-{t_slug}">
          <h2 class="section-title">
            <span>{esc(t_name)} ({len(t_matches)} Matches)</span>
            <span>{tier_badge(t_matches[0]['tier'], t_matches[0]['points'])} · {esc(t_matches[0]['format'])}</span>
          </h2>
          <div class="table-wrap">
            <table class="data-table mobile-cards">
              <thead>
                <tr>
                  <th>Schedule &amp; ID</th>
                  <th>Matchup &amp; Official Leaguepedia Record</th>
                  <th>Obvious Pick</th>
                  <th>Originated Prob &amp; Odds</th>
                  <th>Hotspawn Crowd % (Ignored)</th>
                  <th>H2H / Basis &amp; Official Source Links</th>
                </tr>
              </thead>
              <tbody>
                {render_match_table_rows(t_matches, include_tournament=False)}
              </tbody>
            </table>
          </div>
        </section>
        """)

    body = f"""
    <section class="card-section">
      <h2 class="section-title">
        <span>Originated Low-Tier Regional LoL Picks (202 Matches Across 9 Regional Leagues)</span>
        <span class="badge badge-high">BRADLEY-TERRY / LOG5 ORIGINATION MODEL</span>
      </h2>
      <p style="margin-top:0;color:#cbd5e1;">
        Because minor European, MENA, and Brazilian semi-pro leagues (<em>Prime League 2nd/3rd Division</em>, <em>Komplettligaen</em>, <em>RIVALS LEAGUE</em>, <em>4 Nations</em>, <em>Tunisian Super League</em>, <em>Arabian League 2nd Division</em>, <em>CELOL Série B</em>) are not listed on Polymarket or major sportsbooks, we originated win probabilities for all 202 matches directly from official <a href="https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki" target="_blank" rel="noopener">Leaguepedia</a> raw <code>Data:</code> match schedules and standings:
      </p>
      <ul style="color:#cbd5e1;font-size:13.5px;margin-bottom:14px;">
        <li><strong>Latent Game Strength (<code>S_i</code>):</strong> Computed from verified current-split series wins/losses (<code>SW-SL</code>) and game wins/losses (<code>GW-GL</code>) with Bayesian Laplace smoothing (<code>Beta(2,2)</code> for games, <code>Beta(1.5,1.5)</code> for series): <code>S_i = 0.60·(GW+2)/(GW+GL+4) + 0.40·(SW+1.5)/(SW+SL+3) + Prior_i</code>.</li>
        <li><strong>Head-to-Head &amp; Series Format Scaling:</strong> Pairwise single-game win probability <code>p_game = S_1 / (S_1 + S_2) + H2H_Adjustment</code> is converted to Best-of-3 series win probability via <code>P(Bo3) = p²·(1 + 2·(1 - p))</code>.</li>
        <li><strong>Forfeit &amp; Disqualification Override:</strong> Where an official league ruling disqualifies a team (e.g., <strong>Solid Gaming</strong> in <em>Komplettligaen</em> <code>#1059956</code>), the active opponent is assigned a <strong>99.0% Forfeit Lock</strong>.</li>
      </ul>
      <div class="jump-grid">
        {''.join(nav_pills)}
      </div>
    </section>
    {''.join(sections_html)}
    """
    return page_shell("Originated Low-Tier Regional LoL Picks (202)", "originated.html", body)


def build_unresolved_page(recon: list[dict]) -> str:
    recon_rows = []
    for r in recon:
        status_badge = '<span class="badge badge-lock">ACTIVE IN LOBBY</span>' if r["active_dom_count"] > 0 else '<span class="badge badge-med">0 ACTIVE (STALE ONLY)</span>'
        recon_rows.append(f"""
        <tr>
          <td data-label="Tournament"><strong>{esc(r["name"])}</strong></td>
          <td data-label="Status">{status_badge}</td>
          <td data-label="Tier &amp; Format">{tier_badge(r["tier"], r["points"])} · {esc(r["format"])}</td>
          <td data-label="Filter Bar Count"><strong>{r["filter_count"]}</strong></td>
          <td data-label="Active DOM Cards"><strong>{r["active_dom_count"]}</strong> (CS: {r["closing_soon_count"]}, Up: {r["upcoming_count"]})</td>
          <td data-label="Stale / Locked">{r["locked_or_stale_count"]}</td>
          <td data-label="DOM Extra Duplicates">{r["dom_extra_duplicates"]}</td>
          <td data-label="Official Sources">
            <a href="https://www.hotspawn.com/league-of-legends/tournament/{esc(r['hs_slug'])}" target="_blank" rel="noopener" class="src-btn">Hotspawn ↗</a>
            <a href="{esc(r['lp_url'])}" target="_blank" rel="noopener" class="src-btn src-primary">Official Wiki ↗</a>
          </td>
        </tr>
        """)

    # Unpromoted TBD vs TBD bracket slots table (blank probabilities per non-hallucination rule)
    tbd_rows = [
        ("Oct 22, 18:00–20:00 UTC", "4 Nations 2026 Halloween Heist", "Group C & D Bye Slots (6 Slots)", "Waiting for information vs Waiting for information", "", "", "UNVERIFIED_TBD_BYE_SLOT", "Group C & D only have 3 teams (BDG, Ruddy Ultras, HL Tauri; Absolved, PNS, The Bandits UK) after Impel withdrew; 4th-team slots are empty byes.", "https://www.hotspawn.com/league-of-legends/tournament/4-nations-2026-halloween-heist", "https://lol.fandom.com/wiki/4_Nations/2026_Season/Halloween_Heist"),
        ("Oct 23–28, 16:00–17:00 UTC", "RIVALS LEAGUE Season 2", "Playoff Quarterfinal / Semifinal Placeholders (24 Slots)", "Waiting for information vs Waiting for information", "", "", "UNVERIFIED_TBD_BRACKET", "Group A & B regular season runs through Nov 1; playoff bracket seeding is undetermined until Group Stage concludes.", "https://www.hotspawn.com/league-of-legends/tournament/rivals-league-season-2", "https://lol.fandom.com/wiki/RIVALS_LEAGUE/2026_Season/Season_2"),
        ("Oct 31 – Nov 08, 15:00 UTC", "LigaGG CELOL B 2026 Split 2 Playoffs", "Lower Bracket R2/R3/R4 & Grand Finals (6 Slots)", "Waiting for information vs Waiting for information", "", "", "UNVERIFIED_TBD_BRACKET", "Participants depend on outcomes of Oct 24–25 Round 1/2 matches (#1081083–#1081086). Left blank until matchups are set.", "https://www.hotspawn.com/league-of-legends/tournament/ligagg-celol-b-2026-split-2-playoffs", "https://lol.fandom.com/wiki/LigaGG/CELOL_S%C3%A9rie_B/2026_Season/Split_2_Playoffs"),
        ("Nov 10–13, 05:00–09:00 UTC", "LCP 2027 Promotion", "Free-for-All Bracket R1, R2 & Finals (4 Slots)", "DetonatioN FocusMe / TBD vs TBD", "", "", "UNVERIFIED_TBD_BRACKET", "5-team Free-for-All bracket pairings (DFM, Saigon Warriors, FENNEL, Gromp Esports, Wildcard #1) are not yet drawn on Leaguepedia.", "https://www.hotspawn.com/league-of-legends/tournament/lcp-2027-promotion", "https://lol.fandom.com/wiki/LCP/2027_Season/Promotion"),
        ("Oct 26 – Nov 21, 18:00–20:00 UTC", "4 Nations 2026 Halloween Heist", "Stage 2 Day 5 (Oct 26) & Stage 3 Playoffs (18+ Slots)", "Named Day 5 Teams / Playoff TBDs", "", "", "NOT_YET_IN_PICKEMS_LOBBY", "Listed on Hotspawn's tournament schedule page (#1081651–#1081672) but not yet promoted to play.hotspawn.com/lol-pickems.", "https://www.hotspawn.com/league-of-legends/tournament/4-nations-2026-halloween-heist", "https://lol.fandom.com/wiki/4_Nations/2026_Season/Halloween_Heist"),
    ]
    tbd_html = []
    for dt, trn, stg, mup, p1, p2, flg, note, hs_u, lp_u in tbd_rows:
        tbd_html.append(f"""
        <tr class="row-flagged">
          <td data-label="Schedule Window"><strong>{esc(dt)}</strong></td>
          <td data-label="Tournament">{esc(trn)}<div class="sub-meta">{esc(stg)}</div></td>
          <td data-label="Participants">{esc(mup)}</td>
          <td data-label="Originated Win Prob"><em>{esc(p1)}</em> <span class="badge badge-med">LEFT BLANK (UNVERIFIED)</span></td>
          <td data-label="Recommended Pick"><em>{esc(p2)}</em> <span class="flag-inline"><a>⚠ {esc(flg)}</a></span></td>
          <td data-label="Limitation &amp; Verification Note">{esc(note)}</td>
          <td data-label="Official Sources">
            <a href="{esc(hs_u)}" target="_blank" rel="noopener" class="src-btn">Hotspawn ↗</a>
            <a href="{esc(lp_u)}" target="_blank" rel="noopener" class="src-btn src-primary">Leaguepedia ↗</a>
          </td>
        </tr>
        """)

    body = f"""
    <section class="card-section">
      <h2 class="section-title">
        <span>Unresolved Picks, TBD Bracket Placeholders &amp; Origination Limitations</span>
        <span class="badge badge-med">STRICT NON-HALLUCINATION AUDIT</span>
      </h2>
      <p style="margin-top:0;color:#cbd5e1;">
        A core requirement of our origination pipeline is <strong>never inferring or hallucinating unverified values</strong>. Whenever a fixture on Hotspawn has undetermined participants (<code>Waiting for information vs Waiting for information</code>) or has already locked/completed in the past while still inflating the filter-bar counter, we explicitly document the limitation and leave unverified TBD probabilities blank until official sources confirm the participants.
      </p>

      <h3 style="color:#fff;font-size:16px;margin:16px 0 8px;">Key Limitations When Generating Picks for Unresolved &amp; Low-Tier LoL Matches</h3>
      <ol style="color:#cbd5e1;font-size:13.5px;line-height:1.6;">
        <li><strong>Zero Regulated Sportsbook Coverage Below EMEA Masters / Tier-1 ERLs:</strong> Regulated bookmakers and Polymarket do not offer markets on German Prime League 2nd/3rd Division, Norwegian Komplettligaen, Swedish RIVALS League, UK 4 Nations, Tunisian Super League, or Brazilian CELOL Série B due to low betting liquidity and amateur match-integrity risks. All 202 matches in these leagues require statistical origination from official tournament records.</li>
        <li><strong>High Walkover / Forfeit (<code>ff</code>) &amp; Disqualification Rates in Amateur Online Leagues:</strong> Semi-pro teams frequently forfeit matches due to roster lock violations or scheduling conflicts—for example, <strong>Solid Gaming</strong> was removed from <em>Komplettligaen 2026 Autumn</em> (forfeiting <code>#1059956</code> vs DMG Esports), <strong>Team Reds</strong> had two 2-1/2-0 victories overturned to <code>0-2</code> forfeits in <em>Arabian League 2nd Division</em> for fielding an ineligible player, and <em>CELOL Série B</em> had 15+ regular-season forfeits.</li>
        <li><strong>Hotspawn Database Desynchronization (Stale Locks, Ghost Duplicates &amp; Misattributed Teams):</strong> Hotspawn's ingestion pipeline frequently creates new fixture IDs when matches are rescheduled or teams rename (e.g., <code>ex-A41G</code> → <code>reGOLD eSport</code>; <code>Victorious Demons</code> → <code>Team VDS</code>) without deleting the superseded fixture ID, and auto-maps abbreviations like Swiss team <code>PvB Nation</code> to defunct Vietnamese VCS team <code>Phong Vũ Buffalo</code>.</li>
        <li><strong>Best-of-1 Variance in 4 Nations &amp; Tunisian Super League:</strong> Single-game (Bo1) amateur matches carry significantly higher draft and early-game variance than Best-of-3 (PRM, Komplettligaen, RIVALS, CELOL B) or Best-of-5 (EMEA Masters, LCP Promotion, LGC Rising Finals) series, capping realistic single-game confidence below ~88% unless a team is disqualified.</li>
      </ol>
    </section>

    <section class="card-section" id="tbd-placeholders">
      <h2 class="section-title">
        <span>Unresolved TBD / Bracket Placeholder Fixtures (Left Blank &amp; Flagged as Unverified)</span>
      </h2>
      <div class="table-wrap">
        <table class="data-table mobile-cards">
          <thead>
            <tr>
              <th>Schedule Window</th>
              <th>Tournament &amp; Stage</th>
              <th>Listed Participants</th>
              <th>Originated Win Prob</th>
              <th>Recommended Pick</th>
              <th>Limitation &amp; Verification Note</th>
              <th>Official Sources</th>
            </tr>
          </thead>
          <tbody>
            {''.join(tbd_html)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="card-section" id="reconciliation-264">
      <h2 class="section-title">
        <span>Complete Reconciliation of All 24 Filter-Bar Tournaments (264 Filter-Bar Sum vs 213 Active DOM Cards)</span>
      </h2>
      <p style="margin-top:0;color:#cbd5e1;">
        Formula: <code>264 (Filter-Bar Checkboxes) - 53 (Locked/Completed Past Fixtures) + 2 (PRM 2nd Div Oct 23 Unremoved Duplicates #1079024 &amp; #1079026) = 213 Active Pickable DOM Cards (27 Closing Soon + 186 Upcoming)</code>.
      </p>
      <div class="table-wrap">
        <table class="data-table mobile-cards">
          <thead>
            <tr>
              <th>Tournament Name</th>
              <th>Lobby Status</th>
              <th>Tier &amp; Format</th>
              <th>Filter Bar Count</th>
              <th>Active DOM Cards</th>
              <th>Locked / Stale Count</th>
              <th>Extra DOM Duplicates</th>
              <th>Official Sources</th>
            </tr>
          </thead>
          <tbody>
            {''.join(recon_rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Unresolved Picks & Origination Limitations", "unresolved.html", body)


def build_flagged_page(matches: list[dict]) -> str:
    flagged = [m for m in matches if m["flagged"]]
    rows = []
    for m in flagged:
        mid = m["id"]
        rows.append(f"""
        <tr id="flag-{mid}" class="row-flagged">
          <td data-label="Match ID &amp; Date">
            <strong>#{mid}</strong>
            <div class="sub-meta">{esc(m["date"])} · {esc(m["time_et"])} ET</div>
            <div class="sub-meta"><code>{esc(m["utc_iso"])}</code></div>
          </td>
          <td data-label="Tournament">{esc(m["tournament"])}</td>
          <td data-label="Listed Matchup"><strong>{esc(m["team1"])}</strong> vs <strong>{esc(m["team2"])}</strong></td>
          <td data-label="Irregularity Flag"><span class="flag-inline"><a>⚠ {esc(m["flag_type"])}</a></span></td>
          <td data-label="Recommended Pick &amp; Prob">
            <strong>✓ {esc(m["pick"])} ({m["pick_prob"]:.1f}%)</strong>
            <div class="sub-meta">Crowd: {m["hs_pct1"]}% / {m["hs_pct2"]}%</div>
          </td>
          <td data-label="Audit Explanation &amp; Official Evidence">{esc(m["flag_reason"])}</td>
          <td data-label="Official Sources">
            <a href="{esc(m['hs_match_url'])}" target="_blank" rel="noopener" class="src-btn">Hotspawn #{mid} ↗</a>
            <a href="{esc(m['primary_source_url'])}" target="_blank" rel="noopener" class="src-btn src-primary">{esc(m['primary_source_name'])} ↗</a>
            <a href="{esc(m['secondary_source_url'])}" target="_blank" rel="noopener" class="src-btn">{esc(m['secondary_source_name'])} ↗</a>
          </td>
        </tr>
        """)

    body = f"""
    <section class="card-section">
      <h2 class="section-title">
        <span>Flagged for Review — Irregularities, Disqualifications, Duplicates &amp; Entity Misattributions ({len(flagged)} Active Cards)</span>
        <span class="badge badge-med">COMPLETE DATA INTEGRITY AUDIT</span>
      </h2>
      <p style="margin-top:0;color:#cbd5e1;">
        During our line-by-line verification of all 213 active Pick'em cards against <a href="https://www.hotspawn.com/matches" target="_blank" rel="noopener">Hotspawn's Match Feed</a> and <a href="https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki" target="_blank" rel="noopener">Leaguepedia's Official Data Pages</a>, we identified <strong>{len(flagged)} active cards</strong> with data irregularities (plus the 53 stale filter-bar fixtures and unpromoted TBD slots documented on <a href="unresolved.html">Unresolved &amp; Limitations</a>):
      </p>
      <ul style="color:#cbd5e1;font-size:13.5px;line-height:1.6;">
        <li><strong><code>TEAM_DISQUALIFIED_FORFEIT</code> (1 Card — <code>#1059956</code>):</strong> <em>Solid Gaming</em> was officially removed from <em>Komplettligaen 2026 Autumn</em> and forfeited <code>0-2</code> to <em>DMG Esports</em>, yet Hotspawn still lists the match as pickable and 67% of users picked Solid Gaming.</li>
        <li><strong><code>ALREADY_PLAYED_GHOST_DUPLICATE</code> / <code>ALREADY_PLAYED_STALE</code> (2 Cards — <code>#1079026</code>, <code>#1079143</code>):</strong> <em>Reveal Multigaming vs ex-A41G</em> (<code>#1079026</code>, Oct 23) was already played on Oct 20 under <code>reGOLD eSport</code> (<code>#1079850</code>, 0-2); <em>Pegasus Esports vs Team Reds</em> (<code>#1079143</code>, Oct 25) was already played in Week 2 on Oct 10 (Team Reds won 2-1).</li>
        <li><strong><code>RESCHEDULED_GHOST_DUPLICATE</code> / <code>RESCHEDULED_DUPLICATE_SLOT</code> (5 Cards — <code>#1079024</code>, <code>#1079703</code>, <code>#1080902</code>, <code>#1079922</code>, <code>#1079923</code>):</strong> <code>#1079024</code> (Oct 23) was rescheduled to Nov 3 (<code>#1082746</code>), leaving both cards active in the Pick'em lobby and causing <em>PRM 2nd Division</em> to render 42 DOM cards vs 40 in the filter bar.</li>
        <li><strong><code>TEAM_ALIAS_DUPLICATE</code> &amp; <code>TEAM_RENAME_STALE_ALIAS</code> (6 Cards — <code>#1082105</code>, <code>#1082106</code>, <code>#1082107</code>, <code>#1079035</code>, <code>#1079052</code>, <code>#1079061</code>):</strong> Duplicate fixtures created by team tag changes (<code>Victorious Demons</code> → <code>Team VDS</code> in Arabian League 2nd Div; <code>ex-A41G</code> → <code>reGOLD eSport</code> in PRM 2nd Div).</li>
        <li><strong><code>MISATTRIBUTED_TEAM_ENTITY</code> (11 Cards):</strong> Swiss team <code>PvB Nation</code> in <em>PRM 2nd Division</em> is misattributed to defunct Vietnamese VCS team <code>Phong Vũ Buffalo</code>; German <em>PRM 3rd Division</em> Group B team <code>Rich Gang</code> uses Norwegian <code>Rich NO</code> template metadata.</li>
        <li><strong><code>REVERSED_SLUG</code> (3 Cards — <code>#1074665</code>, <code>#1079145</code>, <code>#1079057</code>):</strong> The Pick'em card displays Team A vs Team B while the official match URL slug reverses them (Team B vs Team A).</li>
        <li><strong><code>MARKET_SPLIT</code> (1 Card — <code>#1081205</code>):</strong> Traditional sportsbooks favor <em>Solary</em> (1.75–1.84) while Polymarket (53¢) and Thunderpick (1.68) favor <em>Galions</em>.</li>
      </ul>
      <div class="table-wrap">
        <table class="data-table mobile-cards">
          <thead>
            <tr>
              <th>Match ID &amp; Date</th>
              <th>Tournament</th>
              <th>Listed Matchup</th>
              <th>Irregularity Flag</th>
              <th>Recommended Pick</th>
              <th>Audit Explanation &amp; Official Evidence</th>
              <th>Official Sources</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </section>
    """
    return page_shell("Flagged for Review — Data Integrity Audit", "flagged.html", body)


def build_automation_page() -> str:
    body = """
    <section class="card-section">
      <h2 class="section-title">
        <span>Reverse-Engineering Hotspawn Pick'ems &amp; 4–8 Hour Automation Architecture</span>
        <span class="badge badge-lock">CRON: EVERY 6 HOURS (00:00, 06:00, 12:00, 18:00 UTC)</span>
      </h2>
      <p style="margin-top:0;color:#cbd5e1;">
        To keep all League of Legends Pick'em probabilities, match locks, and originated regional lines continuously updated within the required <strong>4–8 hour window</strong>, we reverse-engineered Hotspawn's dual-stack architecture and implemented an automated GitHub Actions pipeline (<a href="https://github.com/karagemop466-tech/LOLHOTSPAWN4/blob/main/.github/workflows/update-pickems.yml" target="_blank" rel="noopener"><code>.github/workflows/update-pickems.yml</code></a> + <code>scripts/update_pickems.py</code>).
      </p>

      <h3 style="color:#fff;font-size:16px;margin:16px 0 8px;">1. Reverse-Engineered Hotspawn Endpoints &amp; Architecture</h3>
      <div class="table-wrap">
        <table class="data-table mobile-cards">
          <thead>
            <tr>
              <th>Endpoint / Surface</th>
              <th>URL Pattern</th>
              <th>Authentication &amp; Payload Structure</th>
              <th>Role in 4–8h Pipeline</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td data-label="Surface"><strong>LoL Pick'em SSR Lobby</strong></td>
              <td data-label="URL"><a href="https://play.hotspawn.com/lol-pickems" target="_blank" rel="noopener"><code>https://play.hotspawn.com/lol-pickems</code></a></td>
              <td data-label="Structure">Public SSR HTML containing all active <code>id="pickem-card-&lt;id&gt;"</code> DOM cards, tier/tournament filter counts, point badges (30/20/10 PTS), EDT/EST timestamps, and crowd pick %.</td>
              <td data-label="Role">Primary source of truth for which LoL fixtures are currently open for user picks in the Pick'em lobby.</td>
            </tr>
            <tr>
              <td data-label="Surface"><strong>WP REST Pick'em Fixture API</strong></td>
              <td data-label="URL"><a href="https://www.hotspawn.com/wp-json/pickem/v1/fixture/1067878" target="_blank" rel="noopener"><code>https://www.hotspawn.com/wp-json/pickem/v1/fixture/&lt;id&gt;</code></a></td>
              <td data-label="Structure">Public JSON returning <code>fixture_id</code>, <code>total_picks</code>, and per-team <code>count</code> &amp; <code>percentage</code>.</td>
              <td data-label="Role">Polled to track crowd pick volume &amp; contrarian fade edges (never used as win probability).</td>
            </tr>
            <tr>
              <td data-label="Surface"><strong>WP REST Tournaments API</strong></td>
              <td data-label="URL"><a href="https://www.hotspawn.com/wp-json/hotspawn/v1/tournaments?game=league-of-legends&page=1" target="_blank" rel="noopener"><code>/wp-json/hotspawn/v1/tournaments?game=league-of-legends</code></a></td>
              <td data-label="Structure">Paginated JSON returning all 27 LoL tournaments, WordPress post IDs, slugs, tiers, start/end UNIX timestamps, and participant rosters.</td>
              <td data-label="Role">Maps tournament slugs and metadata across Hotspawn's database.</td>
            </tr>
            <tr>
              <td data-label="Surface"><strong>Hotspawn UTC Match Feed &amp; Tournament Pages</strong></td>
              <td data-label="URL"><a href="https://www.hotspawn.com/matches" target="_blank" rel="noopener"><code>https://www.hotspawn.com/matches</code></a></td>
              <td data-label="Structure">SSR HTML with exact UTC timestamps and canonical match slugs (<code>/matches/&lt;slug&gt;-&lt;id&gt;</code>).</td>
              <td data-label="Role">Verifies exact UTC start times (resolving US EDT/EST Daylight Saving shifts on Nov 1) and canonical URLs.</td>
            </tr>
            <tr>
              <td data-label="Surface"><strong>Leaguepedia Raw Data API</strong></td>
              <td data-label="URL"><a href="https://lol.fandom.com/wiki/Data:Komplettligaen/2026_Season/Autumn_Split?action=raw" target="_blank" rel="noopener"><code>https://lol.fandom.com/wiki/Data:&lt;Tournament&gt;?action=raw</code></a></td>
              <td data-label="Structure">Structured MediaWiki <code>{{MatchSchedule}}</code> templates with game scores, points, Riot platform game IDs (<code>LOLTMNT05_*</code>), and forfeit/DQ footnotes.</td>
              <td data-label="Role">Feeds our Bradley-Terry / Log5 origination engine for all 202 low-tier regional LoL matches.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3 style="color:#fff;font-size:16px;margin:20px 0 8px;">2. Automated 6-Hour Update Workflow (<code>.github/workflows/update-pickems.yml</code>)</h3>
      <p style="color:#cbd5e1;font-size:13.5px;">
        Our GitHub Actions workflow executes automatically every 6 hours (<code>cron: '0 */6 * * *'</code> — within the 4–8 hour target window) as well as on every push to <code>main</code> and manual <code>workflow_dispatch</code>:
      </p>
      <pre style="background:#0b0f17;border:1px solid var(--border);border-radius:8px;padding:14px;overflow-x:auto;color:#7dd3fc;font-size:12.5px;">name: Update Hotspawn LoL Pick'ems &amp; Deploy Pages
on:
  schedule:
    - cron: '0 */6 * * *'   # Runs every 6 hours (4-8h window)
  workflow_dispatch:
  push:
    branches: [ main ]

 jobs:
  update-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run Hotspawn LoL Pick'ems Scraper &amp; Origination Engine
        run: python3 scripts/update_pickems.py
      - name: Commit Updated Dataset &amp; Dashboards if Changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          if ! git diff --quiet; then
            git add data/ *.html assets/
            git commit -m "chore(auto): refresh Hotspawn LoL Pick'ems probabilities and site"
            git push origin HEAD:main || true
          fi
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      - uses: actions/deploy-pages@v4</pre>
    </section>
    """
    return page_shell("API Reverse Engineering & 4–8h Automation", "automation.html", body)


def main():
    with open("data/matches_active_213.json", encoding="utf-8") as f:
        matches = json.load(f)
    with open("data/filter_bar_reconciliation_264.json", encoding="utf-8") as f:
        recon = json.load(f)

    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    (assets_dir / "styles.css").write_text(build_css().strip() + "\n", encoding="utf-8")
    (assets_dir / "app.js").write_text(build_js().strip() + "\n", encoding="utf-8")

    Path("index.html").write_text(build_index_page(matches, recon), encoding="utf-8")
    Path("featured.html").write_text(build_featured_page(matches), encoding="utf-8")
    Path("originated.html").write_text(build_originated_page(matches, recon), encoding="utf-8")
    Path("unresolved.html").write_text(build_unresolved_page(recon), encoding="utf-8")
    Path("flagged.html").write_text(build_flagged_page(matches), encoding="utf-8")
    Path("automation.html").write_text(build_automation_page(), encoding="utf-8")
    Path(".nojekyll").write_text("", encoding="utf-8")

    print("Successfully built all 6 HTML pages + CSS/JS assets:")
    for p in ["index.html", "featured.html", "originated.html", "unresolved.html", "flagged.html", "automation.html"]:
        sz = Path(p).stat().st_size
        print(f"  - {p:18s}: {sz:,} bytes")


if __name__ == "__main__":
    main()
