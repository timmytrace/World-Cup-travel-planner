"""Fixture verification helper backed by the generated 104-fixture schedule."""

from data.wc2026_data import MATCHES
from fan_companion.tools.venue_resolution_tool import resolve_fixture_venue

# Common name aliases so "USA" matches "United States", etc.
_ALIASES: dict[str, set[str]] = {
    "usa":           {"united states", "usmnt", "us"},
    "united states": {"usa", "usmnt", "us"},
    "turkiye":       {"turkey", "türkiye"},
    "türkiye":       {"turkey", "turkiye"},
    "iran":          {"ir iran"},
    "ir iran":       {"iran"},
    "south korea":   {"korea republic", "korea"},
    "korea republic":{"south korea", "korea"},
    "ivory coast":   {"cote d'ivoire", "cote divoire"},
    "cote d'ivoire": {"ivory coast"},
    "dr congo":      {"congo dr", "democratic republic of congo"},
}


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _expand(name: str) -> set[str]:
    """Return the name plus all known aliases."""
    n = _norm(name)
    return {n} | _ALIASES.get(n, set())


def _teams(match: dict) -> set[str]:
    """Return expanded team names (including aliases) for a match record."""
    t1 = _norm(match.get("team1"))
    t2 = _norm(match.get("team2"))
    return (_expand(t1) | _expand(t2)) - {""}


def verify_fixture(team1: str = "", team2: str = "", date: str = "", city: str = "") -> dict:
    """Verify a World Cup 2026 fixture against the local 104-fixture schedule.

    Use this before producing a final itinerary or when a live API result is
    incomplete. It verifies teams/date/city and includes resolved venue details.

    Args:
        team1: First team from the selected fixture.
        team2: Second team from the selected fixture.
        date: Match date in YYYY-MM-DD format.
        city: Host city, if known.

    Returns:
        A dict with verified fixture and venue details, or a not-found status.
    """
    wanted_t1 = _expand(team1)
    wanted_t2 = _expand(team2)
    wanted_teams = (wanted_t1 | wanted_t2) - {""}
    wanted_date = _norm(date)
    wanted_city = _norm(city)

    best: tuple[int, dict] | None = None
    for match in MATCHES:
        match_teams = _teams(match)
        score = 0
        if wanted_teams:
            both_match = wanted_t1 and wanted_t2 and wanted_t1.intersection(match_teams) and wanted_t2.intersection(match_teams)
            one_match  = bool(wanted_teams.intersection(match_teams))
            if both_match:
                score += 8
            elif one_match:
                score += 3
        if wanted_date and _norm(match.get("date")) == wanted_date:
            score += 5
        if wanted_city and wanted_city in _norm(match.get("city_display")):
            score += 3
        if score and (best is None or score > best[0]):
            best = (score, match)

    # Require a minimum score of 8 when teams were specified, so a date-only
    # match never silently returns the wrong fixture as "verified".
    min_score = 8 if wanted_teams else 5
    if best is None or best[0] < min_score:
        return {
            "status": "not_found",
            "note": "No verified schedule record matched. Ask for teams/date/city before giving firm fixture details.",
        }

    match = best[1]
    venue = resolve_fixture_venue(
        team1=match.get("team1", ""),
        team2=match.get("team2", ""),
        date=match.get("date", ""),
        city=match.get("city_display", ""),
        venue_id=match.get("venue_id", ""),
    )
    return {
        "status": "verified",
        "fixture": match,
        "venue_resolution": venue,
    }
