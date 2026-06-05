import asyncio
import os
import queue
import shutil
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from html import escape

import streamlit as st
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from PIL import Image as _PIL_Image
import pydeck as pdk
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from data.wc2026_data import MATCHES, VENUES
from fan_companion import root_agent

load_dotenv()

# ── Ensure mongodb-mcp-server is available (auto-install on cloud) ─────────────
def _ensure_mcp_server() -> None:
    """Install mongodb-mcp-server via npm if not found (Streamlit Cloud startup)."""
    if shutil.which("mongodb-mcp-server") or shutil.which("mongodb-mcp-server.cmd"):
        return
    try:
        subprocess.run(
            ["npm", "install", "-g", "mongodb-mcp-server"],
            check=True, capture_output=True, timeout=120,
        )
    except Exception:
        pass  # Agent will fall back gracefully if MCP is unavailable

_ensure_mcp_server()


_BOT_AVATAR = _PIL_Image.open("World-Cup-2026-umbrella-FTR-(1).jpg.webp")

st.set_page_config(
    page_title="WC 2026 Fan Companion",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
:root {
    --wc-ink: #111318;
    --wc-panel: #ffffff;
    --wc-soft: #f5f7fb;
    --wc-line: #d8dee8;
    --wc-muted: #4f5d70;
    --wc-green: #0b8f62;
    --wc-cyan: #087fa3;
    --wc-pink: #c1136d;
    --wc-focus: #ffbf3f;
}

html, body, [class*="css"] {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.block-container {
    max-width: 1240px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

.skip-link {
    position: absolute;
    top: -44px;
    left: 1rem;
    z-index: 9999;
    background: var(--wc-focus);
    color: var(--wc-ink);
    padding: 0.65rem 0.9rem;
    border-radius: 6px;
    font-weight: 800;
    text-decoration: none;
}

.skip-link:focus {
    top: 0.75rem;
}

button:focus-visible,
a:focus-visible,
input:focus-visible,
textarea:focus-visible,
[tabindex]:focus-visible {
    outline: 3px solid var(--wc-focus) !important;
    outline-offset: 3px !important;
    box-shadow: none !important;
}

.wc-header {
    background:
        linear-gradient(135deg, rgba(17, 19, 24, 0.96), rgba(17, 19, 24, 0.8)),
        radial-gradient(circle at 15% 20%, rgba(53, 208, 127, 0.32), transparent 28%),
        radial-gradient(circle at 85% 15%, rgba(40, 180, 202, 0.28), transparent 28%),
        radial-gradient(circle at 70% 90%, rgba(234, 75, 155, 0.22), transparent 26%);
    padding: clamp(1.25rem, 4vw, 2.75rem);
    border-radius: 8px;
    color: white;
    margin-bottom: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.16);
    box-shadow: 0 18px 44px rgba(16, 17, 19, 0.18);
}

.wc-kicker {
    align-items: center;
    display: inline-flex;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.wc-kicker::before {
    content: "";
    width: 0.65rem;
    height: 0.65rem;
    border-radius: 999px;
    background: #35d07f;
    box-shadow: 0 0 0 5px rgba(53, 208, 127, 0.22);
}

.wc-header h1 {
    max-width: 780px;
    margin: 0;
    font-size: clamp(2rem, 5vw, 4rem);
    font-weight: 800;
    line-height: 1.04;
}

.wc-header span.we-are {
    background: -webkit-linear-gradient(0deg, #35d07f, #28b4ca, #ea4b9b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.wc-header p {
    max-width: 720px;
    margin: 0.85rem 0 1.3rem 0;
    font-size: 1.05rem;
    line-height: 1.6;
    color: #f1f5f9;
}

.wc-hero-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
}

.wc-pill {
    display: inline-flex;
    align-items: center;
    min-height: 2.25rem;
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.13);
    border: 1px solid rgba(255, 255, 255, 0.24);
    color: #ffffff;
    font-size: 0.9rem;
    font-weight: 700;
}

.section-title {
    margin: 0 0 0.45rem;
    color: var(--wc-ink);
    font-size: 1rem;
    font-weight: 800;
}

.section-copy {
    margin: 0 0 1rem;
    color: #3d4d5e; /* darkened from --wc-muted for 4.5:1 contrast on white */
    font-size: 0.94rem;
    line-height: 1.55;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 0 0 1.1rem;
}

.stat-card {
    min-height: 6.25rem;
    padding: 1rem;
    border: 1px solid var(--wc-line);
    border-radius: 8px;
    background: var(--wc-panel);
    box-shadow: 0 10px 26px rgba(20, 24, 32, 0.06);
}

.stat-card strong {
    display: block;
    color: var(--wc-ink);
    font-size: 1.45rem;
    line-height: 1.1;
}

.stat-card span {
    display: block;
    margin-top: 0.35rem;
    color: #3d4d5e; /* meets 4.5:1 on white background */
    font-size: 0.86rem;
    line-height: 1.35;
}

.city-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 0.75rem 0 0.35rem;
}

.city-card {
    min-height: 7.2rem;
    border: 1px solid var(--wc-line);
    border-left: 5px solid var(--wc-green);
    border-radius: 8px;
    padding: 0.9rem;
    background: #ffffff;
    color: var(--wc-ink);
}

.city-card:nth-child(3n + 2) { border-left-color: var(--wc-cyan); }
.city-card:nth-child(3n + 3) { border-left-color: var(--wc-pink); }
.city-card .city-name { font-size: 0.98rem; font-weight: 800; margin-bottom: 0.2rem; }
.city-card .stadium { font-size: 0.82rem; color: var(--wc-muted); line-height: 1.4; }
.city-card .country-tag {
    display: inline-flex;
    margin-top: 0.65rem;
    padding: 0.18rem 0.5rem;
    border-radius: 999px;
    background: #e9f8f2;
    color: #086344;
    font-size: 0.72rem;
    font-weight: 800;
}

.map-insight {
    border: 1px solid var(--wc-line);
    border-radius: 8px;
    background: #ffffff;
    padding: 0.9rem;
    margin: 0.75rem 0;
}

.map-insight strong {
    display: block;
    color: var(--wc-ink);
    font-size: 1rem;
    margin-bottom: 0.25rem;
}

.map-insight span {
    display: block;
    color: #3d4d5e;
    font-size: 0.86rem;
    line-height: 1.45;
}

.mission-card,
.saved-trip-card {
    border: 1px solid var(--wc-line);
    border-radius: 8px;
    background: #ffffff;
    padding: 0.9rem;
    margin: 0.75rem 0;
    box-shadow: 0 10px 24px rgba(20, 24, 32, 0.05);
}

.mission-card strong,
.saved-trip-card strong {
    display: block;
    color: var(--wc-ink);
    font-size: 0.98rem;
    margin-bottom: 0.25rem;
}

.mission-card span,
.saved-trip-card span {
    display: block;
    color: #3d4d5e;
    font-size: 0.84rem;
    line-height: 1.45;
}

.badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 0.65rem 0;
}

