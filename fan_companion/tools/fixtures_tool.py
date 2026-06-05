"""
Live WC 2026 fixtures via api.football-data.org (free tier).
Register at https://www.football-data.org/client/register to get a free API key,
then set FOOTBALL_DATA_API_KEY in your .env file.
"""

import os
import httpx

_BASE = "https://api.football-data.org/v4"
_SEASON = "2026"


def get_live_fixtures(
    team: str = "",
    date_from: str = "",
    date_to: str = "",
) -> dict:
    """Fetch live FIFA World Cup 2026 fixture data from api.football-data.org.

    Use this tool whenever the user asks about real match schedules, dates,
    times, venues, scores, or group stage standings. It returns the official
    FIFA WC 2026 fixture list, optionally filtered by team or date range.

    Args:
        team: Optional team name to filter by, e.g. 'USA', 'Brazil', 'England'.
        date_from: Optional start date in YYYY-MM-DD format.
        date_to: Optional end date in YYYY-MM-DD format.

    Returns:
        A dict with a 'matches' list containing fixture details, or an 'error' key.
    """
    api_key = os.getenv("FOOTBALL_DATA_API_KEY", "")
    if not api_key:
        return {
            "error": (
                "FOOTBALL_DATA_API_KEY is not set. "
                "Fall back to the MongoDB 'find' tool on worldcup2026.matches instead."
            )
        }

    headers = {"X-Auth-Token": api_key}
    params: dict = {"season": _SEASON}
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{_BASE}/competitions/WC/matches",
                headers=headers,
                params=params,
            )
            if resp.status_code == 401 or resp.status_code == 400:
                return {"error": f"Invalid API key: {resp.text[:200]}"}
            resp.raise_for_status()
            data = resp.json()

        matches = data.get("matches", [])

        # Filter by team name (case-insensitive across all name fields)
        if team:
            t = team.lower()
            matches = [
                m for m in matches
                if any(
                    t in (m.get(side, {}).get(field, "") or "").lower()
                    for side in ("homeTeam", "awayTeam")
                    for field in ("name", "shortName", "tla")
                )
            ]

        formatted = []
        for m in matches[:25]:  # cap to avoid context overflow
            score = m.get("score", {})
            ft = score.get("fullTime", {})
            formatted.append({
                "id": m.get("id"),
                "date": (m.get("utcDate") or "")[:10],
                "time_utc": (m.get("utcDate") or "")[11:16],
                "status": m.get("status"),
                "stage": m.get("stage"),
                "group": m.get("group"),
                "home_team": (m.get("homeTeam") or {}).get("name"),
                "away_team": (m.get("awayTeam") or {}).get("name"),
                "venue": m.get("venue"),
                "venue_note": (
                    "Live API did not include a venue. Call resolve_fixture_venue before saying the venue is unavailable."
                    if not m.get("venue")
                    else ""
                ),
                "score_home": ft.get("home"),
                "score_away": ft.get("away"),
            })

        return {
            "source": "api.football-data.org — live",
            "competition": "FIFA World Cup 2026",
            "total_returned": len(formatted),
            "matches": formatted,
        }

    except httpx.HTTPStatusError as exc:
        return {"error": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to fetch live fixtures: {exc}"}
