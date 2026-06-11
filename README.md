# ⚽ WE ARE 26 — World Cup 2026 Fan Companion

> An intelligent, accessible, multilingual AI travel and matchday safety planning agent for the 2026 FIFA World Cup.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-ff4b4b)](https://streamlit.io/)
[![MongoDB Atlas](https://img.shields.io/badge/database-MongoDB%20Atlas-47A248)](https://www.mongodb.com/atlas)
[![Gemini](https://img.shields.io/badge/AI-Gemini%203.1%20Pro-4285F4)](https://ai.google.dev/)

---

## 🎯 What It Does

The **WC 2026 Fan Companion** is a conversational AI agent that helps every kind of fan — regardless of language, mobility, budget, or tech experience — plan their trip to the 2026 FIFA World Cup across 16 host cities in the USA, Canada, and Mexico.

**It goes far beyond a chatbot:**

- 🗓️ **Verifies real fixtures** against a 104-match schedule + live API
- 🏟️ **Resolves venues** with real stadium details, accessibility routes, and transit options
- 🌤️ **Fetches live weather** for match dates via Open-Meteo
- 🚇 **Builds full matchday plans** — departure timeline, crowd surge warnings, prohibited items, local food tips, emergency numbers
- 💾 **Saves itineraries** to MongoDB Atlas via MCP and retrieves them in future sessions
- ♿ **Accessibility-first** — mobility needs, language, crowd sensitivity, and walking tolerance are hard planning constraints

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                Streamlit UI (app.py)             │
│  Chat  │  Host City Map  │  Mission Builder      │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │   Google ADK Agent  │
         │  gemini-3.1-pro     │
         └─────────┬───────────┘
                   │  tools
    ┌──────────────┼──────────────────────┐
    │              │                      │
    ▼              ▼                      ▼
get_live_     verify_fixture +      get_matchday_plan
fixtures()    resolve_venue()       get_weather()
(football-    (104-fixture          (Open-Meteo API)
data.org)      local schedule)
                   │
                   ▼
         MongoDB Atlas MCP
         (worldcup2026 DB)
         ├── venues (16 docs)
         ├── matches (125 docs)
         ├── city_weather (16 docs)
         └── itineraries (user-saved)
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Node.js 18+ (for MongoDB MCP server)
- A [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) free cluster
- A [Google AI Studio](https://aistudio.google.com/app/apikey) API key
- A [football-data.org](https://www.football-data.org/client/register) free API key

### 2. Install the MongoDB MCP server

```bash
npm install -g mongodb-mcp-server
```

### 3. Clone and install Python dependencies

```bash
git clone https://github.com/YOUR_USERNAME/wc2026-fan-companion.git
cd wc2026-fan-companion

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
GOOGLE_API_KEY=your_google_ai_api_key
FOOTBALL_DATA_API_KEY=your_football_data_api_key
```

### 5. Seed the database

```bash
# Seed base data (matches, venues, city weather)
python -m data.seed

# Seed enriched venue data (transit, crowd zones, safety tips)
python seed_venues.py
```

### 6. Run the app

```bash
python -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Cloud Run and MongoDB Atlas

Atlas only accepts connections from addresses in the project's IP access list.
Cloud Run uses a dynamic outbound IP pool unless static egress is configured.

For a short-lived demo, you can temporarily add `0.0.0.0/0` in Atlas under
**Network Access**, record the demo, and remove the rule immediately afterward.
Use a strong database password and a least-privilege database user. This is not
recommended for production.

For production, route Cloud Run outbound traffic through a VPC and Cloud NAT
with a reserved static IP, then allow only that IP as a `/32` entry in Atlas.
Store the full `mongodb+srv://...` URI in Secret Manager and expose it to the
service as `MONGODB_URI`.

The container installs system CA certificates and PyMongo uses the `certifi`
root bundle. Do not disable certificate verification or add
`tlsAllowInvalidCertificates=true`.

After changing Atlas access or the MongoDB secret, deploy a new Cloud Run
revision and confirm that the service logs contain a successful MongoDB ping.

---

## 🧰 Tools & Agent Capabilities

| Tool | What it does |
|---|---|
| `get_live_fixtures` | Fetches live WC 2026 fixture data from football-data.org API |
| `verify_fixture` | Validates a fixture against the local 104-match schedule with team alias resolution |
| `resolve_fixture_venue` | Joins fixture to stadium record; never returns "venue unavailable" if data exists |
| `get_weather_forecast` | Live 16-day forecast via Open-Meteo; falls back to historical monthly averages |
| `get_matchday_plan` | Full matchday guide: timeline, transit, crowd surge zones, food, safety, prohibited items |
| MongoDB MCP `find` | Retrieves saved itineraries, venue enrichment, and match data from Atlas |
| MongoDB MCP `insert-one` | Persists approved itineraries to Atlas after user approval |

---

## ♿ Accessibility Features

- **Screen reader support** — ARIA live regions announce agent responses; typing indicator has `role="status"`
- **Keyboard navigation** — skip-to-chat link; all interactive elements have visible focus outlines
- **Reduced motion** — `@media (prefers-reduced-motion: reduce)` disables all animations
- **High contrast mode** — `@media (forced-colors: active)` applies system colours to all cards
- **Touch targets** — minimum 44px touch targets throughout; 16px input font prevents iOS zoom
- **Map fallback** — "Map data as text" expander provides full venue data for screen readers
- **Multilingual** — agent responds in the fan's preferred language (Spanish, French, Portuguese, German, Arabic, Japanese)
- **Mobility profiles** — step-free routes, wheelchair seating, low-walking and sensory-friendly options as hard constraints

---

## 📱 Device Support

| Device | Layout |
|---|---|
| Desktop (1200px+) | Two-column: chat left, map/dashboard right |
| Tablet / iPad (768–1199px) | Reduced grid, collapsible sidebar |
| Mobile (≤640px) | Single column, stacked sections, collapsible sidebar |

---

## 🗂️ Project Structure

```
├── app.py                    # Streamlit UI
├── main.py                   # CLI runner for testing
├── requirements.txt
├── seed_venues.py            # Enriched venue seeder (transit, safety, crowd zones)
├── .env.example
├── fan_companion/
│   ├── agent.py              # Google ADK agent definition
│   ├── __init__.py
│   └── tools/
│       ├── fixtures_tool.py          # Live fixtures API
│       ├── fixture_verification_tool.py  # Local schedule verification
│       ├── venue_resolution_tool.py  # Venue lookup and joining
│       ├── weather_tools.py          # Weather forecast
│       └── matchday_tool.py          # Full matchday plan builder
├── data/
│   ├── wc2026_data.py        # 16 venues + 104 fixtures + city weather
│   ├── seed.py               # Base MongoDB seeder
│   └── verified_schedule.py
└── scripts/
    └── cleanup_venues.py
```

---

## 🌍 Host Cities Covered

USA: New York/NJ · Los Angeles · Dallas/Fort Worth · San Francisco/Bay Area · Seattle · Atlanta · Miami · Philadelphia · Kansas City · Houston · Boston  
Canada: Toronto · Vancouver  
Mexico: Mexico City · Guadalajara · Monterrey

---

## 🔑 Partner Integration

This project uses **MongoDB Atlas** as the MCP partner:

- **MCP server**: `mongodb-mcp-server` (npm)
- **Database**: `worldcup2026` on MongoDB Atlas
- **Collections**: `venues`, `matches`, `city_weather`, `itineraries`, `config`
- **Operations used by agent**: `find`, `insert-one`, `update-one`

The MongoDB MCP integration provides the agent's long-term memory — saved itineraries persist across sessions and are retrievable by user/session ID.

---

## 📄 License

[MIT](LICENSE) © 2026
