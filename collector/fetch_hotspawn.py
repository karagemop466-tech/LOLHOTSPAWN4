"""Fetch the current (scheduled, pick-open) League of Legends fixtures from the
Hotspawn Pick'Em lobby.

Source (verified 2026-10-21):
  * Human-visible list:  https://play.hotspawn.com/lobby  (LoL tab)
  * Data endpoint:       https://phpstack-1372681-6459848.cloudwaysapps.com/api/v1/fixtures
    query: sport_alias=lol&status=scheduled
    (the phpstack-*.cloudwaysapps.com host is Hotspawn's public backend; the
    same host serves the team logos shown on the lobby page).

Notes:
  * status=scheduled = fixtures currently open for picks (the lobby's
    "Closing Soon" + "Upcoming" sections). Ended/cancelled fixtures have other
    status values and are intentionally excluded: picks are for matches that
    can still be picked.
  * Hotspawn's own "x% picked" figures are crowd data and are NOT used as an
    indicator of match probability (project requirement). We only keep them
    as context.

Output:
  data/raw/hotspawn_fixtures_scheduled.json   (raw API response)
  data/raw/manifest.json                      (fetch metadata, merged)
  stdout: one line per fixture for the workflow audit log.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


def main():
    log("fetching %s" % common.HOTSPAWN_FIXTURES_URL)
    fixtures, status = common.http_get_json(common.HOTSPAWN_FIXTURES_URL)
    if status != 200:
        common.save_snapshot("hotspawn_fixtures_scheduled.json",
                             common.HOTSPAWN_FIXTURES_URL, None, status)
        common.fail("hotspawn fixtures fetch failed (HTTP %s)" % status)

    if not isinstance(fixtures, list):
        common.save_snapshot("hotspawn_fixtures_scheduled.json",
                             common.HOTSPAWN_FIXTURES_URL, fixtures, status)
        common.fail("unexpected fixtures payload (expected list)")

    valid_fixtures = []
    problems = []
    for i, fx in enumerate(fixtures):
        p0 = fx.get("participants0_name")
        p1 = fx.get("participants1_name")
        st = fx.get("scheduled_start_time")
        if not p0 or not p1 or p0.upper() == "TBD" or p1.upper() == "TBD" or not st:
            problems.append("fixture[%d] (id %s) incomplete participant/start data — skipping" % (i, fx.get("id")))
            continue
        valid_fixtures.append(fx)

    if problems:
        for p in problems[:10]:
            log("NOTE: " + p)

    meta = common.save_snapshot("hotspawn_fixtures_scheduled.json",
                                common.HOTSPAWN_FIXTURES_URL, valid_fixtures, status,
                                extra={"count": len(valid_fixtures)})

    # Audit table (workflow log)
    rows = sorted(valid_fixtures, key=lambda f: int(f.get("scheduled_start_time") or 0))
    print("\n=== HOTSPAWN LoL SCHEDULED FIXTURES: %d ===" % len(rows))
    print("%-10s %-22s %-40s %-40s %-6s %-8s %-3s" %
          ("id", "start_utc", "competition", "matchup", "tier", "stage", "pts"))
    for fx in rows:
        start = common.ms_epoch_to_iso(fx.get("scheduled_start_time")) or "?"
        comp = (fx.get("competition_name") or "")[:40]
        matchup = "%s vs %s" % (fx.get("participants0_name"), fx.get("participants1_name"))
        matchup = matchup[:40]
        print("%-10s %-22s %-40s %-40s %-6s %-8s %-3s" % (
            fx.get("id"), start, comp, matchup,
            str(fx.get("tier") or "?")[:6], str(fx.get("stage") or "?")[:8],
            fx.get("offered_points") or "?"))
    print("fetched_at=%s stale=%s" % (meta["fetched_at"], meta["stale"]))


if __name__ == "__main__":
    main()
