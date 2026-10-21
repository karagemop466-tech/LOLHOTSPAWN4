"""Match Hotspawn LoL fixtures against external lines and produce the
published dataset.

Rules (see methodology.html):
  * Pick basis "market-line": a public per-match market (Polymarket
    "Match Winner") prices both teams. Probabilities are the market mids
    exactly as reported by the source (no adjustment). Pick = higher side.
  * Pick basis "derived-estimate": no per-match market, but both teams have
    open tournament-futures markets (Kalshi KXLOL / Polymarket futures) for
    the SAME tournament. We originate our own line with a transparent
    ratio model:  p(A) = f(A) / (f(A) + f(B)), where f = futures mid price.
    Clearly labeled, low confidence, and listed on the Flagged page.
  * Otherwise: UNRESOLVED. No probability, no pick. Flagged with the reason.
  * Hotspawn's own crowd "picked %" is never used as a probability signal
    (project requirement). It is stored only as context.
  * Pinnacle matchups are used as a coverage flag (a pro book lists this
    match) because no public price endpoint exists (verified 2026-10-21).

Output: data/matches.json (single canonical dataset the site renders).
"""

import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

TIME_WINDOW_MATCH = timedelta(hours=36)   # book match market vs fixture start
TIME_WINDOW_LEAGUE = timedelta(days=3)    # event start fallback
PINNACLE_WINDOW = timedelta(hours=24)     # pinnacle coverage check


def parse_pm_game_start(s):
    # formats seen: "2026-10-23 20:00:00+00" or ISO
    if not s:
        return None
    s2 = str(s).strip()
    if " " in s2 and "T" not in s2:
        s2 = s2.replace(" ", "T", 1)
    return common.parse_iso(s2)


def fmt_pct(p):
    return None if p is None else round(p * 100, 1)


def find_polymarket_match_line(fixture, pm_markets):
    """Find an open two-outcome market whose outcomes are the two fixture teams."""
    fa = fixture["team_a"]["name"]
    fb = fixture["team_b"]["name"]
    t0 = common.parse_iso(fixture["start_utc"])
    best = None
    best_key = None
    for m in pm_markets:
        if m["closed"]:
            continue
        outs = m["outcomes"]
        if len(outs) != 2:
            continue
        # order-agnostic team matching
        if (common.teams_match(outs[0], fa) and common.teams_match(outs[1], fb)) or \
           (common.teams_match(outs[0], fb) and common.teams_match(outs[1], fa)):
            t1 = parse_pm_game_start(m.get("game_start")) or \
                common.parse_iso(m.get("event_start"))
            if t0 and t1:
                delta = abs((t1 - t0).total_seconds()) / 3600.0
                window = TIME_WINDOW_MATCH.total_seconds() / 3600.0
                if t0.date() == t1.date():
                    window = max(window, 48)  # same-day is always acceptable
                else:
                    window = TIME_WINDOW_LEAGUE.total_seconds() / 3600.0
                if delta > window:
                    continue
                key = (delta, -(m.get("volume") or 0))
            else:
                key = (9999, -(m.get("volume") or 0))
            if best_key is None or key < best_key:
                best_key = key
                best = m
    return best, best_key


def find_kalshi_futures(fixture, kl_markets):
    """Open futures markets for each fixture team in the same Kalshi event."""
    fa = fixture["team_a"]["name"]
    fb = fixture["team_b"]["name"]
    ma = mb = None
    for m in kl_markets:
        if m.get("mid") in (None, 0) or m.get("status") != "active":
            continue
        sub = m.get("subtitle") or ""
        if common.teams_match(sub, fa) and ma is None:
            ma = m
        elif common.teams_match(sub, fb) and mb is None:
            mb = m
    if ma and mb and ma["event_ticker"] == mb["event_ticker"]:
        return ma, mb
    return None, None


def find_pinnacle_coverage(fixture, pk_matchups):
    fa = fixture["team_a"]["name"]
    fb = fixture["team_b"]["name"]
    t0 = common.parse_iso(fixture["start_utc"])
    for m in pk_matchups:
        if not ((common.teams_match(m["home"], fa) and common.teams_match(m["away"], fb)) or
                (common.teams_match(m["home"], fb) and common.teams_match(m["away"], fa))):
            continue
        t1 = common.parse_iso(m.get("start_time"))
        if t0 and t1 and abs(t1 - t0) > PINNACLE_WINDOW:
            continue
        return m
    return None