.info-badge {
    display: inline-flex;
    align-items: center;
    min-height: 1.8rem;
    padding: 0.22rem 0.55rem;
    border-radius: 999px;
    border: 1px solid var(--wc-line);
    background: var(--wc-soft);
    color: var(--wc-ink);
    font-size: 0.76rem;
    font-weight: 800;
}

.typing-wrap { display: flex; gap: 5px; align-items: center; padding: 6px 0; }
.t-dot {
    width: 8px; height: 8px;
    background: var(--wc-green);
    border-radius: 50%;
    animation: tdot 1.2s infinite;
}
.t-dot:nth-child(2) { animation-delay: 0.2s; }
.t-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes tdot {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-7px); opacity: 1; }
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

div[data-testid="stChatInput"] textarea {
    min-height: 3.25rem !important;
    font-size: 1rem !important;
}

div[data-testid="stChatMessage"] {
    border-radius: 8px;
}

div[data-testid="stSidebar"] {
    background: #f8fafc;
    border-right: 1px solid var(--wc-line);
}

div[data-testid="stSidebar"] ul li {
    padding: 0.15rem 0;
    line-height: 1.8;
}

div[data-testid="stSidebar"] a {
    color: #075985;
    font-weight: 700;
    display: inline-block;
    padding: 0.4rem 0;
    min-height: 2.75rem;
    line-height: 2;
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.001ms !important;
    }
}

/* High-contrast / forced-color mode */
@media (forced-colors: active) {
    .wc-header, .stat-card, .city-card, .mission-card, .saved-trip-card, .map-insight {
        border: 2px solid ButtonText;
    }
    .skip-link {
        border: 2px solid ButtonText;
    }
}

