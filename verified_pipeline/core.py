"""Pure, fail-closed inventory, full-series evidence, and history calculations.

Hotspawn has exactly one permitted role: establish fixture identity and schedule.
No Hotspawn crowd, score, or history field crosses sanitize_inventory().
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
import math
import re
import unicodedata
from urllib.parse import urlparse

UTC = timezone.utc
MAX_QUOTE_AGE = timedelta(hours=8)
MAX_TIME_DIFFERENCE = timedelta(hours=6)
MODEL_VERSION = "partial-series-log5-beta2-shrink10-v1"
MODEL_PARAMETERS = {"prior_wins": 2, "prior_losses": 2, "shrink_samples": 10,
                    "minimum_series_per_team": 2, "lookback_days": 60,
                    "maximum_latest_result_age_days": 14}
HOTSPAWN_FEED = "https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures?sport_alias=lol&status=scheduled"


def iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z") if value else None


def dt(value) -> datetime | None:
    """Only explicit timezone-aware dates or the publisher's millisecond epoch."""
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            number = float(value)
            if number < 1e12:  # never silently interpret seconds as milliseconds
                return None
            return datetime.fromtimestamp(number / 1000, UTC)
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone(UTC) if parsed.tzinfo else None
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def norm(value: str) -> str:
    """Typography/case only. Never drops Academy, II, country, or sponsor words."""
    return "".join(c for c in unicodedata.normalize("NFKC", str(value)).casefold() if c.isalnum())


def provisional(value: str) -> bool:
    n = norm(value)
    return not n or n in {"tbd", "tba", "unknown", "waitingforinformation"} or n.startswith(("winnerof", "loserof", "tbd"))


def competition_family(value: str) -> str:
    n = norm(value)
    if "worldchampionship" in n or "worlds20" in n:
        return "worlds"
    if "emeamasters" in n or re.match(r"em20\d\d", n):
        return "emea"
    if "prm2nddivision" in n:
        return "PRM2"
    if "prm3rddivision" in n:
        return "PRM3"
    if "komplettligaen" in n:
        return "komplett"
    if "rivalsleague" in n:
        return "rivals"
    return n


def valid_https(value) -> bool:
    try:
        u = urlparse(str(value))
        return u.scheme == "https" and bool(u.hostname) and not u.username and not u.password
    except ValueError:
        return False


def sanitize_inventory(payload) -> list[dict]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("Inventory is not a nonempty fixture list; refusing to replace the last known inventory")
    out, seen = [], set()
    for raw in payload:
        if not isinstance(raw, dict):
            raise ValueError("Malformed inventory row")
        if raw.get("sport_alias") != "lol":
            continue
        id_ = str(raw.get("id", ""))
        if not id_.isdigit() or id_ in seen:
            raise ValueError("Missing/duplicate fixture ID; refusing silent inventory loss")
        seen.add(id_)
        # This allow-list is the firewall. Scores, pick counts and probabilities
        # are intentionally absent, including during cache/receipt import.
        out.append({k: raw.get(k) for k in (
            "id", "sport_alias", "status", "competition_id", "competition_name",
            "scheduled_start_time", "lock_time", "participants0_id", "participants0_name",
            "participants1_id", "participants1_name", "best_of", "series_format", "tier", "stage")})
    if not out:
        raise ValueError("No listed LoL fixtures; cannot establish inventory coverage")
    return out


def fresh(observed_at, now: datetime, maximum=MAX_QUOTE_AGE) -> bool:
    observed = dt(observed_at)
    return observed is not None and -timedelta(minutes=5) <= now - observed <= maximum


def american_implied(price) -> float:
    if isinstance(price, bool):
        raise ValueError("Invalid American price")
    x = float(price)
    if not math.isfinite(x) or abs(x) < 100:
        raise ValueError("Invalid American price")
    return -x / (-x + 100) if x < 0 else 100 / (x + 100)


