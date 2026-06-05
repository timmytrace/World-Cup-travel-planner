"""
Weather tool – uses Open-Meteo (free, no API key required).

For match dates beyond the 16-day forecast window the tool falls back to
historical monthly averages stored in the WC data module.
"""

import requests
from datetime import date, datetime
from data.wc2026_data import CITY_WEATHER

# Coordinates for every host city
_CITY_COORDS: dict[str, tuple[float, float]] = {
    "new york / new jersey": (40.7128, -74.0060),
    "los angeles":           (34.0522, -118.2437),
    "dallas / fort worth":   (32.7767, -96.7970),
    "san francisco / bay area": (37.4030, -121.9700),
    "seattle":               (47.6062, -122.3321),
    "atlanta":               (33.7490, -84.3880),
    "miami":                 (25.7617, -80.1918),
    "philadelphia":          (39.9526, -75.1652),
    "kansas city":           (39.0997, -94.5786),
    "houston":               (29.7604, -95.3698),
    "boston":                (42.3601, -71.0589),
    "toronto":               (43.6532, -79.3832),
    "vancouver":             (49.2827, -123.1207),
    "mexico city":           (19.4326, -99.1332),
    "guadalajara":           (20.6597, -103.3496),
    "monterrey":             (25.6866, -100.3161),
}

_WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def get_weather_forecast(city: str, match_date: str) -> dict:
    """
    Return a weather forecast for a given host city on match day.

    Uses the Open-Meteo free API for dates within 16 days; falls back to
    historical monthly averages for future World Cup match dates.

    Args:
        city:       Host city name, e.g. "Dallas / Fort Worth" or "Miami".
        match_date: Date string in YYYY-MM-DD format, e.g. "2026-06-26".

    Returns:
        A dictionary with temperature, precipitation, and description fields.
    """
    city_key = city.strip().lower()
    coords = _CITY_COORDS.get(city_key)

    # Fuzzy match – try partial key lookup
    if not coords:
        for key, val in _CITY_COORDS.items():
            if city_key in key or key in city_key:
                coords = val
                city_key = key
                break

    if not coords:
        return {
            "error": f"City '{city}' not recognised. "
                     f"Available cities: {', '.join(_CITY_COORDS.keys())}"
        }

    try:
        target = datetime.strptime(match_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": f"Invalid date format '{match_date}'. Use YYYY-MM-DD."}

    days_ahead = (target - date.today()).days

    if 0 <= days_ahead <= 16:
        # ── Live forecast via Open-Meteo ──────────────────────────────────────
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude":  coords[0],
            "longitude": coords[1],
            "daily":     "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone":  "auto",
            "start_date": match_date,
            "end_date":   match_date,
        }
        try:
            resp = requests.get(url, params=params, timeout=8)
            resp.raise_for_status()
            d = resp.json().get("daily", {})
            code = d.get("weathercode", [None])[0]
            return {
                "source":        "live_forecast",
                "city":          city,
                "date":          match_date,
                "max_temp_c":    d.get("temperature_2m_max", [None])[0],
                "min_temp_c":    d.get("temperature_2m_min", [None])[0],
                "precipitation_mm": d.get("precipitation_sum", [0])[0],
                "condition":     _WMO_CODES.get(code, "Unknown"),
                "note":          "Live 16-day forecast from Open-Meteo.",
            }
        except Exception as exc:
            # Fall through to averages on any network error
            pass

    # ── Historical monthly averages ───────────────────────────────────────────
    city_display = city_key.title()
    weather_data = CITY_WEATHER.get(city_display) or CITY_WEATHER.get(city)
    if not weather_data:
        # Try to find by partial match
        for k, v in CITY_WEATHER.items():
            if city_key in k.lower() or k.lower() in city_key:
                weather_data = v
                break

    if weather_data:
        month_key = "june" if target.month == 6 else "july"
        avg = weather_data.get(month_key, {})
        return {
            "source":      "historical_average",
            "city":        city,
            "date":        match_date,
            "avg_high_c":  avg.get("avg_high_c"),
            "avg_low_c":   avg.get("avg_low_c"),
            "rain_days_in_month": avg.get("rain_days"),
            "condition":   avg.get("description", "Data not available"),
            "note":        "Historical monthly average (match is beyond live forecast range).",
        }

    return {
        "source": "unavailable",
        "city":   city,
        "date":   match_date,
        "note":   "Weather data not available for this city.",
    }
