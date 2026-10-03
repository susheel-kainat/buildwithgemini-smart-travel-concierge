# Smart Travel Concierge ✈️🌴

A personal AI travel & itinerary concierge built with Google's **Agent Development Kit (ADK)** and deployed on **Vertex AI Agent Engine (Agent Runtime)**. Smart Travel Concierge helps travelers discover destinations, search curated stay options, check real-time weather, convert currencies, find nearby places via Google Maps, generate visual travel postcards and short destination teaser videos, and build personalized trip itineraries.

![Smart Travel Concierge Demo](smart_travel_demo.gif)

---

## 🌟 Features & Wired Google Cloud Services

### 🧠 Agent Architecture & Memory
- **Vertex AI Agent Engine (Agent Runtime)**: Powered by `gemini-2.5-flash` orchestrated via ADK.
- **Vertex AI Memory Bank**: Cross-session long-term memory via `PreloadMemoryTool` and post-turn callbacks to store and recall user travel preferences (favorite destinations, stay styles, budget ranges).
- **A2UI (Agent-to-User Interface v0.8)**: Generates structured, responsive visual UI cards (destinations, weather, postcards, and video players) rendered in real time.

### 🗄️ Database & Storage
- **Google Cloud Firestore**: Persists travel destination packages and user-saved trip itinerary items (`search_destinations`, `get_destination_details`, `add_destination`, `save_itinerary_item`).
- **Google Cloud Storage (GCS)**: Public media bucket hosting generated travel postcards and video teasers.

### 🎨 Visual & Media Generation Tools
- **Image Generation**: Generates custom travel postcards using Imagen (`gemini-3.1-flash-lite-image`) via Vertex AI, saved as Playground artifacts and published to GCS.
- **Video Generation**: Generates destination video teasers using Google's Omni model (`gemini-omni-flash-preview`) in the `global` region, saved as artifacts and published to GCS.

### 🗺️ Location & Utility Tools
- **Google Maps & Places API**: Geocodes addresses (`geocode_address`) and finds nearby attractions and hotels (`find_nearby_places`).
- **Python Sandbox Code Execution**: Secure `AgentEngineSandboxCodeExecutor` for complex budget math and itinerary data calculations.
- **External Weather & Currency APIs**: Real-time forecast lookups (`get_live_weather`) and FX currency conversions (`convert_currency`).

---

## 🛠️ Project Structure

```
smart-travel-concierge/
├── app/                        # ADK Agent package
│   ├── agent.py                # Agent definition, system prompt, callbacks & tools array
│   ├── firestore_tools.py      # Firestore database integration tools
│   ├── maps_tools.py           # Google Maps & Places API tools
│   ├── media_tools.py          # Imagen image & Omni video generation tools
│   ├── tools.py                # Weather, currency, and time utility tools
│   └── a2ui_utils.py           # A2UI callback parser and schema manager
├── frontend/                   # FastAPI Web Application & Chat UI
│   ├── main.py                 # Proxy server communicating with Agent Runtime (A2A)
│   └── static/index.html       # Web UI with dialogue cards & prompt chips
├── smart_travel_demo.gif       # Demo screen recording
├── agents-cli-manifest.yaml    # Deployment manifest
└── pyproject.toml              # Dependencies & project config
```

---

## 🚀 Setup & Local Execution

### 1. Prerequisites
- Python 3.11+ and `uv` package manager
- Google Cloud SDK (`gcloud`) with active authentication

### 2. Environment Setup
Create a `.env` file in the project root:

```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### 3. Install Dependencies
```bash
uv sync
```

### 4. Run the Agent Playground (CLI)
```bash
agents-cli playground
```

### 5. Run the Web Frontend Locally
Navigate to the `frontend/` directory and run:

```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT_ID/locations/us-central1/reasoningEngines/YOUR_AGENT_ENGINE_ID"
export AGENT_DIRECTORY="app"
python main.py
```
Open a browser to port `8080` to access the live chat interface.