def pinnacle_candidates(matchups, markets, *, observed_at, source_url, metadata_url) -> list[dict]:
    """Parent, non-live LoL matchups + open period-0 series moneyline only."""
    if not isinstance(matchups, list) or not isinstance(markets, list):
        return []
    parents = {}
    for m in matchups:
        league = m.get("league") or {}
        if (m.get("type") != "matchup" or m.get("parentId") is not None
                or m.get("parent") is not None or m.get("isLive") is not False
                or m.get("status") != "pending" or "leagueoflegends" not in norm(league.get("name", ""))
                or (league.get("sport") or {}).get("id") != 12):
            continue
        parts = m.get("participants") or []
        if len(parts) != 2 or {p.get("alignment") for p in parts} != {"home", "away"}:
            continue
        parents[str(m.get("id"))] = m
    out = []
    for market in markets:
        if (market.get("type") != "moneyline" or market.get("period") != 0
                or market.get("key") != "s;0;m" or market.get("status") != "open"
                or market.get("isAlternate") is not False):
            continue
        m = parents.get(str(market.get("matchupId")))
        if not m:
            continue
        prices = market.get("prices") or []
        if len(prices) != 2 or {p.get("designation") for p in prices} != {"home", "away"}:
            continue
        by_side = {p["designation"]: p.get("price") for p in prices}
        parts = {p["alignment"]: p.get("name", "") for p in m["participants"]}
        try:
            qa, qb = american_implied(by_side["home"]), american_implied(by_side["away"])
        except (ValueError, TypeError):
            continue
        start = dt(m.get("startTime"))
        if not start or any(provisional(n) for n in parts.values()):
            continue
        out.append({"provider": "Pinnacle", "method": "bookmaker", "scope": "series",
                    "id": str(m["id"]), "team_a": parts["home"], "team_b": parts["away"],
                    "competition": m["league"]["name"], "start_utc": iso(start),
                    "probability_a": qa / (qa + qb), "probability_b": qb / (qa + qb),
                    "raw_prices": by_side, "overround": qa + qb - 1,
                    "source_url": source_url, "metadata_url": metadata_url,
                    "observed_at": observed_at, "provider_updated_at": None,
                    "provider_version": market.get("version"), "best_of": m.get("bestOfX")})
    return out


def _list(value):
    try:
        value = json.loads(value) if isinstance(value, str) else value
        return value if isinstance(value, list) else []
    except (ValueError, TypeError):
        return []


def polymarket_candidates(markets, *, observed_at, source_url) -> list[dict]:
    out, seen = [], set()
    for m in markets if isinstance(markets, list) else []:
        title = str(m.get("question", ""))
        # Game-1 child_moneyline must never price the BO3/BO5 match winner.
        if (m.get("sportsMarketType") != "moneyline" or m.get("groupItemTitle") != "Match Winner"
                or m.get("active") is not True or m.get("closed") is not False
                or m.get("acceptingOrders") is not True
                or not (title.startswith("LoL:") or "league of legends" in title.casefold())
                or re.search(r"\b(?:map|game)\s*\d+|correct score|handicap|total maps", title, re.I)):
            continue
        names, prices = _list(m.get("outcomes")), _list(m.get("outcomePrices"))
        start = dt(m.get("gameStartTime") or m.get("eventStartTime"))
        if len(names) != 2 or len(prices) != 2 or not start or any(provisional(n) for n in names):
            continue
        if any(norm(n) in {"yes", "no", "draw"} for n in names) or norm(names[0]) == norm(names[1]):
            continue
        try:
            a, b = float(prices[0]), float(prices[1])
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(a + b) and 0 < a < 1 and 0 < b < 1 and abs(a + b - 1) < .05):
            continue
        if str(m.get("id")) in seen:
            continue
        seen.add(str(m.get("id")))
        out.append({"provider": "Polymarket", "method": "prediction_market", "scope": "series",
                    "id": str(m["id"]), "team_a": str(names[0]), "team_b": str(names[1]),
                    "competition": title, "start_utc": iso(start),
                    "probability_a": a / (a + b), "probability_b": b / (a + b),
                    "raw_prices": prices, "source_url": "https://gamma-api.polymarket.com/markets/" + str(m["id"]),
                    "metadata_url": source_url, "observed_at": observed_at,
                    "provider_updated_at": m.get("updatedAt"), "provider_version": None, "best_of": None})
    return out


