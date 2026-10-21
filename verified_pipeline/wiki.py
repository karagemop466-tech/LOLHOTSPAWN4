"""Conservative native Leaguepedia MatchSchedule observations, never Elo seeds.

The public Data: pages are community-wiki sources, not organizer endorsements.
No synthetic per-game rows, league-average opponents, invented completion times,
standings expansion, team-code aliases, priors or hard-coded picks are imported.
A template, winner, score, date, scope and exact names must all be recognized.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
import hashlib
import re
from urllib.parse import urlparse

from .core import dt, iso, norm, provisional

BASE = "https://lol.fandom.com/wiki/Data:"
# Public Data: routes independently inspected or identified in the integrated
# source research. HTTP/semantic failures remain visible, never guessed facts.
PAGES = [
    {"key": "prm2", "family": "PRM2", "season": "2026/27", "page": "Prime_League_2nd_Division/2027_Season/Fall_Split"},
    {"key": "prm3", "family": "PRM3", "season": "2026/27", "page": "Prime_League_3rd_Division/2027_Season/Fall_Split"},
    {"key": "komplett", "family": "komplett", "season": "2026", "page": "Komplettligaen/2026_Season/Autumn_Split"},
    {"key": "rivals", "family": "rivals", "season": "2026", "page": "RIVALS_LEAGUE/2026_Season/Season_2"},
    {"key": "four-nations", "family": "four-nations", "season": "2026", "page": "4_Nations/2026_Season/Halloween_Heist"},
    {"key": "arabian2", "family": "arabian2", "season": "2026", "page": "Arabian_League_2nd_Division/2026_Season/Summer_Split"},
    {"key": "arc", "family": "arc", "season": "2026", "page": "Arabian_Regional_Championship_2026/Qualifiers/LB-Li-SY-PS"},
    {"key": "celol-b", "family": "celol-b", "season": "2026", "page": "LigaGG/CELOL_S%C3%A9rie_B/2026_Season/Split_2"},
    {"key": "celol-b-playoffs", "family": "celol-b", "season": "2026", "page": "LigaGG/CELOL_S%C3%A9rie_B/2026_Season/Split_2_Playoffs"},
    {"key": "lgc", "family": "lgc", "season": "2026", "page": "LoL_Game_Changers/2026_Season/Playoffs"},
    {"key": "tunisian", "family": "tunisian", "season": "2026", "page": "Tunisian_Super_League/2026_Season"},
]
SEASONS = {p["family"]: p["season"] for p in PAGES}


def page_url(spec):
    return BASE + spec["page"] + "?action=raw"


def trusted_record(record):
    return any(record.get("source_url") == page_url(p)
               and record.get("competition") == p["family"] and record.get("season") == p["season"]
               for p in PAGES)


def templates(text):
    """Only outer templates; nested games are never promoted to match results."""
    depth, start, i = 0, None, 0
    while i < len(text) - 1:
        pair = text[i:i+2]
        if pair == "{{":
            if depth == 0:
                start = i + 2
            depth += 1
            i += 2
        elif pair == "}}" and depth:
            depth -= 1
            if depth == 0:
                yield text[start:i]
            i += 2
        else:
            i += 1
    if depth:
        raise ValueError("Unbalanced native templates; publication parser refused page")


def fields(template):
    # Split only top-level pipes, preserving any nested stream/game templates.
    pieces, start, brace, bracket, i = [], 0, 0, 0, 0
    while i < len(template):
        pair = template[i:i+2]
        if pair == "{{":
            brace += 1; i += 2; continue
        if pair == "}}":
            brace -= 1; i += 2; continue
        if pair == "[[":
            bracket += 1; i += 2; continue
        if pair == "]]":
            bracket -= 1; i += 2; continue
        if template[i] == "|" and not brace and not bracket:
            pieces.append(template[start:i]); start = i + 1
        i += 1
    pieces.append(template[start:])
    name, values = pieces[0].strip(), {}
    for part in pieces[1:]:
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip().casefold()
        if k in values:
            raise ValueError("Duplicate native template field: " + k)
        values[k] = v.strip()
    return name, values


def scheduled_utc(day, time, zone, dst):
    # Only explicit, recognized native timezone/DST combinations. This is a
    # scheduled start, never an invented game/series completion timestamp.
    offsets = {"UTC": 0, "GMT": 0, "CEST": 2, "BRT": -3, "EDT": -4}
    zone, dst = zone.strip().upper(), dst.strip().casefold()
    if zone in {"CET", "EST"}:
        if dst not in {"yes", "no"}:
            return None
        offset = (2 if dst == "yes" else 1) if zone == "CET" else (-4 if dst == "yes" else -5)
    elif zone in offsets:
        offset = offsets[zone]
    else:
        return None
    try:
        if not re.fullmatch(r"\d{2}:\d{2}", time):
            return None
        parsed = datetime.fromisoformat(day + "T" + time).replace(tzinfo=timezone(timedelta(hours=offset)))
        return iso(parsed)
    except ValueError:
        return None


def parse_page(text, spec, *, observed_on):
    if "{{MatchSchedule" not in text or text.lstrip().startswith("<"):
        raise ValueError("No recognized native MatchSchedule data (shell/access notice is not history)")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    records, schedule, rejected, groups = [], [], 0, {}
    bestof, tab = None, ""
    for block in templates(text):
        name, f = fields(block)
        if name == "TournamentGroups":
            groups = {}
            for group in f.get("groups", "").split(","):
                group = group.strip()
                for team in f.get(group.casefold(), "").split(","):
                    if team.strip():
                        key = norm(team)
                        if key in groups:
                            groups[key] = None  # Ambiguous group, not arbitrary first.
                        else:
                            groups[key] = group
        elif name == "MatchSchedule/Start":
            bestof = int(f["bestof"]) if f.get("bestof") in {"1", "3", "5"} else None
            tab = f.get("tab", "")
        elif name == "MatchSchedule/End":
            bestof, tab = None, ""
        elif name == "MatchSchedule":
            a, b = f.get("team1", ""), f.get("team2", "")
            bo = int(f["bestof"]) if f.get("bestof") in {"1", "3", "5"} else bestof
            day, time = f.get("date", ""), f.get("time", "")
            # No link aliases, TBDs, zero-played profiles or unprinted year.
            if (not bo or any(provisional(t) or re.search(r"[{}\[\]<>]", t) for t in (a, b))
                    or norm(a) == norm(b) or not re.fullmatch(r"20\d\d-\d\d-\d\d", day)):
                rejected += 1; continue
            try:
                date.fromisoformat(day)
            except ValueError:
                rejected += 1; continue
            group_a, group_b = groups.get(norm(a)), groups.get(norm(b))
            group = group_a if group_a and group_a == group_b else None
            identity = "|".join((spec["key"], f.get("initialtab", tab), f.get("initialorder", ""), day, norm(a), norm(b)))
            row = {"id": "wiki-" + spec["key"] + "-" + hashlib.sha256(identity.encode()).hexdigest()[:16],
                   "competition": spec["family"], "season": spec["season"], "group": group,
                   "team_a": a, "team_b": b, "best_of": bo, "source_date": day,
                   "displayed_time": time or None, "source_timezone": f.get("timezone") or None,
                   "source_dst": f.get("dst") or None,
                   "scheduled_utc": scheduled_utc(day, time, f.get("timezone", ""), f.get("dst", "")),
                   "source_url": page_url(spec), "observed_on": observed_on,
                   "retrieval_method": "Native community-wiki MatchSchedule template, not synthetic games or standings",
                   "completed": False}
            # A default score/forfeit/DQ is administrative, not played strength.
            excluded = any(re.search(r"\b(?:ff[12]?|forfeit|dq|dqd|disqualif\w*|walkover|default)\b", k + " " + v, re.I)
                           for k, v in f.items() if k not in {"stream", "streams"})
            # Organizer research reports zero played games for Solid Gaming;
            # conflicting administrative wiki scores are not skill observations.
            if spec["family"] == "komplett" and "solidgaming" in {norm(a), norm(b)}:
                excluded = True
            sa, sb, winner = f.get("team1score", ""), f.get("team2score", ""), f.get("winner", "")
            if (not excluded and sa.isdigit() and sb.isdigit() and winner in {"1", "2"}
                    and max(int(sa), int(sb)) == bo // 2 + 1 and 0 <= min(int(sa), int(sb)) < bo // 2 + 1
                    and ((int(sa) > int(sb)) == (winner == "1"))):
                row.update(score_a=int(sa), score_b=int(sb), completed=True,
                           excerpt=f"{day} {time}; {a} {sa}:{sb} {b}; BO{bo}; winner={winner}; native MatchSchedule")
                records.append(row)
            elif sa or sb or winner or excluded:
                rejected += 1
                row["result_unusable"] = True
            schedule.append(row)
    if not schedule:
        raise ValueError("Native page yielded no recognized dated fixtures")
    return {"records": records, "schedule": schedule, "rejected_results": rejected,
            "notes": "Community-wiki native series, partial archive. No team-code aliases or score-to-synthetic-game expansion."}


def collect(client, previous):
    def fetch(spec):
        key = "wiki-" + spec["key"]
        payload = client.request(key, page_url(spec), html=True,
                                 transform=lambda text: parse_page(text, spec, observed_on=datetime.now(timezone.utc).date().isoformat()))
        return spec, key, payload
    results, scheduled = list(previous), []
    # Polite bounded public requests; no Cargo rate-limit workaround or login.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for spec, key, payload in pool.map(fetch, PAGES):
            if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
                continue
            url = page_url(spec)
            # Successful full-page observations replace this page's previous
            # records, so corrections/retractions cannot survive as extra wins.
            if not client.cache[key].get("error") and not client.offline:
                results = [r for r in results if r.get("source_url") != url]
            known = {r["id"]: r for r in results}
            known.update({r["id"]: r for r in payload["records"]})
            results = list(known.values())
            scheduled += [{**r, "observed_at": client.observed(key)} for r in payload.get("schedule", [])]
    return sorted(results, key=lambda r: (r["source_date"], r["id"])), scheduled
