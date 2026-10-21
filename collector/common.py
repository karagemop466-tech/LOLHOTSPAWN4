"""Shared helpers for the LOL Hotspawn pick collector.

Standard library only (no pip dependencies) so it runs on any GitHub-hosted
runner without an install step.

Design rules (see methodology.html and COORDINATION.md):
  * Every fact in the published dataset must carry the URL of the source it
    came from and the time it was fetched.
  * If a source cannot be fetched, the previous snapshot (if any) is reused
    and marked stale. We never invent values.
  * Raw API responses are saved for audit; the full Polymarket events dump is
    kept only as a workflow artifact (too large for git), a normalized
    extract is committed instead.
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(REPO_ROOT, "data", "raw")

# --- Verified source endpoints (see methodology.html for verification log) ---
HOTSPAWN_API_BASE = "https://phpstack-1372681-6459848.cloudwaysapps.com"
HOTSPAWN_FIXTURES_URL = HOTSPAWN_API_BASE + "/api/v1/fixtures?sport_alias=lol&status=scheduled"
HOTSPAWN_LOBBY_URL = "https://play.hotspawn.com/lobby"

POLYMARKET_GAMMA_BASE = "https://gamma-api.polymarket.com"
POLYMARKET_LOL_TAG_ID = 65  # LoL primary tag (id 39, slug "lol") in GET /sports

KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"
KALSHI_LOL_SERIES = "KXLOL"

PINNACLE_API_BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
PINNACLE_ESPORTS_SPORT_ID = 12  # "E Sports" in GET /sports

USER_AGENT = "lol-hotspawn-pick-desk/1.0 (+research project; contact: repo owner)"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    print("[%s] %s" % (now_iso(), msg), flush=True)


def fail(msg, code=1):
    log("ERROR: " + msg)
    sys.exit(code)


def http_get_json(url, timeout=60, retries=3, backoff=5):
    """GET a URL and parse JSON. Returns (obj, http_status). Raises on final failure."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
                return json.loads(body), resp.status
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:500]
            except Exception:
                pass
            last_err = "HTTP %s for %s (body: %s)" % (e.code, url, body)
            if e.code in (404, 400):
                # Deterministic client error - do not retry, return marker.
                try:
                    return json.loads(body), e.code
                except Exception:
                    raise RuntimeError(last_err)
            # 5xx / 429 - retry
        except Exception as e:  # URLError, timeout, JSON decode
            last_err = "%s for %s" % (e, url)
        if attempt < retries:
            time.sleep(backoff * attempt)
    raise RuntimeError(last_err)


def sha256_of(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")
    log("wrote %s" % os.path.relpath(path, REPO_ROOT))


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_snapshot(name, url, payload, status, extra=None):
    """Save a raw/normalized snapshot plus manifest metadata.

    If fetching failed, reuses the previous snapshot (marked stale) so the
    pipeline can still build.
    """
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(RAW_DIR, name)
    meta = {
        "file": "data/raw/" + name,
        "url": url,
        "fetched_at": now_iso(),
        "http_status": status,
        "stale": False,
    }
    if payload is None:
        # Fetch failed: fall back to previous snapshot if present.
        if os.path.exists(path):
            meta["stale"] = True
            meta["note"] = "fetch failed at %s; reusing previous snapshot" % now_iso()
            log("WARNING: %s stale (fetch failed)" % name)
        else:
            meta["note"] = "fetch failed and no previous snapshot exists"
    else:
        if extra:
            meta.update(extra)
        if isinstance(payload, (dict, list)):
            payload_str = json.dumps(payload, ensure_ascii=False)
        else:
            payload_str = str(payload)
        meta["sha256"] = sha256_of(payload_str)
        write_json(path, payload)
    manifest_path = os.path.join(RAW_DIR, "manifest.json")
    manifest = read_json(manifest_path) if os.path.exists(manifest_path) else {}
    manifest[name] = meta
    write_json(manifest_path, manifest)
    return meta


def load_snapshot(name):
    path = os.path.join(RAW_DIR, name)
    if not os.path.exists(path):
        return None
    return read_json(path)


# --- Team name matching -----------------------------------------------------
_STOPWORDS = {"esports", "esport", "team", "gg", "the", "of"}


def normalize_team(name):
    n = (name or "").lower()
    n = re.sub(r"['\u2019]", "", n)
    n = re.sub(r"[^a-z0-9]+", " ", n).strip()
    return n


def core_words(name):
    words = normalize_team(name).split()
    return [w for w in words if w not in _STOPWORDS]


def teams_match(a, b):
    """Fuzzy two-way match for team names.

    Exact normalized equality, containment for names >= 4 chars, or a high
    sequence ratio. Deliberately conservative: a false match is worse than a
    missed match (missed -> flagged unresolved, never a wrong pick).
    """
    na, nb = normalize_team(a), normalize_team(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if len(na) >= 4 and (na in nb or nb in na):
        return True
    ca, cb = core_words(a), core_words(b)
    if ca and cb and set(ca) == set(cb):
        return True
    ratio = _seq_ratio(na, nb)
    return ratio >= 0.86


def _seq_ratio(a, b):
    # stdlib difflib without importing at module top for speed
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


def ms_epoch_to_iso(ms):
    if ms in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