def build_match(fx, pm, kl, pk, manifest):
    start = common.ms_epoch_to_iso(fx.get("scheduled_start_time"))
    lock = common.ms_epoch_to_iso(fx.get("lock_time"))
    fixture = {
        "hotspawn_id": str(fx.get("id")),
        "competition_id": str(fx.get("competition_id")),
        "tournament": fx.get("competition_name") or "",
        "start_utc": start,
        "lock_utc": lock,
        "tier": fx.get("tier"),
        "stage": fx.get("stage"),
        "offered_points": fx.get("offered_points"),
        "game_multiplier": (fx.get("points_breakdown") or {}).get("game_multiplier"),
        "team_a": {
            "name": fx.get("participants0_name"),
            "hotspawn_team_id": str(fx.get("participants0_id")),
            "crowd_picked_pct": fx.get("participants0_picked_percent"),
            "logo_url": "https://phpstack-1372681-6459848.cloudwaysapps.com/teams/%s.svg" % fx.get("participants0_id"),
        },
        "team_b": {
            "name": fx.get("participants1_name"),
            "hotspawn_team_id": str(fx.get("participants1_id")),
            "crowd_picked_pct": fx.get("participants1_picked_percent"),
            "logo_url": "https://phpstack-1372681-6459848.cloudwaysapps.com/teams/%s.svg" % fx.get("participants1_id"),
        },
    }
    lines = []
    flags = []
    pm_line = None
    try:
        pm_line, key = find_polymarket_match_line(fixture, pm)
    except Exception as e:
        flags.append("polymarket-match-search-error: %s" % e)

    if pm_line:
        fa = fixture["team_a"]["name"]
        outs = pm_line["outcomes"]
        if common.teams_match(outs[0], fa):
            pa, pb = pm_line["prices"][0], pm_line["prices"][1]
            order = "ab"
        else:
            pa, pb = pm_line["prices"][1], pm_line["prices"][0]
            order = "ba"
        lines.append({
            "source": "Polymarket",
            "kind": "match-winner-market",
            "question": pm_line.get("question"),
            "url": pm_line["url"],
            "api_url": pm_line.get("api_url"),
            "team_a_prob": pa,
            "team_b_prob": pb,
            "volume_usd": pm_line.get("volume"),
            "fetched_at": manifest.get("polymarket_lol_markets.json", {}).get("fetched_at"),
            "stale": manifest.get("polymarket_lol_markets.json", {}).get("stale", False),
        })

    ma = mb = None
    if pm_line is None:
        ma, mb = find_kalshi_futures(fixture, kl)
        if ma and mb:
            fa, fb = ma["mid"], mb["mid"]
            if fa + fb > 0:
                pa = fa / (fa + fb)
                pb = fb / (fa + fb)
                lines.append({
                    "source": "Kalshi",
                    "kind": "derived-estimate-input",
                    "note": ("tournament futures used as inputs to our ratio model "
                             "(see methodology)"),
                    "team_a_futures_market": {"url": ma["url"], "title": ma["title"], "mid": ma["mid"]},
                    "team_b_futures_market": {"url": mb["url"], "title": mb["title"], "mid": mb["mid"]},
                    "model": "p(A)=f(A)/(f(A)+f(B)) on futures mids (same Kalshi event %s)"
                             % ma["event_ticker"],
                    "fetched_at": manifest.get("kalshi_lol_markets.json", {}).get("fetched_at"),
                    "stale": manifest.get("kalshi_lol_markets.json", {}).get("stale", False),
                })
                # also record team probs via the derived line
                lines.append({
                    "source": "Derived (this project)",
                    "kind": "derived-estimate",
                    "team_a_prob": pa,
                    "team_b_prob": pb,
                    "fetched_at": manifest.get("kalshi_lol_markets.json", {}).get("fetched_at"),
                    "stale": manifest.get("kalshi_lol_markets.json", {}).get("stale", False),
                })

    pk_line = None
    try:
        pk_line = find_pinnacle_coverage(fixture, pk)
    except Exception as e:
        flags.append("pinnacle-coverage-error: %s" % e)
    if pk_line:
        lines.append({
            "source": "Pinnacle",
            "kind": "listed-matchup-coverage",
            "note": ("Pinnacle lists this matchup with markets; no public price "
                     "endpoint exists (verified 2026-10-21), so no numeric line "
                     "is taken from Pinnacle."),
            "league": pk_line.get("league_name"),
            "best_of": pk_line.get("best_of"),
            "url": pk_line["url"],
            "fetched_at": manifest.get("pinnacle_lol_matchups.json", {}).get("fetched_at"),
            "stale": manifest.get("pinnacle_lol_matchups.json", {}).get("stale", False),
        })

    pa = pb = None
    basis = None
    note = None
    for ln in lines:
        if ln["kind"] in ("match-winner-market", "derived-estimate") and \
           ln.get("team_a_prob") is not None:
            pa, pb = ln["team_a_prob"], ln["team_b_prob"]
            basis = "market-line" if ln["kind"] == "match-winner-market" else "derived-estimate"
            break

    pick = None
    pick_side = None
    if pa is not None and pb is not None:
        if pa > pb:
            pick, pick_side = fixture["team_a"]["name"], "a"
        elif pb > pa:
            pick, pick_side = fixture["team_b"]["name"], "b"
        else:
            note = "Market is exactly even; no pick."
            flags.append("even-market-no-pick")
    if basis == "market-line":
        note = ("Market-mid probability from the source above (fetched %s). "
                "Higher side is the pick." %
                manifest.get("polymarket_lol_markets.json", {}).get("fetched_at"))
    elif basis == "derived-estimate":
        note = ("Our own line, derived from both teams' tournament futures mids "
                "(transparent ratio model, low confidence). Inputs and links are "
                "in the lines section; see Flagged for Review.")
    if pa is None:
        flags.append("no-external-market-found")

    fixture.update({
        "lines": lines,
        "prob_team_a": pa,
        "prob_team_b": pb,
        "pick": pick,
        "pick_side": pick_side,
        "pick_basis": basis,
        "pick_note": note,
        "pinnacle_covered": pk_line is not None,
        "flags": flags,
    })
    return fixture