@media (max-width: 900px) {
    .stat-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .city-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 640px) {
    .block-container {
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }

    /* Larger touch targets on mobile */
    button, [role="button"] {
        min-height: 2.75rem !important;
    }

    div[data-testid="stChatInput"] textarea {
        font-size: 16px !important; /* Prevent iOS zoom on focus */
    }

    .wc-header {
        border-radius: 0;
        margin-left: -0.8rem;
        margin-right: -0.8rem;
    }

    .stat-grid {
        grid-template-columns: 1fr;
    }

    .wc-pill {
        width: 100%;
        justify-content: center;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<a class="skip-link" href="#trip-planning-chat">Skip to chat</a>', unsafe_allow_html=True)
# Hidden ARIA live region – screen readers announce new agent messages without page reload
st.markdown(
    '<div id="chat-live-region" aria-live="polite" aria-atomic="true" class="sr-only"></div>',
    unsafe_allow_html=True,
)


def _host_city_cards(limit: int = 6) -> str:
    cards = []
    for venue in VENUES[:limit]:
        city = escape(venue["city_display"])
        stadium = escape(venue["name"])
        country = escape(venue["country"])
        capacity = f'{venue["capacity"]:,}'
        cards.append(
            "<article class='city-card'>"
            f"<div class='city-name'>{city}</div>"
            f"<div class='stadium'>{stadium} • {capacity} capacity</div>"
            f"<div class='country-tag'>{country}</div>"
            "</article>"
        )
    return "<div class='city-grid'>" + "".join(cards) + "</div>"


def _venues_table() -> str:
    rows = [
        "| Host city | Venue | Country | Capacity |",
        "| --- | --- | --- | ---: |",
    ]
    for venue in VENUES:
        rows.append(
            f"| {venue['city_display']} | {venue['name']} | {venue['country']} | {venue['capacity']:,} |"
        )
    return "\n".join(rows)


def _venue_by_id(venue_id: str) -> dict | None:
    return next((venue for venue in VENUES if venue["venue_id"] == venue_id), None)


def _matches_for_venue(venue_id: str, phase: str = "All") -> list[dict]:
    matches = [match for match in MATCHES if match.get("venue_id") == venue_id]
    if phase != "All":
        matches = [match for match in matches if match.get("phase") == phase]
    return matches


def _venue_risk_profile(venue: dict) -> dict:
    city = venue.get("city_display", "")
    notes = venue.get("host_city_notes", "")
    text = f"{city} {notes}".lower()
    risks = []
    heat_score = 0
    crowd_score = 1
    transit_score = 1 if venue.get("transport") else 0

    if any(word in text for word in ["hot", "heat", "humid", "thunderstorm"]):
        heat_score = 2
        risks.append("Heat/weather prep")
    if "very hot" in text or "extreme" in text or city in {"Dallas / Fort Worth", "Houston", "Miami", "Monterrey"}:
        heat_score = 3
    if "altitude" in text:
        risks.append("Altitude awareness")
        crowd_score += 1
    if city in {"New York / New Jersey", "Dallas / Fort Worth", "Mexico City", "Los Angeles"}:
        crowd_score += 1
        risks.append("Crowd exit planning")
    if city in {"Toronto", "Vancouver", "Seattle", "Philadelphia", "Atlanta"}:
        transit_score = 3
        risks.append("Strong transit option")
    elif transit_score:
        transit_score = 2

    if venue.get("nearest_airports"):
        risks.append("Airport options")
    if not risks:
        risks.append("Standard matchday prep")

    return {
        "heat_score": heat_score,
        "crowd_score": min(crowd_score, 3),
        "transit_score": transit_score,
        "badges": list(dict.fromkeys(risks)),
    }


def _city_risk_badges(venue: dict) -> list[str]:
    return ["Venue details", "Fan zone", *_venue_risk_profile(venue)["badges"]]


def _risk_color(venue: dict, layer: str) -> list[int]:
    profile = _venue_risk_profile(venue)
    if layer == "Heat/weather risk":
        return [[8, 127, 163, 175], [11, 143, 98, 185], [245, 158, 11, 190], [193, 19, 109, 205]][profile["heat_score"]]
    if layer == "Crowd/exit risk":
        return [[8, 127, 163, 175], [11, 143, 98, 185], [245, 158, 11, 190], [193, 19, 109, 205]][profile["crowd_score"]]
    if layer == "Transit accessibility":
        return [[120, 128, 140, 175], [193, 19, 109, 185], [245, 158, 11, 190], [11, 143, 98, 205]][profile["transit_score"]]
    return [11, 143, 98, 185] if venue["country"] == "USA" else ([8, 127, 163, 185] if venue["country"] == "Canada" else [193, 19, 109, 185])


def _city_map_rows(venues: list[dict], phase: str, layer: str) -> list[dict]:
    rows = []
    for venue in venues:
        matches = _matches_for_venue(venue["venue_id"], phase)
        if not matches:
            continue
        profile = _venue_risk_profile(venue)
        rows.append(
            {
                "lat": venue["latitude"],
                "lon": venue["longitude"],
                "city": venue["city_display"],
                "venue": venue["name"],
                "country": venue["country"],
                "capacity": venue["capacity"],
                "match_count": len(matches),
                "radius": (16_000 + len(matches) * 4_500) if layer == "Match volume" else max(18_000, min(55_000, venue["capacity"] * 0.6)),
                "color": _risk_color(venue, layer),
                "risk": ", ".join(profile["badges"]),
            }
        )
    return rows


def _render_badges(items: list[str]) -> str:
    return "<div class='badge-row'>" + "".join(f"<span class='info-badge'>{escape(item)}</span>" for item in items) + "</div>"


def _venue_detail_markdown(venue: dict, matches: list[dict]) -> str:
    airports = ", ".join(venue.get("nearest_airports", [])) or "Check local airport options."
    next_match = matches[0] if matches else None
    next_match_text = (
        f"{next_match['date']} {next_match['time_local']} ET · {next_match['team1']} vs {next_match['team2']}"
        if next_match
        else "No matches in the active filter."
    )
    return f"""
<div class="map-insight">
    <strong>{escape(venue['name'])}</strong>
    <span>{escape(venue['city_display'])}, {escape(venue['country'])} · {venue['capacity']:,} capacity</span>
    <span>Next match: {escape(next_match_text)}</span>
    <span>Airports: {escape(airports)}</span>
</div>
"""


def _mission_card() -> str:
    mission = st.session_state.get("current_mission", {})
    if not mission:
        return ""
    match = mission.get("match", {})
    title = escape(mission.get("title", "Current mission"))
    venue = escape(str(mission.get("venue", "Venue not selected")))
    origin = escape(str(mission.get("origin", st.session_state.accessibility_profile.get("origin", "Not set"))))
    action = escape(str(mission.get("action", "Trip planning")))
    match_text = ""
    if match:
        match_text = f"{escape(match.get('date', ''))} · {escape(match.get('team1', ''))} vs {escape(match.get('team2', ''))}"
    return (
        "<div class='mission-card'>"
        f"<strong>{title}</strong>"
        f"<span>Status: {action}</span>"
        f"<span>Venue: {venue}</span>"
        f"<span>Origin/profile: {origin} · {escape(st.session_state.accessibility_profile.get('max_walking', ''))} walking</span>"
        f"<span>{match_text}</span>"
        "</div>"
    )


def _saved_trip_cards(limit: int = 2) -> str:
    trips, _warning = _load_itineraries()
    cards = []
    for trip in trips[:limit]:
        title = escape(trip.get("title", "Saved itinerary"))
        content = escape((trip.get("content", "") or "").replace("\n", " ")[:180])
        created = trip.get("created_at", "")
        if isinstance(created, datetime):
            created = created.strftime("%b %d, %Y")
        cards.append(
            "<div class='saved-trip-card'>"
            f"<strong>{title}</strong>"
            f"<span>{escape(str(created))}</span>"
            f"<span>{content}{'...' if len(trip.get('content', '')) > 180 else ''}</span>"
            "</div>"
        )
    return "".join(cards)


def _set_agent_prompt(prompt: str, display: str, mission: dict | None = None) -> None:
    if mission:
        st.session_state.current_mission = mission
    st.session_state["_inject_prompt"] = {"prompt": prompt, "display": display}


def _city_action_prompt(action: str, venue: dict, matches: list[dict]) -> str:
    profile = st.session_state.accessibility_profile
    profile_summary = (
        f"language: {profile['language']}; accessibility needs: {', '.join(profile['mobility_needs']) or 'none specified'}; "
        f"walking tolerance: {profile['max_walking']}; transit preference: {profile['transit_preference']}; "
        f"budget: {profile['budget']}; crowd preference: {profile['crowd_sensitivity']}"
    )
    match_lines = "\n".join(
        f"- {match['date']} {match['time_local']} ET: {match['team1']} vs {match['team2']} ({match['phase']})"
        for match in matches[:8]
    ) or "- No matches in current filter."
    transport = venue.get("transport", {})
    if isinstance(transport, dict):
        transport_lines = "\n".join(
            f"- {label.replace('_', ' ').title()}: {detail}"
            for label, detail in transport.items()
        )
    else:
        transport_lines = "\n".join(f"- {item}" for item in transport)
    airports = ", ".join(venue.get("nearest_airports", [])) or "Use local airport guidance."
    base = (
        f"Use the host cities map selection to help me with {venue['city_display']} and {venue['name']}. "
        f"My profile is: {profile_summary}. Known matches here:\n{match_lines}\n"
        f"Selected venue details already available from the app: address {venue.get('address', 'not listed')}; "
        f"capacity {venue.get('capacity', 'unknown')}; fan zone {venue.get('fan_zone', 'check FIFA guidance')}; "
        f"nearest airports {airports}; planning note {venue.get('host_city_notes', 'confirm venue guidance before travel')}.\n"
        f"Known transit details:\n{transport_lines or '- Confirm local transit guidance before travel.'}\n"
        "Call `resolve_fixture_venue` before claiming a venue is unavailable. "
        "Do not mention a database connection problem for this map action; the selected venue context is already present. "
    )
    if action == "plan":
        return base + "Build an accessible city trip plan with airport arrival, transit, fan zone, safety, weather prep, and a save-approval question."
    if action == "matches":
        return base + "Summarize every scheduled match at this venue, include dates/times, likely crowd considerations, and which match is best for a first-time visitor."
    if action == "compare":
        return base + "Compare this host city against two nearby or similar host cities for accessibility, transit, heat/crowd risk, and overall fan experience."
    return base + "Check matchday weather risks and packing guidance for this host city across its scheduled matches."


def _comparison_rows(venues: list[dict], phase: str) -> list[dict]:
    rows = []
    for venue in venues:
        matches = _matches_for_venue(venue["venue_id"], phase)
        profile = _venue_risk_profile(venue)
        rows.append(
            {
                "City": venue["city_display"],
                "Venue": venue["name"],
                "Matches": len(matches),
                "Capacity": f"{venue['capacity']:,}",
                "Heat": profile["heat_score"],
                "Crowd": profile["crowd_score"],
                "Transit": profile["transit_score"],
                "Best notes": ", ".join(profile["badges"][:3]),
            }
        )
    return rows


def _comparison_prompt(venues: list[dict], phase: str) -> str:
    rows = _comparison_rows(venues, phase)
    profile = st.session_state.accessibility_profile
    city_lines = "\n".join(
        f"- {row['City']} / {row['Venue']}: {row['Matches']} matches, heat {row['Heat']}, crowd {row['Crowd']}, transit {row['Transit']}, notes {row['Best notes']}"
        for row in rows
    )
    return (
        "Compare these World Cup host cities for a fan choosing where to travel. "
        f"Profile: language {profile['language']}; accessibility {', '.join(profile['mobility_needs']) or 'none specified'}; "
        f"walking tolerance {profile['max_walking']}; transit preference {profile['transit_preference']}; "
        f"budget {profile['budget']}; crowd preference {profile['crowd_sensitivity']}. "
        f"Phase filter: {phase}. Cities:\n{city_lines}\n"
        "Recommend the best city, explain tradeoffs, and end with one clear next action."
    )


def _match_label(match: dict) -> str:
    kickoff = match.get("time_local") if match.get("time_local") != "TBD" else "kickoff TBD"
    status = "verified" if match.get("fixture_status") in {"official_verified", "schedule_verified"} else "demo"
    return (
        f"{match['date']} {kickoff} · "
        f"{match['team1']} vs {match['team2']} · {match['city_display']} · {status}"
    )


def _kickoff_instruction(match: dict) -> str:
    if match.get("time_local") == "TBD":
        return (
            "The selected fixture is verified, but this local seed does not contain a verified kickoff time. "
            "Do not invent a kickoff time; if live fixture data is unavailable, build relative timeline guidance "
            "such as 'arrive 3 hours before kickoff'."
        )
    return f"The selected fixture kickoff time is {match['time_local']} local time."


def _default_profile() -> dict:
    return {
        "origin": "New York",
        "language": "English",
        "mobility_needs": ["Step-free route"],
        "max_walking": "Under 15 minutes",
        "transit_preference": "Public transit first",
        "budget": "Moderate",
        "crowd_sensitivity": "Prefer lower-crowd routes",
    }


def _latest_assistant_message() -> str:
    for message in reversed(st.session_state.get("messages", [])):
        if message.get("role") == "assistant":
            return message.get("content", "")
    return ""


def _trip_checklist(profile: dict) -> list[str]:
    checklist = [
        "Match ticket and FIFA account access",
        "Government ID or passport",
        "Phone charger or power bank",
        "Allowed-size stadium bag",
        "Weather layer: poncho, hat, sunscreen, or jacket based on forecast",
        "Emergency contact and hotel address saved offline",
    ]
    if profile.get("mobility_needs"):
        checklist.append("Accessibility confirmation, accessible entrance, and backup ride option")
    if profile.get("language") and profile["language"] != "English":
        checklist.append(f"Key directions translated into {profile['language']}")
    return checklist


@st.cache_resource(show_spinner=False)
def _mongo_client(uri: str) -> MongoClient:
    return MongoClient(uri, serverSelectionTimeoutMS=5_000)


def _mongo_db():
    uri = os.getenv("MONGODB_URI", "")
    if not uri:
        return None, "MONGODB_URI is not configured; using this browser session only."
    try:
        client = _mongo_client(uri)
        client.admin.command("ping")
        return client["worldcup2026"], ""
    except PyMongoError as exc:
        return None, f"MongoDB is unavailable right now: {exc}"


def _save_itinerary(title: str, content: str, profile: dict, mission: dict | None) -> tuple[bool, str]:
    doc = {
        "trip_id": f"trip-{uuid.uuid4().hex[:10]}",
        "user_id": st.session_state.session_id,
        "title": title,
        "content": content,
        "profile": profile,
        "mission": mission or {},
        "checklist": _trip_checklist(profile),
        "created_at": datetime.now(timezone.utc),
        "source": "streamlit_save_button",
    }
    db, warning = _mongo_db()
    if db is None:
        st.session_state.saved_itineraries_local.insert(0, doc)
        return True, warning
    try:
        db.itineraries.insert_one(doc)
        return True, "Saved to MongoDB Atlas itineraries."
    except PyMongoError as exc:
        st.session_state.saved_itineraries_local.insert(0, doc)
        return True, f"Saved locally because MongoDB write failed: {exc}"


def _load_itineraries() -> tuple[list[dict], str]:
    local = st.session_state.get("saved_itineraries_local", [])
    db, warning = _mongo_db()
    if db is None:
        return local, warning
    try:
        docs = list(
            db.itineraries.find(
                {"user_id": st.session_state.session_id},
                {"_id": 0},
            )
            .sort("created_at", -1)
            .limit(8)
        )
        return docs or local, ""
    except PyMongoError as exc:
        return local, f"Showing local saved trips because MongoDB read failed: {exc}"


def _sync_verified_fixtures() -> str:
    db, warning = _mongo_db()
    if db is None:
        return warning
    verified_matches = [
        match for match in MATCHES
        if match.get("fixture_status") in {"official_verified", "schedule_verified"}
    ]
    if not verified_matches:
        return "No verified fixtures found in the local seed."
    try:
        for match in verified_matches:
            db.matches.update_one(
                {"match_id": match["match_id"]},
                {"$set": match},
                upsert=True,
            )
        return f"Synced {len(verified_matches)} verified fixtures to MongoDB Atlas."
    except PyMongoError as exc:
        return f"Could not sync verified fixtures: {exc}"


_QUICK_PROMPTS = [
    (
        "Plan Dallas",
        "Plan a 3-day accessible trip to the England vs Croatia match at AT&T Stadium in Dallas. I'm flying from New York.",
    ),
    (
        "Compare Cities",
        "Compare Miami, Los Angeles, and New York/New Jersey for a first-time World Cup visitor.",
    ),
    (
        "Accessible Route",
        "Help me plan an accessible route from the airport to the stadium and fan zone.",
    ),
]

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"
if "session_service" not in st.session_state:
    st.session_state.session_service = InMemorySessionService()
if "runner" not in st.session_state:
    with st.spinner("⚙️ Initialising AI agent — loading tools…"):
        st.session_state.runner = Runner(
            agent=root_agent,
            app_name="worldcup_fan_companion",
            session_service=st.session_state.session_service,
        )
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi there! 👋 I'm your **World Cup 2026** travel planner. "
                "Which match or host city are you dreaming of visiting? Tell me where you're flying from too."
            ),
        }
    ]