def fit(row: dict, evidence: dict, now: datetime) -> tuple[bool, bool]:
    """Exact teams, competition, known nearby start, fresh receipt. No fuzzy aliases."""
    a, b = norm(row["team_a"]), norm(row["team_b"])
    x, y = norm(evidence.get("team_a", "")), norm(evidence.get("team_b", ""))
    start, external = dt(row.get("start_utc")), dt(evidence.get("start_utc"))
    forward = (a, b) == (x, y)
    reverse = (a, b) == (y, x)
    if (not (forward or reverse) or a == b or not start or not external or external <= now
            or abs(start - external) > MAX_TIME_DIFFERENCE or evidence.get("scope") != "series"
            or competition_family(row["competition"]) != competition_family(evidence.get("competition", ""))
            or not fresh(evidence.get("observed_at"), now)
            or not valid_https(evidence.get("source_url")) or not valid_https(evidence.get("metadata_url"))):
        return False, False
    return True, reverse


def result_eligible(result: dict, cutoff: datetime) -> bool:
    try:
        local = date.fromisoformat(result["source_date"])
        # Unspecified organizer timezone: use an intentionally late bound, never
        # label the displayed local date as an exact UTC completion timestamp.
        late_bound = datetime.combine(local + timedelta(days=1), datetime.min.time(), UTC) + timedelta(hours=20)
        seen = date.fromisoformat(result.get("observed_on", "9999-12-31"))
        a, b = result["score_a"], result["score_b"]
        return (result.get("completed") is True and result.get("best_of") == 3
                and type(a) is int and type(b) is int and max(a, b) == 2 and 0 <= min(a, b) < 2
                and late_bound < cutoff and seen <= cutoff.date()
                and cutoff - late_bound <= timedelta(days=MODEL_PARAMETERS["lookback_days"])
                and valid_https(result.get("source_url"))
                and urlparse(result["source_url"]).hostname == "www.primeleague.gg"
                and not provisional(result["team_a"]) and not provisional(result["team_b"]))
    except (KeyError, ValueError, TypeError):
        return False


def history_estimate(row: dict, results: list[dict], now: datetime) -> tuple[dict | None, str]:
    family = competition_family(row["competition"])
    if family not in {"PRM2", "PRM3"} or "26-27" not in row["competition"]:
        return None, "No dated, independently verified training history for this competition."
    start = dt(row.get("start_utc"))
    if not start or start <= now:
        return None, "Unknown or elapsed fixture time; no prematch estimate."
    cutoff = min(start, now)
    used, wins, losses, dates, seen = [], [0, 0], [0, 0], [[], []], set()
    for r in results:
        if r.get("id") in seen or r.get("competition") != family or r.get("season") != "2026/27" or not result_eligible(r, cutoff):
            continue
        seen.add(r["id"])
        contributes = False
        for i, team in enumerate((row["team_a"], row["team_b"])):
            if norm(team) not in {norm(r["team_a"]), norm(r["team_b"])}:
                continue
            side = 0 if norm(team) == norm(r["team_a"]) else 1
            is_win = (r["score_a"] > r["score_b"]) if side == 0 else (r["score_b"] > r["score_a"])
            wins[i] += int(is_win)
            losses[i] += int(not is_win)
            dates[i].append(date.fromisoformat(r["source_date"]))
            contributes = True
        if contributes:
            used.append(r)
    counts = [wins[i] + losses[i] for i in range(2)]
    if min(counts) < MODEL_PARAMETERS["minimum_series_per_team"]:
        return None, f"Insufficient exact-team organizer history ({counts[0]} and {counts[1]} eligible series; minimum 2 per team). Aliases are not guessed."
    if any((now.date() - max(ds)).days > MODEL_PARAMETERS["maximum_latest_result_age_days"] for ds in dates):
        return None, "Organizer history is stale: at least one team's last confirmed result is more than 14 days old."
    # Smoothed observed series rates -> log5 matchup -> small-sample shrinkage.
    # These are stated modeling assumptions, NOT a factual or calibrated chance.
    rates = [(w + 2) / (n + 4) for w, n in zip(wins, counts)]
    ra, rb = rates
    raw = (ra - ra * rb) / (ra + rb - 2 * ra * rb)
    weight = min(counts) / (min(counts) + 10)
    pa = round(.5 + weight * (raw - .5), 6)
    return {"probability_a": pa, "probability_b": round(1 - pa, 6), "version": MODEL_VERSION,
            "counts": counts, "wins": wins, "losses": losses, "parameters": MODEL_PARAMETERS,
            "training_ids": [r["id"] for r in used], "training_results": used,
            "latest_dates": [str(max(ds)) for ds in dates], "cutoff_utc": iso(cutoff),
            "limitations": "Uncalibrated, partial audited series history; very small sample. No strength-of-schedule, roster, draft or patch adjustment. Not bookmaker odds."}, ""


