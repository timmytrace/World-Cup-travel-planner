"""
One-time script: seeds WC 2026 venue data into MongoDB Atlas (worldcup2026.venues).
Run once: python seed_venues.py
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

load_dotenv()

VENUES = [
    {
        "venue_id": "bmo",
        "name": "BMO Field",
        "city": "Toronto", "country": "Canada", "capacity": 30_000,
        "lat": 43.6532, "lon": -79.3832,
        "transit": [
            "🚋 509/510 streetcar from Union Station to Exhibition Loop",
            "🚆 GO Train to Exhibition GO Station (game-day service)",
            "🚌 King St. or Bathurst St. buses to Exhibition Place",
        ],
        "crowd_surge_zones": ["Bremner Blvd (post-match)", "Rees St exit", "Lake Shore Blvd W ramp"],
        "gates_open_hours_before": 2.5,
        "parking": "Limited. Use Exhibition Place lots (pre-book). No stadium parking for general public.",
        "fan_zone": "Ontario Place / Budweiser Stage waterfront area",
        "emergency": "911 (Canada)",
        "prohibited": ["Bags > 30×30×15 cm", "Glass containers", "Umbrellas with metal tips", "Drones"],
        "accessibility": "Accessible streetcar stop at Exhibition Place. Wheelchair section at south end.",
        "local_tips": [
            "Grab poutine or a CN Tower-view meal at Rees St restaurants before heading in.",
            "The waterfront path along Lake Ontario is perfect for post-match walks.",
            "Rogers Centre / Scotiabank Arena area has good sports bars if you miss kick-off.",
        ],
        "aliases": ["toronto", "bmo"],
    },
    {
        "venue_id": "att",
        "name": "AT&T Stadium",
        "city": "Arlington / Dallas", "country": "USA", "capacity": 80_000,
        "lat": 32.7357, "lon": -97.1081,
        "transit": [
            "🚆 TRE (Trinity Railway Express) to CentrePort/DFW, then shuttle to stadium",
            "🚌 Dedicated game-day shuttle buses from downtown Dallas/Fort Worth",
            "🚗 Uber/Lyft drop-off at Legends Way",
        ],
        "crowd_surge_zones": ["Collins St after final whistle", "Randol Mill Rd intersections", "West parking structures"],
        "gates_open_hours_before": 2.0,
        "parking": "Cowboys Way lot is closest. Pre-purchase via SeatGeek. Expect $30–60.",
        "fan_zone": "Arlington Entertainment District (Globe Life Field area)",
        "emergency": "911 (USA)",
        "prohibited": ["Bags > 14×14×6 in", "Outside food/drink", "Selfie sticks > 6 in", "Laser pointers"],
        "accessibility": "ADA parking in Lot 1. Accessible entrances at all gates.",
        "local_tips": [
            "Deep ellum in Dallas has great pre-match energy — bars and Tex-Mex 30 min away.",
            "Heat warning: June/July temperatures regularly exceed 37°C. Hydrate and wear sunscreen.",
            "AT&T Stadium has air conditioning inside — a welcome relief!",
        ],
        "aliases": ["dallas", "arlington", "att stadium"],
    },
    {
        "venue_id": "metlife",
        "name": "MetLife Stadium",
        "city": "New York / New Jersey", "country": "USA", "capacity": 82_500,
        "lat": 40.8135, "lon": -74.0745,
        "transit": [
            "🚆 NJ Transit direct Meadowlands Station service on match days",
            "🚌 MetLife Stadium Express bus from Port Authority Bus Terminal (NYC)",
            "🚕 Uber/Lyft drop-off at MetLife Way (budget 45–60 min from Manhattan)",
        ],
        "crowd_surge_zones": ["NJ Transit platform (post-match rush)", "Route 3 East on-ramps", "Lot F parking structure exit"],
        "gates_open_hours_before": 2.0,
        "parking": "Pre-book via SeatGeek/ParkWhiz. Arrive 3+ hrs early to avoid gridlock.",
        "fan_zone": "NYC FIFA Fan Festival (Times Square / Central Park area)",
        "emergency": "911 (USA/NJ)",
        "prohibited": ["Bags > 12×12×6 in", "Outside beverages", "Selfie sticks"],
        "accessibility": "ADA lots adjacent to gates. Accessible seating on all levels.",
        "local_tips": [
            "NJ Transit train is by far the easiest — avoid driving if possible.",
            "NYC fan zones are massive. Get there early — capacity fills fast.",
            "The post-match NJ Transit queue can be 45+ min. Have a plan.",
        ],
        "aliases": ["new york", "new jersey", "nyc", "metlife"],
    },
    {
        "venue_id": "hardrock",
        "name": "Hard Rock Stadium",
        "city": "Miami", "country": "USA", "capacity": 65_326,
        "lat": 25.7617, "lon": -80.1918,
        "transit": [
            "🚇 Metrorail Orange/Green Line to Dolphin Station, then free shuttle",
            "🚆 Brightline from downtown Miami to Aventura (closest station with shuttle)",
            "🚗 Palmetto Expressway SR-826 — Exits 12A/12B for stadium",
        ],
        "crowd_surge_zones": ["NW 199th St post-match", "Dolphin Expressway SR-836 on-ramps", "Tailgate lots C/D exit"],
        "gates_open_hours_before": 2.0,
        "parking": "Tailgate lots open 5 hrs before. Book via Ticketmaster. Expect $40–80.",
        "fan_zone": "Bayfront Park / FTX Arena waterfront in downtown Miami",
        "emergency": "911 (USA/FL)",
        "prohibited": ["Bags > 14×14×6 in", "Outside food/drink", "Weapons/pepper spray"],
        "accessibility": "ADA parking in Lot J. Blue Lot accessible drop-off.",
        "local_tips": [
            "Miami heat + humidity in June is intense. Wear light clothing and stay hydrated.",
            "Little Havana is 20 min from the stadium — amazing Cuban food.",
            "Post-match: Wynwood Walls area is lively for celebrations.",
        ],
        "aliases": ["miami", "hard rock"],
    },
    {
        "venue_id": "sofi",
        "name": "SoFi Stadium",
        "city": "Los Angeles", "country": "USA", "capacity": 70_240,
        "lat": 34.0522, "lon": -118.2437,
        "transit": [
            "🚇 Metro C Line (Green) to Hawthorne/Lennox, then rideshare",
            "🚌 Dedicated game-day shuttle from several Metro stations",
            "🚗 I-405 — Exit La Tijera Blvd. Budget 90 min from downtown LA.",
        ],
        "crowd_surge_zones": ["Prairie Ave post-match", "Manchester Blvd / I-405 on-ramps", "Parking Garage A exit"],
        "gates_open_hours_before": 2.5,
        "parking": "Pre-book via SoFi Stadium parking portal. $50–100.",
        "fan_zone": "LA Live / Crypto.com Arena entertainment complex",
        "emergency": "911 (USA/CA)",
        "prohibited": ["Bags > 14×14×6 in", "Drones", "Outside food/drink"],
        "accessibility": "ADA Level 1 parking. Accessible entrances at all gates.",
        "local_tips": [
            "LA traffic is legendary. Give yourself 90+ min even from central LA.",
            "Venice Beach and Santa Monica are great for the day before.",
            "Hollywood Walk of Fame / Sunset Strip bars are perfect for pre/post-match.",
        ],
        "aliases": ["los angeles", "la", "sofi", "inglewood"],
    },
    {
        "venue_id": "mercedesbenz",
        "name": "Mercedes-Benz Stadium",
        "city": "Atlanta", "country": "USA", "capacity": 71_000,
        "lat": 33.7490, "lon": -84.3880,
        "transit": [
            "🚇 MARTA Red/Gold Line to Vine City or GWCC/CNN Center station",
            "🚌 Dedicated game-day shuttles from key MARTA park-and-rides",
        ],
        "crowd_surge_zones": ["Martin Luther King Jr. Dr post-match", "Ted Turner Dr / Ivan Allen Jr Blvd"],
        "gates_open_hours_before": 2.0,
        "parking": "On-site pre-book. GWCC lots recommended.",
        "fan_zone": "Centennial Olympic Park / Buckhead Village",
        "emergency": "911 (USA/GA)",
        "prohibited": ["Bags > 14×14×6 in", "Outside beverages"],
        "accessibility": "MARTA fully accessible. ADA section on Level 100.",
        "local_tips": [
            "Atlanta is extremely walkable from the stadium to downtown.",
            "The Beltline trail connects many fan-friendly neighborhoods.",
        ],
        "aliases": ["atlanta", "mercedes benz", "mb stadium"],
    },
    {
        "venue_id": "levis",
        "name": "Levi's Stadium",
        "city": "San Francisco / Santa Clara", "country": "USA", "capacity": 68_500,
        "lat": 37.3387, "lon": -121.8853,
        "transit": [
            "🚇 VTA Light Rail to Great America Station (directly adjacent)",
            "🚆 Caltrain to Mountain View, then VTA 522 BRT",
            "🚌 Game-day shuttles from multiple Bay Area transit hubs",
        ],
        "crowd_surge_zones": ["Tasman Dr post-match", "Great America Pkwy / US-101 on-ramps"],
        "gates_open_hours_before": 2.5,
        "parking": "Pre-book via Levi's Stadium app. $30–50.",
        "fan_zone": "San Francisco Ferry Building / Embarcadero waterfront",
        "emergency": "911 (USA/CA)",
        "prohibited": ["Bags > 14×14×6 in", "Outside food/drink"],
        "accessibility": "VTA light rail fully accessible. ADA sections on all levels.",
        "local_tips": [
            "SF proper is 45 min by Caltrain — budget extra time.",
            "Santana Row (2 min walk) has excellent pre-match restaurants.",
        ],
        "aliases": ["san francisco", "santa clara", "levis", "levi stadium", "bay area"],
    },
    {
        "venue_id": "arrowhead",
        "name": "Arrowhead Stadium",
        "city": "Kansas City", "country": "USA", "capacity": 76_416,
        "lat": 38.8197, "lon": -94.4847,
        "transit": [
            "🚌 KC Streetcar (limited range) + rideshare",
            "🚗 I-70 East to Blue Ridge Cutoff. Arrive 2+ hrs early.",
        ],
        "crowd_surge_zones": ["Truman Rd post-match", "I-70 East on-ramps", "Lot A/B exit bottlenecks"],
        "gates_open_hours_before": 2.0,
        "parking": "Chiefs parking lots. Pre-purchase required.",
        "fan_zone": "Power & Light District in downtown KC",
        "emergency": "911 (USA/MO)",
        "prohibited": ["Bags > 14×14×6 in", "Outside beverages"],
        "accessibility": "ADA parking in Lot M.",
        "local_tips": [
            "KC BBQ is world-famous — Joe's KC or Jack Stack for a pre-match feast.",
            "Power & Light District is the place for post-match celebrations.",
        ],
        "aliases": ["kansas city", "kc", "arrowhead"],
    },
    {
        "venue_id": "lumen",
        "name": "Lumen Field",
        "city": "Seattle", "country": "USA", "capacity": 69_000,
        "lat": 47.6062, "lon": -122.3321,
        "transit": [
            "🚇 Link Light Rail to SODO station (5 min walk)",
            "🚢 Water Taxi from West Seattle",
            "🚌 King County Metro buses along 1st Ave S",
        ],
        "crowd_surge_zones": ["Occidental Ave post-match", "1st Ave S / Edgar Martinez Dr"],
        "gates_open_hours_before": 2.0,
        "parking": "Very limited. Use transit. Paid lots on 1st Ave S.",
        "fan_zone": "Pike Place Market / Capitol Hill",
        "emergency": "911 (USA/WA)",
        "prohibited": ["Bags > 14×14×6 in"],
        "accessibility": "Light Rail fully accessible. ADA section at south end zone.",
        "local_tips": [
            "Seattle is very transit-friendly — the Link Light Rail is the best option.",
            "Pike Place Market for a pre-match morning, then SODO bars for build-up.",
        ],
        "aliases": ["seattle", "lumen"],
    },
    {
        "venue_id": "gillette",
        "name": "Gillette Stadium",
        "city": "Boston / Foxborough", "country": "USA", "capacity": 65_878,
        "lat": 42.0909, "lon": -71.2643,
        "transit": [
            "🚆 MBTA Commuter Rail (Providence/Stoughton Line) to Foxboro Station on match days",
            "🚌 Game-day bus from South Station, Boston",
        ],
        "crowd_surge_zones": ["Rt 1 North post-match", "Patriot Place parking exits", "MBTA platform surge"],
        "gates_open_hours_before": 2.0,
        "parking": "Patriot Place lots. Pre-book. $40+.",
        "fan_zone": "Faneuil Hall / TD Garden area in Boston",
        "emergency": "911 (USA/MA)",
        "prohibited": ["Bags > 14×14×6 in", "Outside food/drink"],
        "accessibility": "Commuter Rail accessible. ADA section at all levels.",
        "local_tips": [
            "Foxborough is 45 min from downtown Boston by commuter rail.",
            "Patriot Place has great dining right at the stadium.",
            "Boston is a world-class fan city — Fenway area is buzzing on match days.",
        ],
        "aliases": ["boston", "foxborough", "gillette", "new england"],
    },
    {
        "venue_id": "nrg",
        "name": "NRG Stadium",
        "city": "Houston", "country": "USA", "capacity": 72_220,
        "lat": 29.6847, "lon": -95.4107,
        "transit": [
            "🚇 METRORail Red Line to NRG Park Station",
            "🚌 Game-day Park & Ride shuttle from Reliant Park",
        ],
        "crowd_surge_zones": ["Kirby Dr post-match", "Main St / I-610 Loop ramps"],
        "gates_open_hours_before": 2.0,
        "parking": "NRG lots — pre-purchase. Lots B/C closest.",
        "fan_zone": "Discovery Green / Midtown Houston",
        "emergency": "911 (USA/TX)",
        "prohibited": ["Bags > 14×14×6 in", "Outside food/drink"],
        "accessibility": "METRORail accessible. ADA parking in Lot A.",
        "local_tips": [
            "Houston heat rivals Dallas — June temperatures hit 38°C+ with humidity.",
            "The Museum District / Hermann Park is beautiful for a pre-match stroll.",
        ],
        "aliases": ["houston", "nrg", "reliant"],
    },
    {
        "venue_id": "linc",
        "name": "Lincoln Financial Field",
        "city": "Philadelphia", "country": "USA", "capacity": 69_796,
        "lat": 39.9008, "lon": -75.1675,
        "transit": [
            "🚇 SEPTA Broad Street Line to AT&T Station (5 min walk)",
            "🚌 SEPTA game-day buses from Center City",
        ],
        "crowd_surge_zones": ["Pattison Ave post-match", "I-95 southbound on-ramps", "Broad St subway platform"],
        "gates_open_hours_before": 2.0,
        "parking": "Lots B/C adjacent. Pre-book.",
        "fan_zone": "Penn's Landing / Old City District",
        "emergency": "911 (USA/PA)",
        "prohibited": ["Bags > 14×14×6 in"],
        "accessibility": "Broad Street Line accessible. ADA section in lower level.",
        "local_tips": [
            "Philly cheesesteak is mandatory — Pat's King of Steaks or Geno's near the stadium.",
            "South Philly neighborhood is passionate about sport — great atmosphere.",
        ],
        "aliases": ["philadelphia", "philly", "lincoln financial", "the linc"],
    },
    {
        "venue_id": "bcplace",
        "name": "BC Place",
        "city": "Vancouver", "country": "Canada", "capacity": 54_500,
        "lat": 49.2827, "lon": -123.1207,
        "transit": [
            "🚇 SkyTrain Canada/Expo Line to Stadium-Chinatown Station (adjacent)",
            "🚌 Multiple TransLink routes on Beatty St",
        ],
        "crowd_surge_zones": ["Beatty St / Robson St post-match", "SkyTrain platform surge at Stadium station"],
        "gates_open_hours_before": 2.0,
        "parking": "Very limited. Use SkyTrain — the station is right at the stadium.",
        "fan_zone": "Granville Island / Canada Place waterfront",
        "emergency": "911 (Canada/BC)",
        "prohibited": ["Bags > 30×30×15 cm", "Glass containers"],
        "accessibility": "SkyTrain fully accessible. ADA section at east end.",
        "local_tips": [
            "SkyTrain is the only sensible option — driving in downtown Vancouver is painful.",
            "Gastown neighbourhood is great for a pre-match pint.",
            "Vancouver is stunning — arrive a day early and do the Seawall walk.",
        ],
        "aliases": ["vancouver", "bc place", "bc"],
    },
    {
        "venue_id": "azteca",
        "name": "Estadio Azteca",
        "city": "Mexico City", "country": "Mexico", "capacity": 87_523,
        "lat": 19.4326, "lon": -99.1332,
        "transit": [
            "🚇 Metro Line 2 to Tasqueña, then tram (Tren Ligero) to Estadio Azteca station",
            "🚌 Game-day shuttle buses from Insurgentes Sur corridor",
            "🚕 Uber is available but expect heavy traffic on Calzada de Tlalpan",
        ],
        "crowd_surge_zones": ["Calzada de Tlalpan post-match", "Insurgentes Sur / Periférico junction", "Tren Ligero platform surge"],
        "gates_open_hours_before": 2.5,
        "parking": "Stadium parking available but very limited. Arrive 3+ hrs early.",
        "fan_zone": "Zócalo (historic centre) fan festival area",
        "emergency": "911 (Mexico)",
        "prohibited": ["Bags > 35×35×15 cm", "Glass containers", "Outside alcohol"],
        "accessibility": "Metro and Tren Ligero have accessible cars. ADA section at north end.",
        "local_tips": [
            "Altitude warning: Mexico City sits at 2,240m. Acclimatise for 24–48 hrs before the match.",
            "Eat at Mercado de Medellín or try tacos at El Califa pre-match.",
            "Pick-pocket awareness in crowded transit — keep valuables secure.",
            "Spanish phrases: 'Dónde está la salida?' (Where is the exit?), '¡Ayuda!' (Help!)",
        ],
        "aliases": ["mexico city", "azteca", "cdmx"],
    },
    {
        "venue_id": "akron",
        "name": "Estadio Akron",
        "city": "Guadalajara", "country": "Mexico", "capacity": 49_850,
        "lat": 20.6597, "lon": -103.3496,
        "transit": [
            "🚇 Guadalajara Metro Line 1 to Zapopan, then shuttle",
            "🚕 Uber from central Guadalajara (~20 min)",
        ],
        "crowd_surge_zones": ["Avenida Paseo Acueducto post-match", "Blvd Puerta de Hierro exits"],
        "gates_open_hours_before": 2.0,
        "parking": "On-site parking available. Pre-purchase recommended.",
        "fan_zone": "Centro Histórico de Guadalajara / Tlaquepaque artisan district",
        "emergency": "911 (Mexico)",
        "prohibited": ["Glass containers", "Outside alcohol", "Bags > 35×35×15 cm"],
        "accessibility": "Metro accessible. ADA section at south end.",
        "local_tips": [
            "Birria tacos in Guadalajara are world-class — try Birriería Las 9 Esquinas.",
            "Tequila is from this region — visit Cantina La Fuente for authentic mezcal.",
        ],
        "aliases": ["guadalajara", "akron", "chivas stadium"],
    },
    {
        "venue_id": "bbva",
        "name": "Estadio BBVA",
        "city": "Monterrey", "country": "Mexico", "capacity": 53_500,
        "lat": 25.6866, "lon": -100.3161,
        "transit": [
            "🚇 Monterrey Metro Line 1 to Estadio BBVA station (directly adjacent)",
            "🚕 Uber from Centro / Barrio Antiguo (~15 min)",
        ],
        "crowd_surge_zones": ["Av. Constitución post-match", "Metro platform at Estadio station", "Av. Pablo Livas exits"],
        "gates_open_hours_before": 2.0,
        "parking": "Adjacent lots. Pre-book.",
        "fan_zone": "Barrio Antiguo / Macroplaza city centre",
        "emergency": "911 (Mexico)",
        "prohibited": ["Glass containers", "Outside alcohol", "Bags > 35×35×15 cm"],
        "accessibility": "Metro fully accessible. Stadium has ADA section.",
        "local_tips": [
            "Cabrito (roast kid goat) is the local speciality — try El Rey del Cabrito.",
            "Cerro de la Silla mountain backdrop makes for incredible match atmosphere.",
        ],
        "aliases": ["monterrey", "bbva", "rayados stadium"],
    },
]


def seed():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI not set in .env")

    client = MongoClient(uri, serverSelectionTimeoutMS=10_000)
    db = client["worldcup2026"]
    col = db["venues"]

    # Upsert each venue by venue_id
    ops = [
        UpdateOne({"venue_id": v["venue_id"]}, {"$set": v}, upsert=True)
        for v in VENUES
    ]
    result = col.bulk_write(ops)
    print(f"✅ Seeded {len(VENUES)} venues — "
          f"upserted: {result.upserted_count}, modified: {result.modified_count}")

    # Create a text index for fuzzy search
    try:
        col.create_index([("name", "text"), ("city", "text"), ("aliases", "text")])
        print("✅ Text index created on venues collection")
    except Exception as e:
        print(f"⚠️  Text index skipped (already exists): {e}")

    # Seed global config: safety tips queried live by matchday_tool.py
    db["config"].update_one(
        {"key": "safety_tips"},
        {"$set": {
            "key": "safety_tips",
            "tips": [
                "📋 Keep your FIFA Fan ID and match ticket accessible — digital + printed backup.",
                "🔋 Charge your phone fully. Save emergency contacts offline.",
                "💧 Stay hydrated, especially at outdoor or warm-weather venues.",
                "👥 Agree on a meeting point with your group before entering.",
                "💵 Carry some local cash for street food and small vendors.",
                "📱 Follow @FIFAWorldCup and local police on social media for real-time updates.",
                "🚨 If separated or in an emergency, move to the nearest steward or police officer.",
                "🎒 Use a small bag that fits in the palm of your hand to avoid security delays.",
            ],
        }},
        upsert=True,
    )
    print("✅ Global config (safety_tips) upserted")
    client.close()


if __name__ == "__main__":
    seed()
