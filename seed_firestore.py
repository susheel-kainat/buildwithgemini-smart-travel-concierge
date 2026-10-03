"""Seed script for Smart Travel & Itinerary Concierge Firestore database."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-14f2a818ecc2"

SEED_DESTINATIONS = [
    {
        "id": "dest-kyoto",
        "name": "Kyoto Historic Temples & Gardens",
        "location": "Kyoto, Japan",
        "category": "Culture & Heritage",
        "budget_tier": "mid-range",
        "avg_daily_cost_usd": 180,
        "highlights": [
            "Fushimi Inari Shrine",
            "Arashiyama Bamboo Grove",
            "Gion Geisha District",
            "Kinkaku-ji Golden Pavilion",
        ],
        "best_season": "Spring & Autumn",
        "description": "Ancient capital of Japan famed for classical Buddhist temples, serene zen gardens, traditional wooden tea houses, and cherry blossoms.",
    },
    {
        "id": "dest-paris",
        "name": "Paris Art & Culinary Discovery",
        "location": "Paris, France",
        "category": "Culture & Heritage",
        "budget_tier": "luxury",
        "avg_daily_cost_usd": 320,
        "highlights": [
            "Louvre Museum",
            "Eiffel Tower Sunset",
            "Le Marais Pastry Tour",
            "Montmartre Art Walk",
        ],
        "best_season": "Spring & Early Fall",
        "description": "The City of Light offers world-class art collections, Michelin-starred gastronomy, historic architecture, and romantic Seine river cruises.",
    },
    {
        "id": "dest-maui",
        "name": "Maui Tropical Coastal Escape",
        "location": "Hawaii, USA",
        "category": "Beach & Relaxation",
        "budget_tier": "luxury",
        "avg_daily_cost_usd": 350,
        "highlights": [
            "Road to Hana",
            "Haleakala Sunrise Park",
            "Molokini Crater Snorkeling",
            "Ka'anapali Beach",
        ],
        "best_season": "Year-round",
        "description": "Tropical Hawaiian island featuring dramatic volcanic landscapes, crystal-clear snorkeling bays, luxury beach resorts, and scenic coastal drives.",
    },
    {
        "id": "dest-rome",
        "name": "Rome Imperial Heritage & Food Tour",
        "location": "Rome, Italy",
        "category": "Culture & Heritage",
        "budget_tier": "mid-range",
        "avg_daily_cost_usd": 200,
        "highlights": [
            "Colosseum & Forum",
            "Vatican Museums & Sistine Chapel",
            "Trastevere Food Walk",
            "Trevi Fountain",
        ],
        "best_season": "Spring & Autumn",
        "description": "The Eternal City boasts nearly 3,000 years of globally influential art, architecture, ancient ruins, and irresistible authentic Italian trattorias.",
    },
    {
        "id": "dest-banff",
        "name": "Banff Alpine Wilderness & Lakes",
        "location": "Alberta, Canada",
        "category": "Adventure & Nature",
        "budget_tier": "mid-range",
        "avg_daily_cost_usd": 220,
        "highlights": [
            "Lake Louise Kayaking",
            "Moraine Lake Sunrise",
            "Icefields Parkway Scenic Drive",
            "Banff Upper Hot Springs",
        ],
        "best_season": "Summer (Hiking) & Winter (Skiing)",
        "description": "Breathtaking national park in the Canadian Rockies known for turquoise glacier-fed lakes, towering peaks, alpine wildlife, and mountain adventures.",
    },
]


def seed_database():
    print(f"Connecting to Firestore for project: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")

    for dest in SEED_DESTINATIONS:
        doc_id = dest["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(dest)
        print(f"  - Seeded destination: {dest['name']} ({doc_id})")

    print(
        f"Successfully seeded {len(SEED_DESTINATIONS)} destinations into Firestore 'destinations' collection!"
    )


if __name__ == "__main__":
    seed_database()