def build_dataset(inventory, *, inventory_at, now, candidates=(), history=(), permalinks=None, sources=(), findings=()):
    rows = []
    permalinks = permalinks or {}
    inv_fresh = fresh(inventory_at, now)
    for raw in sanitize_inventory(inventory):
        a, b = str(raw.get("participants0_name") or ""), str(raw.get("participants1_name") or "")
        start, lock = dt(raw.get("scheduled_start_time")), dt(raw.get("lock_time"))
        state = "upcoming" if start and start > now else "elapsed" if start else "unknown_time"
        if state == "upcoming" and lock and lock <= now:
            state = "locked"
        url = permalinks.get(str(raw["id"]))
        if not (valid_https(url) and urlparse(url).hostname == "www.hotspawn.com" and urlparse(url).path.startswith("/matches/")):
            url = HOTSPAWN_FEED
        flags = []
        if raw.get("status") == "scheduled" and state == "elapsed":
            flags.append("Stale-listed: feed still says scheduled, but the listed start is in the past; outcome not inferred.")
        if not inv_fresh:
            flags.append("Inventory observation is stale or unavailable; new fixture coverage cannot be confirmed.")
        if any(provisional(t) for t in (a, b)) or norm(a) == norm(b):
            flags.append("Unconfirmed or duplicate participant identity; no probability or pick.")
        if not start:
            flags.append("No valid timezone-aware start in the inventory; no probability or pick.")
        if not raw.get("best_of") and not raw.get("series_format"):
            flags.append("Hotspawn series format is unspecified; only explicitly full-series market evidence is eligible.")
        row = {"id": str(raw["id"]), "team_a": a, "team_b": b,
               "competition": str(raw.get("competition_name") or ""), "competition_id": raw.get("competition_id"),
               "start_utc": iso(start), "lock_utc": iso(lock), "state": state,
               "inventory_status": raw.get("status"), "inventory_at": inventory_at, "inventory_source": HOTSPAWN_FEED,
               "hotspawn_url": url, "canonical_match_link": url != HOTSPAWN_FEED,
               "probability_a": None, "probability_b": None, "pick": None, "method": "unresolved",
               "evidence": [], "model": None, "flags": flags, "reason": ""}
        if state != "upcoming":
            row["reason"] = "Elapsed/locked listing retained for full inventory accountability; no current prematch pick." if state != "unknown_time" else "Start time unconfirmed."
        elif not inv_fresh or any(provisional(t) for t in (a, b)) or norm(a) == norm(b):
            row["reason"] = "Inventory freshness or exact participant identity is unconfirmed."
        rows.append(row)
    # A quote cannot identify two inventory fixtures. Ambiguous rematches are
    # rejected rather than selecting whichever row happened to be first.
    for evidence in candidates:
        matching = [(r, rev) for r in rows if r["state"] == "upcoming" and not r["reason"]
                    for ok, rev in [fit(r, evidence, now)] if ok]
        if len(matching) != 1:
            continue
        row, reverse = matching[0]
        e = dict(evidence)
        e["reversed_to_inventory"] = reverse
        e["probability_a"] = evidence["probability_b"] if reverse else evidence["probability_a"]
        e["probability_b"] = evidence["probability_a"] if reverse else evidence["probability_b"]
        row["evidence"].append(e)
    for row in rows:
        if row["reason"]:
            continue
        if row["evidence"]:
            # One transparent primary line, never an unexplained multi-provider average.
            row["evidence"].sort(key=lambda e: (0 if e["method"] == "bookmaker" else 1, e["provider"], e["id"]))
            primary = row["evidence"][0]
            row.update(probability_a=round(primary["probability_a"], 6), probability_b=round(primary["probability_b"], 6), method=primary["method"])
            for e in row["evidence"]:
                if dt(e["start_utc"]) != dt(row["start_utc"]):
                    row["flags"].append(f"Schedule conflict: Hotspawn {row['start_utc']}; {e['provider']} {e['start_utc']}. Exact teams/competition match, within 6-hour guard; confirm start before acting.")
                if e.get("provider_updated_at") is None:
                    row["flags"].append(f"{e['provider']} supplies no quote update timestamp; observation time is retrieval time, not a price-change time.")
            if any(abs(e["probability_a"] - primary["probability_a"]) > .1 for e in row["evidence"][1:]):
                row["flags"].append("Providers disagree by more than 10 percentage points; primary line retained, no blind average.")
            row["reason"] = "Full-series, fresh, exact-team external line; probabilities are normalized price implications, not known outcomes."
        else:
            model, reason = history_estimate(row, list(history), now)
            if model:
                row.update(probability_a=model["probability_a"], probability_b=model["probability_b"], method="model", model=model)
                row["flags"].append(model["limitations"])
                row["reason"] = "Independent series-history estimate, not a market quote; see every input and the formula."
            else:
                row["reason"] = "No accepted full-series external line. " + reason
        if row["probability_a"] is not None:
            delta = row["probability_a"] - row["probability_b"]
            row["pick"] = row["team_a"] if delta > .000001 else row["team_b"] if delta < -.000001 else None
            if row["pick"] is None:
                row["flags"].append("Evidence-based tie: probabilities available, but no directional pick; never defaults to team A.")
    rows.sort(key=lambda r: (r["state"] == "elapsed", r["start_utc"] or "9999", r["id"]))
    counts = Counter(r["method"] for r in rows if r["state"] == "upcoming")
    summary = {"listed": len(rows), "upcoming": sum(r["state"] == "upcoming" for r in rows),
               "elapsed": sum(r["state"] == "elapsed" for r in rows),
               "locked_or_unknown": sum(r["state"] not in {"upcoming", "elapsed"} for r in rows),
               "picks": sum(r["pick"] is not None for r in rows), "bookmaker": counts["bookmaker"],
               "prediction_market": counts["prediction_market"], "model": counts["model"],
               "unresolved": sum(r["state"] == "upcoming" and r["pick"] is None for r in rows),
               "needs_review": sum(bool(r["flags"]) for r in rows)}
    dataset = {"schema_version": 1, "generated_at": iso(now), "inventory_observed_at": inventory_at,
               "inventory_fresh": inv_fresh, "inventory_source": HOTSPAWN_FEED,
               "refresh_interval_hours": 4, "probability_stale_after_hours": 8,
               "model_version": MODEL_VERSION, "summary": summary, "sources": list(sources),
               "findings": list(findings), "matches": rows}
    validate_dataset(dataset)
    return dataset


