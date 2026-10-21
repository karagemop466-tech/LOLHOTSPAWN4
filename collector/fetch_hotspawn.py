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
    common.log("fetching %s" % common.HOTSPAWN_FIXTURES_URL)
    fixtures, status = common.http_get_json(common.HOTSPAWN_FIXTURES_URL)
    if status != 200:
        common.save_snapshot("hotspawn_fixtures_scheduled.json",
                             common.HOTSPAWN_FIXTURES_URL, None, status)
        common.fail("hotspawn fixtures fetch failed (HTTP %s)" % status)

    if not isinstance(fixtures, list):
        common.save_snapshot("hotspawn_fixtures_scheduled.json",
                             common.HOTSPAWN_FIXTURES_URL, fixtures, status)
        common.fail("unexpected fixtures payload (expected list)")

    problems = []
    for i, fx in enumerate(fixtures):
        for field in ("id", "competition_name", "sport_alias", "status",
                      "participants0_name", "participants1_name",
                      "scheduled_start_time"):
            if fx.get(field) in (None, ""):
                problems.append("fixture[%d] missing %s" % (i, field))
        if fx.get("sport_alias") != "lol":
            problems.append("fixture %s sport_alias=%s" % (fx.get("id"), fx.get("sport_alias")))
        if fx.get("status") != "scheduled":
            problems.append("fixture %s status=%s" % (fx.get("id"), fx.get("status")))
        if common.ms_epoch_to_iso(fx.get("scheduled_start_time")) is None:
            problems.append("fixture %s bad scheduled_start_time" % fx.get("id"))

    if problems:
        for p in problems[:20]:
            log("VALIDATION: " + p)
        common.save_snapshot("hotspawn_fixtures_scheduled.json",
                             common.HOTSPAWN_FIXTURES_URL, fixtures, status)
        common.fail("fixture validation failed (%d problems)" % len(problems))

    meta = common.save_snapshot("hotspawn_fixtures_scheduled.json",
                                common.HOTSPAWN_FIXTURES_URL, fixtures, status,
                                extra={"count": len(fixtures)})

    # Audit table (workflow log)
    rows = sorted(fixtures, key=lambda f: int(f.get("scheduled_start_time") or 0))
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