def main():
    manifest = common.read_json(os.path.join(common.RAW_DIR, "manifest.json")) \
        if os.path.exists(os.path.join(common.RAW_DIR, "manifest.json")) else {}
    hs = common.load_snapshot("hotspawn_fixtures_scheduled.json")
    pm = common.load_snapshot("polymarket_lol_markets.json")
    kl = common.load_snapshot("kalshi_lol_markets.json")
    pk = common.load_snapshot("pinnacle_lol_matchups.json")
    if hs is None:
        common.fail("no hotspawn fixtures snapshot; cannot build")

    pm_markets = (pm or {}).get("markets", [])
    kl_markets = (kl or {}).get("markets", [])
    pk_matchups = (pk or {}).get("matchups", [])

    matches = []
    for fx in hs:
        matches.append(build_match(fx, pm_markets, kl_markets, pk_matchups, manifest))
    matches.sort(key=lambda m: (m["start_utc"] or "", m["hotspawn_id"]))

    n_line = sum(1 for m in matches if m["pick_basis"] == "market-line")
    n_derived = sum(1 for m in matches if m["pick_basis"] == "derived-estimate")
    n_unres = sum(1 for m in matches if m["pick_basis"] is None)
    n_pin = sum(1 for m in matches if m["pinnacle_covered"])

    payload = {
        "generated_at": common.now_iso(),
        "scope": "League of Legends fixtures currently open for picks on the "
                 "Hotspawn Pick'Em lobby (status=scheduled), with win "
                 "probabilities from external betting/prediction markets only.",
        "sources": {
            "hotspawn": {
                "name": "Hotspawn Pick'Em lobby (match list only - NOT used for "
                        "probabilities)",
                "lobby_url": common.HOTSPAWN_LOBBY_URL,
                "api_url": common.HOTSPAWN_FIXTURES_URL,
                "fetched_at": manifest.get("hotspawn_fixtures_scheduled.json", {}).get("fetched_at"),
                "stale": manifest.get("hotspawn_fixtures_scheduled.json", {}).get("stale", False),
            },
            "polymarket": {
                "name": "Polymarket (gamma API)",
                "url": common.POLYMARKET_GAMMA_BASE,
                "fetched_at": manifest.get("polymarket_lol_markets.json", {}).get("fetched_at"),
                "stale": manifest.get("polymarket_lol_markets.json", {}).get("stale", False),
            },
            "kalshi": {
                "name": "Kalshi (KXLOL series)",
                "url": "%s/series/%s" % (common.KALSHI_API_BASE, common.KALSHI_LOL_SERIES),
                "fetched_at": manifest.get("kalshi_lol_markets.json", {}).get("fetched_at"),
                "stale": manifest.get("kalshi_lol_markets.json", {}).get("stale", False),
            },
            "pinnacle": {
                "name": "Pinnacle (guest API - coverage check only)",
                "url": common.PINNACLE_API_BASE,
                "fetched_at": manifest.get("pinnacle_lol_matchups.json", {}).get("fetched_at"),
                "stale": manifest.get("pinnacle_lol_matchups.json", {}).get("stale", False),
            },
        },
        "matches": matches,
        "summary": {
            "total_matches": len(matches),
            "market_line": n_line,
            "derived_estimate": n_derived,
            "unresolved": n_unres,
            "pinnacle_covered": n_pin,
        },
        "limitations": [
            "Most Hotspawn LoL matches are low-tier regional/online events. No "
            "verified public betting line exists for them, so their picks are "
            "left blank and they are listed under Flagged for Review. Per the "
            "project rules, no probability is invented for these matches.",
            "Pinnacle lists professional LoL markets (e.g., Worlds, EMEA "
            "Masters) but its public guest API exposes no price endpoint "
            "(matchups/<id>/markets -> 404, verified 2026-10-21). Pinnacle is "
            "therefore used only to confirm a match carries a pro-book line.",
            "Polymarket currently lists per-match markets only for its covered "
            "LoL events (Worlds 2026, EMEA Masters). Matches outside those "
            "events have no per-match market.",
            "Kalshi's KXLOL series currently contains tournament futures only "
            "(no per-match markets, verified 2026-10-21). Futures are used "
            "only as labeled inputs to our derived estimate for matches where "
            "both teams have futures in the same event.",
            "The Hotspawn backend endpoint is unofficial (reverse-engineered "
            "from the public lobby page, which serves team logos from the same "
            "host). If Hotspawn changes the host, refreshes fail and the site "
            "shows the last good data with a STALE marker instead of inventing "
            "new matches.",
            "Probabilities are market mids at fetch time and move over time. "
            "Every number on the site carries the fetch timestamp from the "
            "manifest; the data refreshes automatically every 4 hours.",
            "Derived estimates (our own lines) use a transparent ratio model "
            "on tournament-futures mids. They are not book lines, are labeled "
            "as such, and are duplicated on the Flagged for Review page.",
        ],
    }
    common.write_json(os.path.join(common.REPO_ROOT, "data", "matches.json"), payload)

    print("\n=== BUILD SUMMARY ===")
    print("total=%d market-line=%d derived=%d unresolved=%d pinnacle-covered=%d"
          % (len(matches), n_line, n_derived, n_unres, n_pin))
    for m in matches:
        basis = m["pick_basis"] or "UNRESOLVED"
        pa = fmt_pct(m["prob_team_a"])
        pb = fmt_pct(m["prob_team_b"])
        print("%s | %s | %s vs %s | %s%% vs %s%% | %s | %s | pin=%s" % (
            (m["start_utc"] or "?")[:16],
            (m["tournament"] or "")[:34],
            (m["team_a"]["name"] or "")[:20], (m["team_b"]["name"] or "")[:20],
            pa if pa is not None else "-", pb if pb is not None else "-",
            m["pick"] or "-", basis, m["pinnacle_covered"]))


if __name__ == "__main__":
    main()