def validate_dataset(data):
    rows, ids = data["matches"], set()
    if not rows or data["summary"]["listed"] != len(rows):
        raise ValueError("Coverage summary mismatch/empty dataset")
    for r in rows:
        if r["id"] in ids or not valid_https(r["inventory_source"]):
            raise ValueError("Duplicate ID or missing inventory source")
        ids.add(r["id"])
        a, b = r["probability_a"], r["probability_b"]
        if a is None or b is None:
            if a is not None or b is not None or r["pick"] is not None:
                raise ValueError("Unconfirmed values must remain jointly null, without a pick")
        else:
            if not (isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isfinite(a + b)
                    and 0 <= a <= 1 and 0 <= b <= 1 and abs(a + b - 1) < .00001):
                raise ValueError("Invalid paired probabilities")
            if r["method"] not in {"bookmaker", "prediction_market", "model"} or r["state"] != "upcoming":
                raise ValueError("Unbacked/elapsed probability")
            if r["method"] == "model" and (not r["model"] or not r["model"]["training_results"]):
                raise ValueError("Model without original result evidence")
            if r["method"] != "model" and not r["evidence"]:
                raise ValueError("Market probability without original publisher evidence")
            expected = r["team_a"] if a > b + .000001 else r["team_b"] if b > a + .000001 else None
            if r["pick"] != expected:
                raise ValueError("Pick disagrees with probability or invents a tie-break")
    if len(ids) != data["summary"]["listed"]:
        raise ValueError("Inventory accounting mismatch")
