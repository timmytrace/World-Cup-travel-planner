r"""Fetch the full World Cup 2026 schedule and write a local fixture module.

The source page exposes every fixture as schema.org SportsEvent JSON-LD.
Run from the project root:

    .\.venv\Scripts\python.exe scripts\update_verified_schedule.py
"""

from __future__ import annotations

import re
import json
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_URL = "https://worldcuphub.io/en/schedule"
OUTPUT = Path("data/verified_schedule.py")

VENUE_IDS = {
    "AT&T Stadium": "att",
    "BC Place": "bcplace",
    "BMO Field": "bmo",
    "Estadio Akron": "akron",
    "Estadio Banorte": "azteca",
    "Estadio BBVA": "bbva",
    "GEHA Field at Arrowhead Stadium": "arrowhead",
    "Gillette Stadium": "gillette",
    "Hard Rock Stadium": "hardrock",
    "Levi's Stadium": "levis",
    "Lincoln Financial Field": "linc",
    "Lumen Field": "lumen",
    "Mercedes-Benz Stadium": "mercedesbenz",
    "MetLife Stadium": "metlife",
    "NRG Stadium": "nrg",
    "SoFi Stadium": "sofi",
}

CITY_DISPLAY = {
    "atlanta": "Atlanta",
    "boston": "Boston",
    "dallas": "Dallas / Fort Worth",
    "guadalajara": "Guadalajara",
    "houston": "Houston",
    "kansas-city": "Kansas City",
    "los-angeles": "Los Angeles",
    "mexico-city": "Mexico City",
    "miami": "Miami",
    "monterrey": "Monterrey",
    "new-york": "New York / New Jersey",
    "philadelphia": "Philadelphia",
    "san-francisco": "San Francisco / Bay Area",
    "seattle": "Seattle",
    "toronto": "Toronto",
    "vancouver": "Vancouver",
}

ROUND_BY_NUMBER = {
    **{n: "Group Stage" for n in range(1, 73)},
    **{n: "Round of 32" for n in range(73, 89)},
    **{n: "Round of 16" for n in range(89, 97)},
    **{n: "Quarter-Final" for n in range(97, 101)},
    101: "Semi-Final",
    102: "Semi-Final",
    103: "Third Place",
    104: "Final",
}


def _fetch_html() -> str:
    req = Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def _date_iso(label: str) -> str:
    dt = datetime.strptime(label.strip(), "%A, %B %d, %Y")
    return dt.date().isoformat()


def _group_from_event(name: str, text_window: str) -> str | None:
    # The rendered schedule carries strings like "Grp L" near each event.
    match = re.search(re.escape(name) + r".{0,160}?Grp ([A-L])", text_window, re.DOTALL)
    if match:
        return match.group(1)
    return None


def _strip_tags(html: str) -> str:
    text = re.sub(r"<!--.*?-->", "", html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_row(row_html: str) -> tuple[str, str, str, str, str] | None:
    cells = re.findall(r"<td\b.*?</td>", row_html, flags=re.DOTALL)
    if len(cells) < 4:
        return None
    time_et = _strip_tags(cells[0])
    teams_text = _strip_tags(cells[1])
    venue_name = ""
    for candidate in sorted(VENUE_IDS, key=len, reverse=True):
        if teams_text.endswith(candidate):
            venue_name = candidate
            teams_text = teams_text[: -len(candidate)].strip()
            break
    if not venue_name:
        return None
    teams_match = re.match(r"(.+?)\s+vs\s+(.+)$", teams_text)
    if not teams_match:
        return None
    team1, team2 = [part.strip() for part in teams_match.groups()]
    group = _strip_tags(cells[2]).replace("Grp ", "")
    city = _strip_tags(cells[3])
    return time_et, team1, team2, venue_name, city, group


def build_schedule() -> list[dict]:
    html = _fetch_html()
    schedule_start = html.find("Schedule by date")
    if schedule_start == -1:
        raise RuntimeError("Could not find schedule table")
    schedule_html = html[schedule_start:]
    sections = re.findall(
        r"<section><h3[^>]*>(.*?)</h3>(.*?)(?=<section><h3|</main>)",
        schedule_html,
        flags=re.DOTALL,
    )
    fixtures = []
    for date_label_html, section_html in sections:
        date = _date_iso(_strip_tags(date_label_html))
        table_match = re.search(r"<table\b.*?</table>", section_html, flags=re.DOTALL)
        if not table_match:
            continue
        rows = re.findall(r"<tr\b.*?</tr>", table_match.group(0), flags=re.DOTALL)
        for row in rows:
            parsed = _parse_row(row)
            if not parsed:
                continue
            time_et, team1, team2, venue_name, city_display, group = parsed
            index = len(fixtures) + 1

            fixtures.append(
            {
                "match_id": f"WC26-{index:03d}",
                "phase": ROUND_BY_NUMBER.get(index, "Knockout"),
                "group": group,
                "match_number": index,
                "team1": team1,
                "team2": team2,
                "date": date,
                "time_et": time_et,
                "time_local": time_et,
                "timezone": "America/New_York",
                "venue_id": VENUE_IDS.get(venue_name, ""),
                "venue_name": venue_name,
                "city_display": CITY_DISPLAY.get(city_display.lower().replace(" ", "-"), city_display),
                "fixture_status": "schedule_verified",
                "source": SOURCE_URL,
            }
        )
    return fixtures


def main() -> None:
    fixtures = build_schedule()
    missing = [item for item in fixtures if not item["venue_id"]]
    if len(fixtures) != 104:
        raise RuntimeError(f"Expected 104 fixtures, parsed {len(fixtures)}")
    if missing:
        raise RuntimeError(f"Missing venue ids: {missing}")

    OUTPUT.write_text(
        '"""Verified FIFA World Cup 2026 schedule snapshot.\n\n'
        f"Generated from {SOURCE_URL}.\n"
        'Times are listed in Eastern Time as exposed by the source schedule.\n'
        '"""\n\n'
        f"VERIFIED_MATCHES = {json.dumps(fixtures, indent=4, ensure_ascii=False)}\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(fixtures)} fixtures to {OUTPUT}")


if __name__ == "__main__":
    main()
