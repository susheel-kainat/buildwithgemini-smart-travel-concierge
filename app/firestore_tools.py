"""Firestore tools for Smart Travel & Itinerary Concierge agent."""

import json
from google.cloud import firestore

# IMPORTANT: Hardcode GCP Project ID as string to prevent deployment issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-01-14f2a818ecc2"

db = firestore.Client(project=PROJECT_ID)


def search_destinations(category: str = "", max_budget: int = 0) -> str:
    """Search for travel destinations in Firestore database.

    Args:
        category: Optional category filter (e.g. 'Culture & Heritage', 'Beach & Relaxation', 'Adventure & Nature').
        max_budget: Optional maximum average daily cost in USD (e.g. 250).

    Returns:
        JSON string list of matching destinations.
    """
    collection_ref = db.collection("destinations")
    docs = collection_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # Apply category filter
        if category and category.lower() not in data.get("category", "").lower():
            continue

        # Apply budget filter
        if max_budget > 0 and data.get("avg_daily_cost_usd", 0) > max_budget:
            continue

        results.append(data)

    if not results:
        return f"No destinations found matching category='{category}' and max_budget=${max_budget}."

    return json.dumps(results, indent=2)


def get_destination_details(destination_id: str) -> str:
    """Retrieve complete details for a specific destination by ID.

    Args:
        destination_id: The unique destination ID (e.g. 'dest-kyoto', 'dest-paris').

    Returns:
        JSON string with complete destination details or an error message if not found.
    """
    doc_ref = db.collection("destinations").document(destination_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Destination '{destination_id}' not found in database."

    data = doc.to_dict()
    data["id"] = doc.id
    return json.dumps(data, indent=2)


def add_destination(
    name: str,
    location: str,
    category: str,
    budget_tier: str,
    avg_daily_cost_usd: int,
    description: str,
    highlights: list[str],
    best_season: str = "Year-round",
) -> str:
    """Add a new travel destination to the Firestore database.

    Args:
        name: Name of destination or tour (e.g. 'Tokyo Tech & Pop Culture').
        location: City and country (e.g. 'Tokyo, Japan').
        category: Category (e.g. 'Culture & Heritage', 'Beach & Relaxation', 'Adventure & Nature').
        budget_tier: Budget classification ('budget', 'mid-range', 'luxury').
        avg_daily_cost_usd: Estimated average daily cost in USD.
        description: Informative overview of the destination.
        highlights: Key attractions or activities list.
        best_season: Ideal season to visit (e.g. 'Spring & Autumn').

    Returns:
        Confirmation message with the created document ID.
    """
    slug = name.lower().replace(" ", "-")
    doc_id = f"dest-{slug[:20]}"

    dest_data = {
        "id": doc_id,
        "name": name,
        "location": location,
        "category": category,
        "budget_tier": budget_tier,
        "avg_daily_cost_usd": avg_daily_cost_usd,
        "description": description,
        "highlights": highlights,
        "best_season": best_season,
    }

    db.collection("destinations").document(doc_id).set(dest_data)
    return f"Successfully added destination '{name}' with ID '{doc_id}' to Firestore!"


def save_itinerary_item(
    user_id: str, destination_name: str, notes: str = ""
) -> str:
    """Save an itinerary item or destination to a user's travel itinerary in Firestore.

    Args:
        user_id: User or session ID saving the item.
        destination_name: Name of the destination to save.
        notes: Personal notes or planned activities for this trip item.

    Returns:
        Confirmation string indicating saved itinerary item.
    """
    item_id = f"trip-{destination_name.lower().replace(' ', '-')[:15]}"
    item_data = {
        "id": item_id,
        "user_id": user_id,
        "destination_name": destination_name,
        "notes": notes,
        "created_at": firestore.SERVER_TIMESTAMP,
    }

    db.collection("user_itineraries").document(item_id).set(item_data)
    return f"Successfully saved '{destination_name}' to user '{user_id}' itinerary in Firestore!"
