"""Google Maps Geocoding & Places (New) API tools for Smart Travel Concierge agent."""

import json
import os
import urllib.parse
import urllib.request
from dotenv import load_dotenv

load_dotenv()


def geocode_address(address: str) -> str:
    """Converts a street address or location name into geographic coordinates (latitude and longitude).

    Args:
        address: The address or location name to geocode (e.g. 'Kyoto Station', 'Eiffel Tower, Paris').

    Returns:
        JSON string containing formatted address, latitude, longitude, and place_id.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

    try:
        encoded_addr = urllib.parse.quote(address.strip())
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_addr}&key={api_key}"

        req = urllib.request.Request(
            url, headers={"User-Agent": "SmartTravelAgent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}'. Status: {data.get('status')}."

        result = data["results"][0]
        location = result.get("geometry", {}).get("location", {})

        output = {
            "query": address,
            "formatted_address": result.get("formatted_address"),
            "latitude": location.get("lat"),
            "longitude": location.get("lng"),
            "place_id": result.get("place_id"),
        }
        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error geocoding address '{address}': {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "tourist_attraction",
    radius_meters: int = 2000,
) -> str:
    """Finds nearby places of a given type around coordinates using the Google Places API (New).

    Args:
        latitude: Latitude coordinate of the central search location.
        longitude: Longitude coordinate of the central search location.
        place_type: Type of place to search for (e.g. 'tourist_attraction', 'restaurant', 'museum', 'lodging', 'park').
        radius_meters: Search radius in meters (default 2000m / 2km).

    Returns:
        JSON string list of nearby places with name, formatted address, location coordinates, and rating.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

    try:
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.primaryType",
        }

        body = {
            "includedTypes": [place_type],
            "maxResultCount": 5,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                    },
                    "radius": float(radius_meters),
                }
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m of ({latitude}, {longitude})."

        results = []
        for p in places:
            display_name = p.get("displayName", {}).get("text", "Unknown")
            address = p.get("formattedAddress", "N/A")
            loc = p.get("location", {})
            rating = p.get("rating", "N/A")

            results.append({
                "name": display_name,
                "address": address,
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                },
                "rating": rating,
            })

        return json.dumps(results, indent=2)

    except Exception as e:
        return f"Error searching nearby places: {str(e)}"