if "accessibility_profile" not in st.session_state:
    st.session_state.accessibility_profile = _default_profile()
if "saved_itineraries_local" not in st.session_state:
    st.session_state.saved_itineraries_local = []
if "current_mission" not in st.session_state:
    st.session_state.current_mission = {}

with st.sidebar:
    st.markdown("### Official Links")
    st.markdown("- [FIFA WC 2026](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026)")
    st.markdown("- [Buy Tickets](https://www.fifa.com/tickets)")
    st.markdown("- [Fan ID](https://www.fifa.com/en/fanid)")
    st.markdown("- [Host Cities](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/host-cities)")
    if st.button("Sync Verified Fixtures", use_container_width=True, help="Update MongoDB Atlas with locally verified fixture corrections."):
        st.toast(_sync_verified_fixtures())
    st.divider()
    st.markdown("### Fan Profile")
    profile = st.session_state.accessibility_profile
    with st.form("fan_profile_form"):
        origin = st.text_input("Starting city or hotel area", value=profile["origin"])
        language = st.selectbox(
            "Preferred language",
            ["English", "Spanish", "French", "Portuguese", "German", "Arabic", "Japanese"],
            index=["English", "Spanish", "French", "Portuguese", "German", "Arabic", "Japanese"].index(profile["language"]),
        )
        mobility_needs = st.multiselect(
            "Accessibility needs",
            ["Step-free route", "Wheelchair seating", "Low walking", "Service animal", "Elevator access", "Quiet entry"],
            default=profile["mobility_needs"],
        )
        max_walking = st.select_slider(
            "Maximum comfortable walking",
            options=["Under 5 minutes", "Under 15 minutes", "Under 30 minutes", "No limit"],
            value=profile["max_walking"],
        )
        transit_preference = st.selectbox(
            "Transit preference",
            ["Public transit first", "Rideshare first", "Driving/parking", "Lowest walking"],
            index=["Public transit first", "Rideshare first", "Driving/parking", "Lowest walking"].index(profile["transit_preference"]),
        )
        budget = st.selectbox(
            "Budget",
            ["Budget", "Moderate", "Flexible"],
            index=["Budget", "Moderate", "Flexible"].index(profile["budget"]),
        )
        crowd_sensitivity = st.selectbox(
            "Crowd preference",
            ["Prefer lower-crowd routes", "Okay with busy routes", "Need sensory-friendly guidance"],
            index=["Prefer lower-crowd routes", "Okay with busy routes", "Need sensory-friendly guidance"].index(profile["crowd_sensitivity"]),
        )
        if st.form_submit_button("Update Profile", use_container_width=True):
            st.session_state.accessibility_profile = {
                "origin": origin,
                "language": language,
                "mobility_needs": mobility_needs,
                "max_walking": max_walking,
                "transit_preference": transit_preference,
                "budget": budget,
                "crowd_sensitivity": crowd_sensitivity,
            }
            st.toast("Profile updated")
            st.rerun()

    st.caption(
        "The agent uses this profile as a planning constraint for accessibility, language, crowd, and mobile-friendly guidance."
    )
    st.divider()
    st.markdown("### Saved Trips")
    latest_plan = _latest_assistant_message()
    save_disabled = not bool(latest_plan.strip())
    if st.button("Save Latest Plan", use_container_width=True, disabled=save_disabled):
        mission = st.session_state.get("current_mission", {})
        title = mission.get("title") or "World Cup matchday plan"
        ok, message = _save_itinerary(
            title=title,
            content=latest_plan,
            profile=st.session_state.accessibility_profile,
            mission=mission,
        )
        st.toast(message if ok else "Could not save plan")
        st.rerun()

    saved_trips, saved_warning = _load_itineraries()
    if saved_warning:
        st.caption(saved_warning)
    if not saved_trips:
        st.caption("Saved itineraries will appear here after you approve a plan.")
    for trip in saved_trips[:4]:
        created = trip.get("created_at", "")
        if isinstance(created, datetime):
            created = created.strftime("%b %d, %Y %H:%M UTC")
        with st.expander(trip.get("title", "Saved itinerary")):
            st.caption(str(created))
            st.markdown(trip.get("content", "")[:900] + ("…" if len(trip.get("content", "")) > 900 else ""))
            checklist = trip.get("checklist") or []
            if checklist:
                st.markdown("**Checklist**")
                for item in checklist:
                    st.checkbox(item, key=f"{trip.get('trip_id', uuid.uuid4().hex)}-{item}", value=False)

    st.divider()
    st.markdown("### Accessibility")
    st.caption(
        "This interface supports keyboard focus outlines, reduced motion preferences, "
        "larger touch targets, and a text alternative for the map."
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<section class="wc-header" aria-labelledby="page-title">
    <div class="wc-kicker">World Cup travel planner</div>
    <h1 id="page-title"><span class="we-are">WE ARE 26</span> Fan Companion</h1>
    <p>Plan matches, travel routes, weather prep, and fan experiences across the 16 host cities.</p>
    <div class="wc-hero-actions" aria-label="App highlights">
        <span class="wc-pill">16 host cities</span>
        <span class="wc-pill">Accessible trip guidance</span>
        <span class="wc-pill">MongoDB Atlas MCP memory</span>
        <span class="wc-pill">Mobile-first chat</span>
    </div>
</section>
""",
    unsafe_allow_html=True,
)

countries = sorted({venue["country"] for venue in VENUES})
st.markdown(
    f"""
<section class="stat-grid" aria-label="World Cup planning summary">
    <div class="stat-card"><strong>{len(VENUES)}</strong><span>Host city venues across North America</span></div>
    <div class="stat-card"><strong>{len(countries)}</strong><span>Countries represented: {", ".join(countries)}</span></div>
    <div class="stat-card"><strong>{len(MATCHES)}</strong><span>Verified fixtures available to plan around</span></div>
    <div class="stat-card"><strong>MCP</strong><span>MongoDB Atlas stores saved itineraries and powers retrieval</span></div>
</section>
""",
    unsafe_allow_html=True,
)

chat_col, vis_col = st.columns([1.05, 0.95], gap="large")
# Wrap both columns in a semantic main landmark via an invisible anchor
st.markdown('<a id="main-content" tabindex="-1" aria-hidden="true"></a>', unsafe_allow_html=True)


# ── Agent streaming helper ────────────────────────────────────────────────────
def get_agent_response_stream(user_text: str):
    runner = st.session_state.runner
    session_service = st.session_state.session_service
    session_id = st.session_state.session_id
    q = queue.Queue()

    async def _run():
        existing = await session_service.get_session(
            app_name="worldcup_fan_companion", user_id="fan_user", session_id=session_id
        )
        if not existing:
            await session_service.create_session(
                app_name="worldcup_fan_companion", user_id="fan_user", session_id=session_id
            )
        async for event in runner.run_async(
            user_id="fan_user",
            session_id=session_id,
            new_message=Content(role="user", parts=[Part(text=user_text)]),
        ):
            if event.content and event.content.parts:
                text = event.content.parts[0].text or ""
                if text:
                    q.put(("text", text))
        q.put(("done", None))

    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run())
        except Exception as e:
            q.put(("error", str(e)))
        finally:
            loop.close()

    threading.Thread(target=_thread_target, daemon=True).start()
    return q


# ── LHS: Chat ─────────────────────────────────────────────────────────────────
with chat_col:
    st.markdown('<span id="trip-planning-chat" class="sr-only">Trip planning chat</span>', unsafe_allow_html=True)
    chat_head, clear_btn = st.columns([4, 1])
    chat_head.subheader("Trip Planning Chat")
    if clear_btn.button("Clear", use_container_width=True, help="Reset the conversation"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Chat cleared! 👋 I'm your World Cup 2026 travel planner. "
                    "Which match or city are you planning to visit?"
                ),
            }
        ]
        st.rerun()

    st.markdown('<p class="section-copy">Ask about matches, flights, stadium access, weather, fan zones, or accessible routes.</p>', unsafe_allow_html=True)
    mission_markup = _mission_card()
    if mission_markup:
        st.markdown(mission_markup, unsafe_allow_html=True)

    saved_markup = _saved_trip_cards()
    if saved_markup:
        with st.expander("Saved Trip Cards", expanded=False):
            st.markdown(saved_markup, unsafe_allow_html=True)

    with st.expander("Build a Multi-Step Mission", expanded=True):
        st.caption("Create a concrete task for the agent: plan, use tools, present next actions, then let you approve saving.")
        match_labels = [_match_label(match) for match in MATCHES]
        with st.form("mission_builder_form"):
            selected_label = st.selectbox("Match or event", match_labels, index=0)
            profile = st.session_state.accessibility_profile
            mission_origin = st.text_input("Starting point", value=profile["origin"])
            trip_days = st.slider("Trip length in days", min_value=1, max_value=7, value=3)
            include_saved_memory = st.checkbox("Ask agent to check saved MongoDB trip memory first", value=True)
            submitted = st.form_submit_button("Launch Mission", use_container_width=True)

        if submitted:
            selected_match = MATCHES[match_labels.index(selected_label)]
            venue = next(
                (venue for venue in VENUES if venue["venue_id"] == selected_match["venue_id"]),
                None,
            )
            venue_name = (venue or {}).get("name", selected_match["city_display"])
            profile = st.session_state.accessibility_profile
            profile_summary = (
                f"preferred language: {profile['language']}; "
                f"accessibility needs: {', '.join(profile['mobility_needs']) or 'none specified'}; "
                f"maximum walking: {profile['max_walking']}; "
                f"transit preference: {profile['transit_preference']}; "
                f"budget: {profile['budget']}; "
                f"crowd preference: {profile['crowd_sensitivity']}"
            )
            memory_instruction = (
                f"First, use MongoDB MCP `find` on `worldcup2026.itineraries` for user_id `{st.session_state.session_id}` if useful. "
                if include_saved_memory
                else ""
            )
            prompt = (
                "Launch a multi-step World Cup matchday mission. "
                f"{memory_instruction}"
                f"Plan a {trip_days}-day accessible trip from {mission_origin} for "
                f"{selected_match['team1']} vs {selected_match['team2']} on {selected_match['date']} "
                f"in {selected_match['city_display']} at {venue_name}. "
                f"{_kickoff_instruction(selected_match)} "
                f"Fixture source/status: {selected_match.get('source', 'local seed')} / "
                f"{selected_match.get('fixture_status', 'representative_demo')}. "
                f"My profile is: {profile_summary}. "
                "Use your tools: call `verify_fixture` for the selected fixture, call `resolve_fixture_venue` before claiming any venue is unavailable, look up fixture/venue data, call weather, call matchday planning, "
                "build a scannable mobile-friendly itinerary, include an accessibility route, "
                "crowd/safety guidance, a checklist, and a clear approval question before saving. "
                "Preserve the selected teams, date, and venue exactly unless a live official fixture source conflicts; "
                "if there is a conflict, label it as a fixture correction before continuing. "
                "When I approve saving, use MongoDB MCP `insert-one` into `worldcup2026.itineraries`; "
                "if MCP is unavailable, tell me to use the app's Save Latest Plan button, which keeps a local fallback."
            )
            st.session_state.current_mission = {
                "title": f"{selected_match['team1']} vs {selected_match['team2']} · {selected_match['city_display']}",
                "match": selected_match,
                "venue": venue_name,
                "origin": mission_origin,
                "trip_days": trip_days,
                "action": "Accessible trip mission",
            }
            _set_agent_prompt(
                prompt,
                f"Plan accessible trip: {selected_match['team1']} vs {selected_match['team2']} in {selected_match['city_display']}",
            )
            st.rerun()

    quick_cols = st.columns(len(_QUICK_PROMPTS))
    for index, (label, prompt) in enumerate(_QUICK_PROMPTS):
        if quick_cols[index].button(label, use_container_width=True, help=f"Ask: {prompt}"):
            _set_agent_prompt(prompt, label)
            st.rerun()

    chat_container = st.container(height=520, border=True)

    for msg in st.session_state.messages:
        avatar = _BOT_AVATAR if msg["role"] == "assistant" else None
        chat_container.chat_message(msg["role"], avatar=avatar).markdown(msg["content"])

    def _run_chat(user_input: str, display_text: str | None = None):
        shown_text = display_text or user_input
        st.session_state.messages.append({"role": "user", "content": shown_text})
        chat_container.chat_message("user").markdown(shown_text)

        with chat_container.chat_message("assistant", avatar=_BOT_AVATAR):
            placeholder = st.empty()
            placeholder.markdown(
                "<div class='typing-wrap' role='status' aria-label='Assistant is preparing a response' aria-live='polite'>"
                "<div class='t-dot' aria-hidden='true'></div>"
                "<div class='t-dot' aria-hidden='true'></div>"
                "<div class='t-dot' aria-hidden='true'></div>"
                "</div>",
                unsafe_allow_html=True,
            )
            q = get_agent_response_stream(user_input)
            full_text = ""
            while True:
                typ, data = q.get()
                if typ == "done":
                    break
                if typ == "error":
                    st.toast(f"Agent error: {data}", icon="❌")
                    full_text = full_text or "Sorry, something went wrong. Please try again."
                    break
                if typ == "text" and len(data) > len(full_text):
                    full_text = data
                    placeholder.markdown(full_text + " ▌")

            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
            # Push response text into the ARIA live region for screen readers
            escaped = full_text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')[:500]
            st.markdown(
                f'<div id="chat-live-region" aria-live="polite" aria-atomic="true" class="sr-only">{escaped}</div>',
                unsafe_allow_html=True,
            )
        st.rerun()

    if "_inject_prompt" in st.session_state:
        injected_prompt = st.session_state.pop("_inject_prompt")
        if isinstance(injected_prompt, dict):
            _run_chat(injected_prompt["prompt"], injected_prompt.get("display"))
        else:
            _run_chat(injected_prompt)

    if user_input := st.chat_input("Ask about any match, city, or trip…"):
        _run_chat(user_input)


with vis_col:
    st.subheader("Host City Dashboard")
    st.markdown(
        '<p class="section-copy">Filter host cities, inspect venues and scheduled matches, then hand the city context to the agent.</p>',
        unsafe_allow_html=True,
    )

    country_options = ["All"] + sorted({venue["country"] for venue in VENUES})
    phase_options = ["All"] + sorted({match["phase"] for match in MATCHES})
    layer_options = ["Match volume", "Heat/weather risk", "Crowd/exit risk", "Transit accessibility"]
    filter_col, phase_col, layer_col = st.columns(3)
    selected_country = filter_col.selectbox("Country", country_options)
    selected_phase = phase_col.selectbox("Match phase", phase_options)
    selected_layer = layer_col.selectbox("Map layer", layer_options)

    filtered_venues = [
        venue for venue in VENUES
        if selected_country == "All" or venue["country"] == selected_country
    ]
    filtered_venues = [
        venue for venue in filtered_venues
        if _matches_for_venue(venue["venue_id"], selected_phase)
    ]

    map_rows = _city_map_rows(filtered_venues, selected_phase, selected_layer)
    if map_rows:
        st.pydeck_chart(
            pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(latitude=38.5, longitude=-96, zoom=1.85, pitch=0),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=map_rows,
                        get_position="[lon, lat]",
                        get_radius="radius",
                        get_fill_color="color",
                        pickable=True,
                        opacity=0.8,
                        stroked=True,
                        get_line_color=[255, 255, 255],
                        line_width_min_pixels=1,
                    )
                ],
                tooltip={
                    "html": "<b>{city}</b><br/>{venue}<br/>{match_count} matches · {capacity} capacity<br/>{risk}",
                    "style": {"backgroundColor": "#111318", "color": "white"},
                },
            ),
            height=360,
            use_container_width=True,
        )
        # Text alternative for screen readers / keyboard-only users
        with st.expander("Map data as text (screen reader / keyboard alternative)", expanded=False):
            for row in map_rows:
                st.markdown(
                    f"**{row['city']}** — {row['venue']} · {row['match_count']} matches · "
                    f"{row['capacity']:,} capacity · {row['country']} · {row['risk']}"
                )
    else:
        st.info("No host cities match the current filters.")

    city_labels = [f"{venue['city_display']} · {venue['name']}" for venue in filtered_venues]
    if not city_labels:
        city_labels = [f"{venue['city_display']} · {venue['name']}" for venue in VENUES]
        filtered_venues = VENUES
    selected_city_label = st.selectbox("Selected host city", city_labels)
    selected_venue = filtered_venues[city_labels.index(selected_city_label)]
    selected_matches = _matches_for_venue(selected_venue["venue_id"], selected_phase)

    st.markdown(_venue_detail_markdown(selected_venue, selected_matches), unsafe_allow_html=True)
    st.markdown(_render_badges(_city_risk_badges(selected_venue)), unsafe_allow_html=True)

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Matches", len(selected_matches))
    metric_b.metric("Capacity", f"{selected_venue['capacity']:,}")
    metric_c.metric("Country", selected_venue["country"])

    with st.expander("Compare host cities"):
        compare_labels = [f"{venue['city_display']} · {venue['name']}" for venue in filtered_venues]
        default_compare = compare_labels[: min(3, len(compare_labels))]
        selected_compare = st.multiselect(
            "Choose 2-3 host cities",
            compare_labels,
            default=default_compare,
            max_selections=3,
        )
        compare_venues = [
            filtered_venues[compare_labels.index(label)]
            for label in selected_compare
        ]
        if compare_venues:
            st.dataframe(_comparison_rows(compare_venues, selected_phase), hide_index=True, use_container_width=True)
        if len(compare_venues) >= 2 and st.button("Ask Agent To Compare", use_container_width=True):
            _set_agent_prompt(
                _comparison_prompt(compare_venues, selected_phase),
                "Compare selected host cities",
                {
                    "title": "Host city comparison",
                    "venue": ", ".join(venue["city_display"] for venue in compare_venues),
                    "origin": st.session_state.accessibility_profile.get("origin", "Not set"),
                    "action": "City comparison",
                },
            )
            st.rerun()

    with st.expander("Matches at this venue", expanded=True):
        rows = [
            {
                "Date": match["date"],
                "Time ET": match["time_local"],
                "Match": f"{match['team1']} vs {match['team2']}",
                "Phase": match["phase"],
                "Group": match.get("group") or "",
            }
            for match in selected_matches
        ]
        st.dataframe(rows, hide_index=True, use_container_width=True)

    with st.expander("Transit, fan zone, and accessibility notes"):
        st.markdown(f"**Fan zone:** {selected_venue.get('fan_zone', 'Check FIFA host city guidance.')}")
        st.markdown(f"**Nearest airports:** {', '.join(selected_venue.get('nearest_airports', [])) or 'Check local airport options.'}")
        transport = selected_venue.get("transport", {})
        if isinstance(transport, dict) and transport:
            st.markdown("**Transport options**")
            for label, detail in transport.items():
                st.markdown(f"- **{label.replace('_', ' ').title()}:** {detail}")
        st.markdown(f"**Planning note:** {selected_venue.get('host_city_notes', 'Confirm venue guidance before travel.')}")

    action_cols = st.columns(2)
    if action_cols[0].button("Plan Accessible Trip", use_container_width=True):
        _set_agent_prompt(
            _city_action_prompt("plan", selected_venue, selected_matches),
            f"Plan accessible trip: {selected_venue['city_display']}",
            {
                "title": f"{selected_venue['city_display']} host city plan",
                "venue": selected_venue["name"],
                "origin": st.session_state.accessibility_profile.get("origin", "Not set"),
                "action": "Accessible city trip",
            },
        )
        st.rerun()
    if action_cols[1].button("Show Matches Here", use_container_width=True):
        _set_agent_prompt(
            _city_action_prompt("matches", selected_venue, selected_matches),
            f"Show matches: {selected_venue['city_display']}",
            {
                "title": f"{selected_venue['city_display']} match list",
                "venue": selected_venue["name"],
                "origin": st.session_state.accessibility_profile.get("origin", "Not set"),
                "action": "Venue match summary",
            },
        )
        st.rerun()
    compare_col, weather_col = st.columns(2)
    if compare_col.button("Compare City", use_container_width=True):
        _set_agent_prompt(
            _city_action_prompt("compare", selected_venue, selected_matches),
            f"Compare city: {selected_venue['city_display']}",
            {
                "title": f"{selected_venue['city_display']} comparison",
                "venue": selected_venue["name"],
                "origin": st.session_state.accessibility_profile.get("origin", "Not set"),
                "action": "City comparison",
            },
        )
        st.rerun()
    if weather_col.button("Weather Prep", use_container_width=True):
        _set_agent_prompt(
            _city_action_prompt("weather", selected_venue, selected_matches),
            f"Weather prep: {selected_venue['city_display']}",
            {
                "title": f"{selected_venue['city_display']} weather prep",
                "venue": selected_venue["name"],
                "origin": st.session_state.accessibility_profile.get("origin", "Not set"),
                "action": "Weather prep",
            },
        )
        st.rerun()
