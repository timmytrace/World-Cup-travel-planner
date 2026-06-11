"""
Matchday Travel & Safety Assistant tool.

Given a fan's starting location, venue, and match details, this tool returns
a fully structured matchday plan: timeline, transport options, crowd surge
warnings, safety tips, prohibited items, and weather — all ready for the
agent to narrate (and translate if needed).

Venue data is fetched LIVE from MongoDB Atlas (worldcup2026.venues).
Weather is fetched LIVE from Open-Meteo API.
"""

import os
import re
import httpx
from datetime import datetime, timedelta
from data.wc2026_data import CITY_WEATHER, VENUES
from fan_companion.mongo import create_mongo_client


def _query_local_venue(venue_hint: str) -> dict | None:
    hint = venue_hint.strip().lower()
    for venue in VENUES:
        searchable = " ".join(
            str(venue.get(key, ""))
            for key in ("venue_id", "name", "city", "city_display", "country")
        ).lower()
        if hint in searchable or any(part and part in searchable for part in hint.split()):
            return venue
    return None


def _query_mongo(venue_hint: str) -> tuple[dict | None, list]:
    """
    Single Atlas connection: fetch venue doc + global safety tips.
    Returns (venue_doc, safety_tips). Both may be None/[] on failure.
    """
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None, []
    try:
        with create_mongo_client(uri, timeout_ms=8_000) as client:
            db = client["worldcup2026"]
            hint = venue_hint.strip().lower()
            venue_doc = db.venues.find_one(
                {
                    "$or": [
                        {"venue_id": hint},
                        {"aliases": hint},
                        {"name": {"$regex": re.escape(hint), "$options": "i"}},
                        {"city": {"$regex": re.escape(hint), "$options": "i"}},
                        {"aliases": {"$regex": re.escape(hint), "$options": "i"}},
                    ]
                },
                {"_id": 0},
            )
            cfg = db.config.find_one({"key": "safety_tips"}, {"_id": 0})
            safety_tips = (cfg or {}).get("tips", [])
        return venue_doc, safety_tips
    except Exception:
        return None, []




def _wmo_label(code: int) -> str:
    table = {
        0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
        45: "Foggy 🌫️", 48: "Freezing fog 🌫️",
        51: "Light drizzle 🌦️", 53: "Moderate drizzle 🌦️", 55: "Dense drizzle 🌧️",
        61: "Slight rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
        71: "Light snow ❄️", 73: "Moderate snow ❄️", 75: "Heavy snow ❄️",
        80: "Light showers 🌦️", 81: "Moderate showers 🌧️", 82: "Violent showers ⛈️",
        95: "Thunderstorm ⛈️", 96: "Thunderstorm with hail ⛈️",
    }
    return table.get(code, "Mixed conditions 🌡️")


def _get_weather(lat: float | None, lon: float | None, date: str) -> dict:
    if lat is None or lon is None:
        return {"summary": "Weather data not available for this venue."}
    try:
        r = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                "timezone": "auto", "start_date": date, "end_date": date,
            },
            timeout=8,
        )
        if r.status_code != 200:
            return {"summary": "Weather forecast temporarily unavailable."}
        d = r.json().get("daily", {})
        max_t = (d.get("temperature_2m_max") or [None])[0]
        min_t = (d.get("temperature_2m_min") or [None])[0]
        rain  = (d.get("precipitation_sum") or [0.0])[0] or 0.0
        code  = (d.get("weathercode") or [0])[0] or 0
        label = _wmo_label(code)
        poncho = " Bring a rain poncho!" if rain > 2 else ""
        return {
            "condition": label,
            "high_c": max_t, "low_c": min_t, "rain_mm": rain,
            "summary": f"{label}. High {max_t}°C / Low {min_t}°C."
                       + (f" Rain expected: {rain} mm.{poncho}" if rain > 0.5 else ""),
        }
    except Exception:
        return {"summary": "Weather forecast temporarily unavailable."}


def _get_weather_average(city: str, date: str) -> dict:
    try:
        target = datetime.strptime(date, "%Y-%m-%d")
        month_key = "june" if target.month == 6 else "july"
    except ValueError:
        month_key = "june"

    city_key = city.strip().lower()
    weather_data = None
    for name, values in CITY_WEATHER.items():
        name_key = name.lower()
        if city_key in name_key or name_key in city_key or any(part and part in name_key for part in city_key.split()):
            weather_data = values
            city = name
            break

    if not weather_data:
        return {"summary": "Weather data not available for this venue."}

    avg = weather_data.get(month_key, {})
    return {
        "condition": avg.get("description", "Historical average"),
        "high_c": avg.get("avg_high_c"),
        "low_c": avg.get("avg_low_c"),
        "rain_days_in_month": avg.get("rain_days"),
        "summary": (
            f"Historical {month_key.title()} average for {city}: "
            f"high {avg.get('avg_high_c')}°C / low {avg.get('avg_low_c')}°C. "
            f"{avg.get('description', '')}"
        ),
    }



