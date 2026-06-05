"""Verify every local World Cup fixture resolves to a venue."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.wc2026_data import MATCHES
from fan_companion.tools.venue_resolution_tool import resolve_fixture_venue


def main() -> None:
    failures = []
    for match in MATCHES:
        result = resolve_fixture_venue(
            team1=match.get("team1", ""),
            team2=match.get("team2", ""),
            date=match.get("date", ""),
            city=match.get("city_display", ""),
            venue_id=match.get("venue_id", ""),
        )
        if result.get("status") != "resolved" or not result.get("venue", {}).get("name"):
            failures.append(
                {
                    "match_id": match.get("match_id"),
                    "teams": f"{match.get('team1')} vs {match.get('team2')}",
                    "date": match.get("date"),
                    "status": result.get("status"),
                }
            )

    if len(MATCHES) != 104:
        raise SystemExit(f"Expected 104 fixtures, found {len(MATCHES)}")
    if failures:
        raise SystemExit(f"Venue resolution failures: {failures}")

    print("OK: 104 fixtures resolve to venues.")


if __name__ == "__main__":
    main()
