"""Original-publisher HTTP receipts, public discovery, and conservative parsing.

No keys, geo-bypass, rotating proxies, login workarounds or CAPTCHA solving.
HTTP 200 is retrieval, not evidence of results. Last-good receipt dates survive
failures; failed attempts never turn old data into a new observation.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .core import HOTSPAWN_FEED, iso, norm, sanitize_inventory, valid_https

PINNACLE = "https://guest.api.arcadia.pinnacle.com/0.1"
GAMMA = "https://gamma-api.polymarket.com"
MAX_BYTES = 8_000_000
MAX_GAMMA_PAGES = 8
GAMMA_FIELDS = ("id", "question", "outcomes", "outcomePrices", "sportsMarketType", "groupItemTitle", "gameStartTime", "eventStartTime", "active", "closed", "acceptingOrders", "updatedAt", "slug")


def stamp():
    return iso(datetime.now(timezone.utc))


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def json_list(value):
    if not isinstance(value, list):
        raise ValueError("Publisher schema changed: expected a JSON list")
    return value


def gamma_events(value):
    events = json_list(value)
    # Keep complete event counts for pagination, but discard image URLs,
    # descriptions, tokens and unrelated outcome metadata from the public cache.
    return [{"id": e.get("id"), "slug": e.get("slug"), "title": e.get("title"),
             "markets": [{k: m.get(k) for k in GAMMA_FIELDS} for m in e.get("markets", []) if isinstance(m, dict)]}
            for e in events if isinstance(e, dict)]


class SourceClient:
    def __init__(self, path, *, offline=False):
        self.path = Path(path)
        self.offline = offline
        self.cache = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.active = set()

    def request(self, key, url, *, transform=None, html=False):
        self.active.add(key)
        old = self.cache.get(key, {})
        if old.get("source_url") != url:
            old = {}
        attempted = stamp()
        record = dict(old)
        record.update(source_id=key, source_url=url, attempted_at=attempted, cache_used=False)
        if self.offline:
            record.update(cache_used=True, attempted_at=old.get("attempted_at"), offline_build_at=attempted,
                          status="cached receipt (offline build); no new HTTP request")
            self.cache[key] = record
            return record.get("payload")
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; LOLHOTSPAWN4 source-audit/1.0; +https://github.com/karagemop466-tech/LOLHOTSPAWN4)",
                                           "Accept": "text/html" if html else "application/json"})
            with urlopen(request, timeout=22) as response:
                body = response.read(MAX_BYTES + 1)
                code = response.status
                final_url = response.geturl()
                response_date = response.headers.get("Date")
            if len(body) > MAX_BYTES:
                raise ValueError("Publisher response exceeds the 8 MB safety limit")
            text = body.decode("utf-8", "replace")
            payload = text if html else json.loads(text)
            if not html and isinstance(payload, dict) and payload.get("status") in (401, 403):
                raise PermissionError("Publisher authorization notice; no access workaround attempted")
            payload = transform(payload) if transform else payload
            record.update(payload=payload, observed_at=stamp(), http_status=code, final_url=final_url,
                          response_date_header=response_date, body_sha256=hashlib.sha256(body).hexdigest(),
                          status="retrieved; semantic guards still apply", error=None, cache_used=False)
        except HTTPError as exc:
            record.update(http_status=exc.code, error=f"HTTP {exc.code}; no access workaround attempted", cache_used=bool(old), status="retrieval failed")
        except Exception as exc:
            record.update(http_status=None, error=f"{type(exc).__name__}: {str(exc)[:220]}", cache_used=bool(old), status="retrieval failed")
        self.cache[key] = record
        print(key, record["status"], record.get("http_status"), record.get("error") or "", flush=True)
        return record.get("payload")

    def observed(self, key):
        return self.cache.get(key, {}).get("observed_at")

    def receipts(self):
        return [{k: v for k, v in self.cache[key].items() if k != "payload"} for key in sorted(self.active)]

    def save(self):
        # Bounded current receipts, not a growing high-volume raw-data archive.
        atomic_json(self.path, {k: v for k, v in self.cache.items() if k in self.active})

    def bootstrap(self, directory):
        """Import only dated original research receipts, never legacy picks data."""
        mapping = {"hotspawn-fixtures": "hotspawn", "pinnacle-worlds-matchups": "pinnacle-meta-9587",
                   "pinnacle-worlds-prices": "pinnacle-prices-9587", "pinnacle-emea-matchups": "pinnacle-meta-225201",
                   "pinnacle-emea-prices": "pinnacle-prices-225201", "polymarket-series-5721049": "gamma-series-audit"}
        for filename, key in mapping.items():
            path = Path(directory) / (filename + ".json")
            if not path.exists() or key in self.cache:
                continue
            raw = json.loads(path.read_text())
            payload = raw.get("json")
            if not raw.get("verified_retrieval") or not raw.get("retrieved_at") or payload is None:
                continue
            if key == "hotspawn":
                payload = sanitize_inventory(payload)
            self.cache[key] = {"source_id": key, "source_url": raw["source_url"], "observed_at": raw["retrieved_at"],
                               "attempted_at": raw["attempted_at"], "body_sha256": raw.get("body_sha256"),
                               "http_status": raw.get("http_status"), "status": "dated original-publisher receipt import",
                               "payload": payload, "cache_used": True, "error": None}


def canonical_links(client, ids):
    found = {}
    # These four exact URLs were returned by the official WP resolver on Oct21.
    # They are durable identity links, never probability inputs.
    initial = {
        "1081205": "https://www.hotspawn.com/matches/galions-vs-solary-em-2026-summer-main-event-1081205",
        "1071214": "https://www.hotspawn.com/matches/ascent-gaming-vs-ntnui-kometkameratene-komplettligaen-2026-autumn-1071214",
        "1067878": "https://www.hotspawn.com/matches/gen-g-vs-invictus-gaming-worlds-2026-main-event-1067878",
        "1067680": "https://www.hotspawn.com/matches/bilibili-gaming-vs-movistar-koi-worlds-2026-main-event-1067680"}
    found.update({k: v for k, v in initial.items() if k in ids})
    for offset in range(0, len(ids), 60):
        batch = ids[offset:offset + 60]
        url = "https://www.hotspawn.com/wp-json/pickem/v1/fixtures?ids=" + ",".join(batch)
        def validate(value):
            if not isinstance(value, dict) or value.get("success") is not True or not isinstance(value.get("permalinks"), dict):
                raise ValueError("Official canonical-permalink resolver schema mismatch")
            return {"success": True, "permalinks": {str(k): v for k, v in value["permalinks"].items()
                if str(k) in batch and valid_https(v) and urlparse(v).hostname == "www.hotspawn.com"
                and urlparse(v).path.startswith("/matches/")}}
        data = client.request("hotspawn-links-" + str(offset // 60), url, transform=validate)
        if isinstance(data, dict):
            found.update(data.get("permalinks", {}))
    return found


def discover_pinnacle(client):
    leagues = client.request("pinnacle-discovery", PINNACLE + "/sports/12/leagues", transform=json_list) or []
    ids = {str(l["id"]) for l in leagues if "leagueoflegends" in norm(l.get("name", "")) and str(l.get("id", "")).isdigit()}
    # Previously verified league routes remain candidates if discovery is down;
    # the dashboard reports the failed discovery receipt, not exhaustive coverage.
    ids.update({"9587", "225201"})
    if len(ids) > 30:
        raise ValueError("Unexpected LoL league discovery size; review source schema")
    tasks = [("pinnacle-meta-" + id_, PINNACLE + "/leagues/" + id_ + "/matchups") for id_ in sorted(ids)]
    tasks += [("pinnacle-prices-" + id_, PINNACLE + "/leagues/" + id_ + "/markets/straight") for id_ in sorted(ids)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda item: client.request(*item, transform=json_list), tasks))
    return sorted(ids)


def discover_gamma(client):
    markets, truncated = [], False
    for page in range(MAX_GAMMA_PAGES):
        url = GAMMA + f"/events?tag_id=65&active=true&closed=false&limit=100&offset={page * 100}"
        events = client.request("gamma-events-" + str(page), url, transform=gamma_events)
        if not isinstance(events, list):
            break
        for event in events:
            for market in event.get("markets", []):
                markets.append({**market, "_receipt_observed_at": client.observed("gamma-events-" + str(page)), "_receipt_source_url": url})
        if len(events) < 100:
            break
        if page == MAX_GAMMA_PAGES - 1:
            truncated = True
    # A directly verified canonical series route is a fallback to discovery,
    # never the Game1 route from the historical implementation.
    single = client.request("gamma-series-audit", GAMMA + "/markets/5721049",
                            transform=lambda m: {k: m.get(k) for k in GAMMA_FIELDS} if isinstance(m, dict) else {})
    return markets, single, truncated


class TextPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens, self.links, self.title, self.skip, self.in_title = [], [], [], 0, False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style"}:
            self.skip += 1
        if tag == "title":
            self.in_title = True
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.skip:
            return
        value = data.strip()
        if value:
            self.tokens.append(value)
            if self.in_title:
                self.title.append(value)


def parse_prime_result(html, url, competition):
    """Strict template recognition; unrecognized HTML yields no result facts."""
    parser = TextPage()
    parser.feed(html)
    title = " ".join(parser.title)
    names = re.fullmatch(r"(.+?) vs (.+?)\s*\|\s*Matches\s*\|\s*Prime League", title, re.I)
    # Only the event header before fan predictions/game detail sections is read.
    text = "\n".join(parser.tokens)
    prefix = re.split(r"\bPredictions\b|\bGame 1 Details\b|\bComparison\b", text, maxsplit=1, flags=re.I)[0]
    date_match = re.search(r"\b(20\d\d-\d\d-\d\d)\s+(\d\d:\d\d)\b", prefix)
    score = re.search(r"(?:Show\s*Results\s*)?\b([0-3])\s*:\s*([0-3])\s*best\s+of\s+three\b", prefix, re.I)
    if not names or not date_match or not score or re.search(r"forfeit|default\s+win|walkover", prefix, re.I):
        return None
    a, b = int(score[1]), int(score[2])
    if max(a, b) != 2 or min(a, b) not in (0, 1):
        return None
    id_match = re.search(r"/matches/(\d+)-", url)
    if not id_match:
        return None
    return {"id": "prime-" + id_match[1], "competition": competition, "season": None,
            "season_note": "Season is not established by the recognized match header; this automatic observation cannot satisfy same-season model eligibility.",
            "source_url": url, "source_date": date_match[1], "displayed_time": date_match[2], "source_timezone": None,
            "team_a": names[1].strip(), "team_b": names[2].strip(), "score_a": a, "score_b": b,
            "best_of": 3, "completed": True, "observed_on": stamp()[:10],
            "retrieval_method": "Original organizer HTML; strict event header parser, no fan predictions",
            "excerpt": f"{date_match[1]} {date_match[2]}; {names[1]} {a}:{b} {names[2]}; best of three"}


def organizer_history(client, audited):
    records = {r["id"]: r for r in audited}
    # Discovery is retried on every refresh. 403 stops this branch of discovery;
    # no claim that the immutable audited history has become newly refreshed.
    for comp, path in (("PRM2", "liga2"), ("PRM3", "liga3")):
        url = "https://www.primeleague.gg/en/" + path
        key = "prime-" + path
        def extract_html(text):
            parser = TextPage()
            parser.feed(text)
            links = sorted({urljoin(url, link) for link in parser.links
                            if re.match(r"(?:https://www\.primeleague\.gg)?/en/matches/\d+-", link)})
            # Do not publish HTML rosters, pictures or prediction percentages.
            return {"match_urls": links, "recognized_match_links": len(links)}
        data = client.request(key, url, html=True, transform=extract_html)
        if not data or client.cache[key].get("error"):
            continue
        links = data.get("match_urls", [])
        # A bounded set of current match details; deduplicated, no synthetic IDs.
        known = {r["source_url"] for r in records.values() if r["competition"] == comp}
        new_links = [link for link in links if link not in known][:60]
        def retrieve(link):
            m = re.search(r"/matches/(\d+)", link)
            payload = client.request("prime-result-" + m[1], link, html=True,
                                     transform=lambda text: parse_prime_result(text, link, comp))
            return payload if isinstance(payload, dict) else None
        with ThreadPoolExecutor(max_workers=2) as pool:
            for r in pool.map(retrieve, new_links):
                if r:
                    records[r["id"]] = r
    return sorted(records.values(), key=lambda r: (r["source_date"], r["id"]))


def alternative_source_checks(client):
    tasks = [
        ("komplett-results", "https://www.komplettligaen.no/lol/resultater?season=13909&division=18859"),
        ("rivals-results", "https://www.rivalsleague.gg/lol/match/08083633-9115-4db9-95de-19940a62b738"),
        ("ggbet-access", "https://gg.bet/en/esports/league-of-legends"),
        ("thunderpick-access", "https://thunderpick.io/esports/league-of-legends/emea-masters-2026-summer/10747/solary-vs-galions/2829674"),
        ("bwin-access", "https://www.bwin.com/en/sports/league-of-legends-106")]
    def check(item):
        # Access and manual-review evidence ONLY. A page shell, ambiguous year,
        # region notice, or unvalidated live badge cannot become a price/result.
        return client.request(*item, html=True, transform=lambda text: {
            "bytes_decoded": len(text.encode("utf-8")), "validated_price_or_result": False,
            "notes": "Reachability check only; no machine-verified full-series price or dated result extracted. Access failure is not proof of market absence."})
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(check, tasks))