def get_matchday_plan(
    starting_location: str,
    venue_name: str,
    match_date: str,
    kickoff_time: str = "18:00",
    language: str = "English",
) -> dict:
    """
    Build a personalised matchday travel and safety plan for a World Cup 2026 fan.

    Args:
        starting_location: Where the fan is starting from (e.g. "Union Station, Toronto",
                           "Downtown Miami hotel", "Times Square New York").
        venue_name:        Stadium name or host city (e.g. "BMO Field", "Toronto",
                           "MetLife Stadium", "Estadio Azteca").
        match_date:        Match date in YYYY-MM-DD format (e.g. "2026-06-15").
        kickoff_time:      Local kickoff time in HH:MM 24-h format (default "18:00").
        language:          Language for the plan — English, Spanish, French, Portuguese,
                           German, Arabic, Japanese, etc.

    Returns:
        A structured dict with timeline, transit options, crowd warnings, safety tips,
        weather, prohibited items, fan zone, emergency numbers, and local food tips.
        The agent should narrate this as a friendly, readable matchday guide.
    """
    venue, safety_tips = _query_mongo(venue_name)
    if not venue:
        venue = _query_local_venue(venue_name)
    venue_key = (venue or {}).get("name", venue_name)
    city = (venue or {}).get("city_display") or (venue or {}).get("city", venue_name)
    lat = (venue or {}).get("lat") or (venue or {}).get("latitude")
    lon = (venue or {}).get("lon") or (venue or {}).get("longitude")

    # ── Build timeline ────────────────────────────────────────────────────────
    timeline = {}
    try:
        y, mo, day = map(int, match_date.split("-"))
        kh, km = map(int, kickoff_time.split(":"))
        ko = datetime(y, mo, day, kh, km)
        gates_open_h = (venue or {}).get("gates_open_hours_before", 2.0)
        timeline = {
            "pre_match_meal":        (ko - timedelta(hours=4)).strftime("%H:%M"),
            "recommended_departure": (ko - timedelta(hours=3)).strftime("%H:%M"),
            "gates_open":            (ko - timedelta(hours=gates_open_h)).strftime("%H:%M"),
            "kickoff":               ko.strftime("%H:%M"),
            "post_match_exit":       (ko + timedelta(hours=2)).strftime("%H:%M"),
            "note": "Allow extra time if travelling from far outside the city centre.",
        }
    except Exception:
        timeline = {
            "pre_match_meal": "~4 hrs before kickoff",
            "recommended_departure": "~3 hrs before kickoff",
            "gates_open": f"~{(venue or {}).get('gates_open_hours_before', 2)} hrs before kickoff",
            "kickoff": kickoff_time,
            "post_match_exit": "~2 hrs after kickoff",
        }

    # ── Weather (coordinates fetched from MongoDB venue doc) ─────────────────
    weather = _get_weather(lat, lon, match_date)
    if "unavailable" in weather.get("summary", "").lower():
        weather = _get_weather_average(city, match_date)

    # ── Assemble plan ─────────────────────────────────────────────────────────
    # Normalise transit options: prefer a 'transit' list; fall back to converting
    # the 'transport' dict into a list of strings; final fallback is a generic tip.
    raw_transit = (venue or {}).get("transit") or (venue or {}).get("transport")
    if isinstance(raw_transit, dict):
        transit_options = [
            f"{k.replace('_', ' ').title()}: {v}" for k, v in raw_transit.items()
        ]
    elif isinstance(raw_transit, list):
        transit_options = raw_transit
    else:
        transit_options = ["Check local transit authority website for game-day services."]

    plan = {
        "starting_location": starting_location,
        "venue": venue_key.title() if venue else venue_name,
        "city": city,
        "country": (venue or {}).get("country", ""),
        "match_date": match_date,
        "kickoff_time": kickoff_time,
        "language_requested": language,
        "weather": weather,
        "timeline": timeline,
        "transit_options": transit_options,
        "crowd_surge_zones": (venue or {}).get("crowd_surge_zones", []),
        "parking": (venue or {}).get("parking") or (venue or {}).get("transport", {}).get("parking", "See official venue guide."),
        "fan_zone": (venue or {}).get("fan_zone", "Check FIFA official fan zone listings."),
        "prohibited_items": (venue or {}).get("prohibited", ["Check FIFA venue guide for full prohibited items list."]),
        "accessibility": (venue or {}).get("accessibility", "Contact venue for accessibility information."),
        "emergency_number": (venue or {}).get("emergency", "911 (USA/Canada) · 911 (Mexico)"),
        "local_food_tips": (venue or {}).get("local_tips", []),
        "universal_safety_tips": safety_tips,
        "language_note": (
            f"This plan is in English. "
            + (f"Ask the agent to translate the full plan into {language}." if language.lower() != "english" else "")
        ),
    }

    return plan
