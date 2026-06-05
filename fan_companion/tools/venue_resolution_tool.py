"""Resolve World Cup 2026 fixture venues from the local fixture and venue map."""

from data.wc2026_data import MATCHES, VENUES

# Common name aliases so "USA" resolves to "United States", etc.
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
    n = _norm(name)
    return {n} | _ALIASES.get(n, set())


def _team_set(match: dict) -> set[str]:
    t1 = _norm(match.get("team1"))
    t2 = _norm(match.get("team2"))
    return (_expand(t1) | _expand(t2)) - {""}


def _venue_by_id(venue_id: str | None) -> dict | None:
    wanted = _norm(venue_id)
    if not wanted:
        return None
    for venue in VENUES:
        if _norm(venue.get("venue_id")) == wanted:
            return venue
    return None


def resolve_fixture_venue(
    team1: str = "",
    team2: str = "",
    date: str = "",
    city: str = "",
    venue_id: str = "",
) -> dict:
    """Resolve the known venue for a World Cup 2026 fixture.

    Use this whenever live fixture data has a blank/missing venue field, or before
    saying that a venue is unavailable. It searches the local fixture seed and
    joins the match to the local venue reference data.

    Args:
        team1: One team in the fixture.
        team2: Other team in the fixture.
        date: Match date in YYYY-MM-DD format.
        city: Host city display name, if known.
        venue_id: Local venue id, if known.

    Returns:
        A dict containing match and venue details when resolved, otherwise a
        not_found status with guidance for the agent.
    """
    wanted_t1 = _expand(team1)
    wanted_t2 = _expand(team2)
    wanted_teams = (wanted_t1 | wanted_t2) - {""}
    wanted_date = _norm(date)
    wanted_city = _norm(city)
    wanted_venue_id = _norm(venue_id)

    best: tuple[int, dict] | None = None
    for match in MATCHES:
        match_teams = _team_set(match)
        score = 0
        if wanted_venue_id and _norm(match.get("venue_id")) == wanted_venue_id:
            score += 8
        if wanted_date and _norm(match.get("date")) == wanted_date:
            score += 5
        if wanted_teams:
            both_match = wanted_t1 and wanted_t2 and wanted_t1.intersection(match_teams) and wanted_t2.intersection(match_teams)
            one_match  = bool(wanted_teams.intersection(match_teams))
            if both_match:
                score += 8
            elif one_match:
                score += 3
        if wanted_city and wanted_city in _norm(match.get("city_display")):
            score += 3

        if score and (best is None or score > best[0]):
            best = (score, match)

    # Require a minimum combined score of 5 so a single weak signal (e.g. city
    # only = 3, or one-team only = 3) never resolves the wrong fixture.
    if best is None or best[0] < 5:
        return {
            "status": "not_found",
            "note": (
                "No local fixture/venue match was found. Do not claim the venue is unavailable; "
                "say it could not be resolved from the current fixture data and ask for the match/city."
            ),
        }

    match = best[1]
    venue = _venue_by_id(match.get("venue_id"))
    if not venue:
        return {
            "status": "match_found_venue_missing",
            "match": match,
            "note": "The fixture exists locally, but the linked venue record is missing.",
        }

    return {
        "status": "resolved",
        "source": "local fixture-to-venue map",
        "match": {
            "match_id": match.get("match_id"),
            "team1": match.get("team1"),
            "team2": match.get("team2"),
            "date": match.get("date"),
            "time_local": match.get("time_local"),
            "timezone": match.get("timezone"),
            "city_display": match.get("city_display"),
            "fixture_status": match.get("fixture_status", "representative_demo"),
        },
        "venue": {
            "venue_id": venue.get("venue_id"),
            "name": venue.get("name"),
            "city": venue.get("city_display") or venue.get("city"),
            "country": venue.get("country"),
            "address": venue.get("address"),
            "capacity": venue.get("capacity"),
            "latitude": venue.get("latitude"),
            "longitude": venue.get("longitude"),
            "fan_zone": venue.get("fan_zone"),
            "nearest_airports": venue.get("nearest_airports", []),
            "transport": venue.get("transport", {}),
            "accessibility_note": venue.get("accessibility") or venue.get("host_city_notes", ""),
        },
    }
