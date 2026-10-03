# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.firestore_tools import (
    add_destination,
    get_destination_details,
    save_itinerary_item,
    search_destinations,
)
from app.maps_tools import find_nearby_places, geocode_address
from app.media_tools import (
    generate_destination_postcard,
    generate_destination_video,
)

load_dotenv()

PROJECT_ID = "qwiklabs-gcp-01-14f2a818ecc2"
AGENT_ENGINE_ID = "3536785309171712000"

WEATHER_CODES = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤️",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Foggy 🌫️",
    48: "Depositing rime fog 🌫️",
    51: "Light drizzle 🌧️",
    53: "Moderate drizzle 🌧️",
    55: "Dense drizzle 🌧️",
    61: "Slight rain 🌧️",
    63: "Moderate rain 🌧️",
    65: "Heavy rain 🌧️",
    71: "Slight snow ❄️",
    73: "Moderate snow ❄️",
    75: "Heavy snow ❄️",
    80: "Slight rain showers 🌦️",
    81: "Moderate rain showers 🌦️",
    82: "Violent rain showers ⛈️",
    95: "Thunderstorm 🌩️",
}


def get_live_weather(city: str) -> str:
    """Fetches real-time current weather conditions and temperature for any destination city worldwide.

    Args:
        city: Name of the destination city or location (e.g. 'Kyoto', 'Paris', 'Maui', 'Rome', 'Banff', 'San Francisco').

    Returns:
        Formatted string containing current temperature in Celsius and Fahrenheit, wind speed, and weather conditions.
    """
    try:
        encoded_city = urllib.parse.quote(city.strip())
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=en&format=json"

        req = urllib.request.Request(
            geo_url, headers={"User-Agent": "SmartTravelAgent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))

        if not geo_data.get("results"):
            return f"Could not find geographic coordinates for city '{city}'."

        loc = geo_data["results"][0]
        lat = loc["latitude"]
        lon = loc["longitude"]
        city_name = loc.get("name", city)
        country = loc.get("country", "")

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req_w = urllib.request.Request(
            weather_url, headers={"User-Agent": "SmartTravelAgent/1.0"}
        )
        with urllib.request.urlopen(req_w, timeout=5) as resp_w:
            w_data = json.loads(resp_w.read().decode("utf-8"))

        curr = w_data.get("current_weather", {})
        temp_c = curr.get("temperature", "N/A")
        temp_f = (
            round((temp_c * 9 / 5) + 32, 1)
            if isinstance(temp_c, (int, float))
            else "N/A"
        )
        wind_kmh = curr.get("windspeed", "N/A")
        w_code = curr.get("weathercode", -1)
        condition = WEATHER_CODES.get(w_code, "Fair weather")

        location_str = f"{city_name}, {country}" if country else city_name
        return (
            f"Current weather in {location_str}: {temp_c}°C ({temp_f}°F), "
            f"condition: {condition}, wind speed: {wind_kmh} km/h."
        )

    except Exception as e:
        return f"Error fetching live weather for '{city}': {str(e)}"


def convert_currency(
    amount: float, from_currency: str = "USD", to_currency: str = "JPY"
) -> str:
    """Converts a travel monetary amount between world currencies using live real-time exchange rates.

    Args:
        amount: The monetary amount to convert (e.g. 250.0).
        from_currency: 3-letter currency code converting from (e.g. 'USD', 'EUR', 'GBP', 'CAD').
        to_currency: 3-letter currency code converting to (e.g. 'JPY', 'EUR', 'CAD', 'USD', 'GBP').

    Returns:
        Formatted conversion string with live rate and calculated converted amount.
    """
    try:
        base = from_currency.upper().strip()
        target = to_currency.upper().strip()

        api_key = os.environ.get("EXCHANGE_RATE_API_KEY", "")
        if api_key:
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{base}/{target}/{amount}"
        else:
            url = f"https://open.er-api.com/v6/latest/{base}"

        req = urllib.request.Request(
            url, headers={"User-Agent": "SmartTravelAgent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if api_key and "conversion_result" in data:
            converted = data["conversion_result"]
            rate = data.get("conversion_rate", converted / amount if amount else 0)
            return (
                f"{amount:.2f} {base} = {converted:,.2f} {target} "
                f"(Live exchange rate: 1 {base} = {rate} {target})"
            )

        rates = data.get("rates", {})
        if target not in rates:
            return f"Currency code '{target}' not found in live exchange rates."

        rate = rates[target]
        converted = round(amount * rate, 2)
        return (
            f"{amount:.2f} {base} = {converted:,.2f} {target} "
            f"(Live exchange rate: 1 {base} = {rate} {target})"
        )

    except Exception as e:
        return f"Error converting {amount} {from_currency} to {to_currency}: {str(e)}"


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: City name to get current time for.

    Returns:
        Formatted time string.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        tz_identifier = "UTC"

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each agent turn to send session events to Vertex AI Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        print(f"Memory extraction error: {e}")
    return None


# Initialize AgentEngineSandboxCodeExecutor using deployment_metadata.json if available
agent_engine_resource_name = f"projects/{PROJECT_ID}/locations/us-central1/reasoningEngines/{AGENT_ENGINE_ID}"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)

# Build A2UI System Instruction (version 0.8) with Basic Catalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are the Smart Travel & Itinerary Concierge. "
        "You help travelers search destinations, explore travel packages, get real-time weather forecasts, "
        "convert travel budgets between currencies, geocode addresses into GPS coordinates, "
        "find nearby tourist attractions using Google Maps & Places API (New), "
        "generate visual travel postcards using gemini-3.1-flash-lite-image, "
        "safely execute Python code in a secure Agent Engine sandbox for math or data calculations, "
        "add new destinations to the database, and save customized trip itineraries.\n\n"
        "MEMORY & PREFERENCES MANAGEMENT:\n"
        "- You have cross-session long-term memory via PreloadMemoryTool and Memory Bank.\n"
        "- Actively recall user preferred travel locations (e.g. Kyoto, Paris, Maui, Rome, Banff) "
        "and preferred types of stays (e.g. luxury resorts, boutique hotels, eco-lodges, ryokans, beach villas, cozy chalets).\n"
        "- Whenever the user mentions a favorite destination, preferred location, accommodation type, or stay preference, "
        "acknowledge and incorporate these preferences into your responses.\n"
        "- Personalize all itinerary recommendations, destination searches, and travel packages around the user's remembered preferences."
    ),
    workflow_description="Analyze the user request, call necessary tools, and return structured A2UI cards when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property (\'h1\', \'h2\', \'body\') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or \'kind\'/\'data\'/\'metadata\' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
    tools=[
        PreloadMemoryTool(),
        search_destinations,
        get_destination_details,
        add_destination,
        save_itinerary_item,
        geocode_address,
        find_nearby_places,
        generate_destination_postcard,
        generate_destination_video,
        get_live_weather,
        convert_currency,
        get_current_time,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
