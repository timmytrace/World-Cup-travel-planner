"""One-time cleanup: remove stale venue docs with wrong IDs, verify enrichment."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"), serverSelectionTimeoutMS=8000)
db = client["worldcup2026"]

print("Before cleanup:", db.venues.count_documents({}), "venue docs")

# Check if the correctly-IDed docs have enriched fields
metlife = db.venues.find_one({"venue_id": "metlife"}, {"_id": 0})
print("metlife keys:", list(metlife.keys()) if metlife else "NOT FOUND")
print("Has transit:", "transit" in (metlife or {}))
print("Has crowd_surge_zones:", "crowd_surge_zones" in (metlife or {}))
print()

# Remove stale old-ID docs that were inserted before the venue_id fix
stale_ids = [
    "bmo field", "at&t stadium", "metlife stadium", "hard rock stadium",
    "sofi stadium", "mercedes-benz stadium", "levi's stadium",
    "arrowhead stadium", "lumen field", "gillette stadium", "nrg stadium",
    "lincoln financial field", "bc place",
    "estadio azteca", "estadio akron", "estadio bbva",
]
result = db.venues.delete_many({"venue_id": {"$in": stale_ids}})
print(f"Deleted {result.deleted_count} stale venue docs")
print("After cleanup:", db.venues.count_documents({}), "venue docs")

client.close()
