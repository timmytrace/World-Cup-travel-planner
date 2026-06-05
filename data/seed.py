"""
Seed MongoDB Atlas with 2026 World Cup data.

Usage:
    1. Copy .env.example → .env and fill in your MONGODB_URI
    2. Run:  python -m data.seed
"""

import sys
import os
from pathlib import Path

# Allow running as  python -m data.seed  from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import BulkWriteError

from data.wc2026_data import VENUES, MATCHES, CITY_WEATHER

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "worldcup2026"


def seed(uri: str = MONGODB_URI, db_name: str = DB_NAME) -> None:
    if not uri:
        raise ValueError(
            "MONGODB_URI is not set. Copy .env.example → .env and add your Atlas connection string."
        )

    client = MongoClient(uri)
    db = client[db_name]

    # ── Venues ──────────────────────────────────────────────────────────────────
    print("Seeding venues …")
    db.venues.drop()
    db.venues.insert_many(VENUES)
    db.venues.create_index([("venue_id", ASCENDING)], unique=True)
    db.venues.create_index([("city_display", TEXT), ("name", TEXT)])
    db.venues.create_index([("country", ASCENDING)])
    print(f"  ✓ {db.venues.count_documents({})} venues inserted")

    # ── Matches ─────────────────────────────────────────────────────────────────
    print("Seeding matches …")
    db.matches.drop()
    db.matches.insert_many(MATCHES)
    db.matches.create_index([("match_id", ASCENDING)], unique=True)
    db.matches.create_index([("team1", TEXT), ("team2", TEXT)])
    db.matches.create_index([("venue_id", ASCENDING)])
    db.matches.create_index([("date", ASCENDING)])
    db.matches.create_index([("phase", ASCENDING)])
    print(f"  ✓ {db.matches.count_documents({})} matches inserted")

    # ── City weather ─────────────────────────────────────────────────────────────
    print("Seeding city weather …")
    db.city_weather.drop()
    weather_docs = [
        {"city_display": city, **data} for city, data in CITY_WEATHER.items()
    ]
    db.city_weather.insert_many(weather_docs)
    db.city_weather.create_index([("city_display", ASCENDING)])
    print(f"  ✓ {db.city_weather.count_documents({})} city weather records inserted")

    # ── Itineraries (empty – written by the agent at runtime) ────────────────────
    print("Preparing itineraries collection …")
    if "itineraries" not in db.list_collection_names():
        db.create_collection("itineraries")
    db.itineraries.create_index([("user_id", ASCENDING)])
    db.itineraries.create_index([("created_at", ASCENDING)])
    print("  ✓ itineraries collection ready")

    client.close()
    print(f"\nAll done! Database '{db_name}' is seeded and ready.")


if __name__ == "__main__":
    seed()
