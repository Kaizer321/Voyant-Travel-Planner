# Voyant - AI Travel Planning Assistant

## 🎯 Project Overview

**Voyant** (Voyage + Savant) is an intelligent travel planning assistant powered by a multi-agent architecture. The system implements the research paper:

> **"Orchestrating Intelligence: A CrewAI-Based Architecture for Seamless End-to-End Travel Planning"**  
> by Muhammad Umar, Abdullah Naeem, and Ammar Ahmed (FAST NUCES Islamabad)

Voyant orchestrates specialized AI agents to create comprehensive travel itineraries with intelligent failure recovery mechanisms, all through a beautiful ChatGPT-style minimal interface.

## 🎥 Demo Video

<video src="attached_assets/demo.mp4" controls="controls" style="max-width: 100%;">
  Your browser does not support the video tag.
</video>

> *Watch Voyant in action: Planning a complete trip to Paris with real-time agent coordination.*
>
> *(Note: Place your video file named `demo.mp4` in the `attached_assets` folder)*

## ✨ Key Features

### 🤖 Multi-Agent Architecture
- **Meta-Agent**: Central coordinator managing the entire planning workflow
- **Flight Agent**: Searches flights using Amadeus API with real-time pricing
- **Hotel Agent**: Finds accommodations matching preferences and budgets
- **Weather Agent**: Provides forecasts using OpenWeatherMap API
- **Activity Agent**: Recommends experiences based on location and weather
- **Verification Agent**: Validates itineraries for consistency and budget compliance
- **Re-planning Engine**: Handles failures with multi-level recovery

### 💬 Voyant Chat Interface
- **ChatGPT-style minimal design** - Clean, professional, and focused
- **Real-time WebSocket communication** - Instant responses
- **Markdown formatting** - Beautiful, organized travel itineraries
- **Left-right chat layout** - User messages on right, assistant on left
- **Planning animation** - Visual feedback during trip planning
- **No initial message** - Starts clean with message count at 0

### 🔄 Communication Protocols

#### A2A Protocol (Agent-to-Agent)
- Standardized peer-to-peer communication framework
- Message passing between Meta-Agent and specialized agents
- Message history tracking for audit and debugging
- Implementation: `src/protocols/a2a_protocol.py`

#### Model Context Protocol (MCP)
- Shared contextual state management across all agents
- Dependency tracking between contexts
- Version control for context updates
- Conflict detection mechanism
- Implementation: `src/protocols/mcp_context.py`

### 🛡️ Multi-Level Recovery Strategy
- **Level 1 - Local Recovery**: Individual agents retry failed operations
- **Level 2 - Cross-Domain Recovery**: Meta-Agent coordinates changes across domains
- **Level 3 - Global Re-planning**: Complete itinerary reconstruction

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Meta-Agent                          │
│            (Hierarchical Task Decomposition)            │
└───────────────┬────────────────────────────────────────┘
                │
        ┌───────┴───────┐
        │  A2A Protocol │ (Message Passing)
        └───────┬───────┘
                │
    ┌───────────┴────────────┐
    │   MCP Context Store    │ (Shared State)
    └────────────────────────┘
                │
    ┌───────────┼────────────┬────────────┬──────────────┐
    │           │            │            │              │
┌───▼────┐  ┌───▼────┐  ┌───▼────┐  ┌───▼────┐   ┌─────▼─────┐
│ Flight │  │ Hotel  │  │Weather │  │Activity│   │Verification│
│ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │   │   Agent    │
└────────┘  └────────┘  └────────┘  └────────┘   └───────────┘
    │           │            │            │              │
    └───────────┴────────────┴────────────┴──────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Re-planning Engine │
                    │  (Failure Recovery)│
                    └────────────────────┘
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- API Keys (add to `.env` file):
  - `AMADEUS_API_KEY` and `AMADEUS_API_SECRET`
  - `OPENWEATHERMAP_API_KEY`
  - `GEMINI_API_KEY`

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd OrchestratingIntelligence
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file with your API keys:
```env
AMADEUS_API_KEY=your_amadeus_key
AMADEUS_API_SECRET=your_amadeus_secret
OPENWEATHERMAP_API_KEY=your_openweather_key
GEMINI_API_KEY=your_gemini_key
```

### Running the Application

1. **Start the backend server**
```bash
python -m src.api.main
```
Backend runs on `http://localhost:5000`

2. **Start the frontend server** (in a new terminal)
```bash
python -m http.server 8000 --directory frontend
```
Frontend runs on `http://localhost:8000`

3. **Access Voyant**
Open your browser to `http://localhost:8000` and start planning your trip!

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service health check |
| `/plan-trip` | POST | Create travel itinerary |
| `/itinerary/{request_id}` | GET | Retrieve specific itinerary |
| `/itineraries` | GET | List all itineraries |
| `/simulate-failure` | POST | Test failure recovery |
| `/system/health` | GET | System health monitoring |
| `/system/a2a-messages` | GET | View A2A message history |
| `/system/mcp-context` | GET | Inspect MCP context state |
| `/ws` | WS | Real-time WebSocket updates |

## � How to Use Voyant

1. **Open the chat interface** at `http://localhost:8000`
2. **Start chatting** - Voyant will ask for your travel details:
   - Origin city
   - Destination
   - Travel dates
   - Number of travelers
   - Budget
3. **Watch the magic** - See the planning animation as agents work
4. **Get your itinerary** - Beautifully formatted with:
   - Flight options with prices
   - Hotel recommendations
   - Weather forecast
   - Activity suggestions
   - Total cost breakdown

## 📁 Project Structure

```
.
├── src/
│   ├── agents/              # All agent implementations
│   │   ├── meta_agent.py
│   │   ├── flight_agent.py
│   │   ├── hotel_agent.py
│   │   ├── weather_agent.py
│   │   ├── activity_agent.py
│   │   ├── verification_agent.py
│   │   └── replanning_engine.py
│   ├── protocols/           # Communication protocols
│   │   ├── a2a_protocol.py
│   │   └── mcp_context.py
│   ├── models/              # Data models and schemas
│   │   └── schemas.py
│   ├── apis/                # Real API clients
│   │   └── amadeus_client.py
│   ├── mock_apis/           # Mock external APIs
│   │   ├── flight_api.py
│   │   ├── hotel_api.py
│   │   ├── weather_api.py
│   │   └── activity_api.py
│   └── api/                 # FastAPI application
│       └── main.py
├── frontend/
│   └── index.html           # Voyant chat interface
├── attached_assets/
│   └── research_paper.pdf   # Original research paper
├── .env                     # Environment variables (create this)
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```

## 🛠️ Technology Stack

### Backend
- **CrewAI 1.3.0** - Multi-agent orchestration
- **FastAPI 0.121.0** - Modern async web framework
- **Pydantic 2.x** - Data validation
- **Google Gemini** - LLM for conversational AI
- **Amadeus API** - Real flight and hotel data
- **OpenWeatherMap API** - Weather forecasts
- **WebSockets** - Real-time communication

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling (minimal, professional design)
- **JavaScript** - Interactivity
- **Marked.js** - Markdown parsing
- **WebSocket API** - Real-time updates

## 🔬 Research Implementation

This project implements key concepts from the research paper:

1. ✅ **Hierarchical Task Decomposition** - Meta-Agent breaks down complex planning
2. ✅ **A2A Protocol** - Standardized agent communication
3. ✅ **MCP Integration** - Shared context management
4. ✅ **Multi-Level Recovery** - 3-tier failure handling
5. ✅ **Verification Loop** - Continuous validation
6. ✅ **Dynamic Re-planning** - Adaptive recovery

## 📈 Key Metrics (from Paper)

- **Failure Recovery Rate**: 87.3% (vs 58.9% baseline)
- **Planning Success Rate**: 94.7% (vs 81.4% baseline)

## � Design Philosophy

Voyant's interface follows these principles:
- **Minimal** - No clutter, just conversation
- **Professional** - Clean color palette (teal/green #10a37f)
- **Familiar** - ChatGPT-style layout users know
- **Responsive** - Works on desktop and mobile
- **Accessible** - Clear typography and contrast

## 🧪 Testing

Test the API integration:
```bash
python test_real_apis.py
```

This tests:
- Amadeus flight search
- Amadeus hotel search
- Amadeus activity search
- OpenWeatherMap forecasts

## 🚧 Future Enhancements

1. **User Authentication** - Save trip history
2. **Booking Integration** - Direct flight/hotel booking
3. **Multi-language Support** - International travelers
4. **Mobile App** - Native iOS/Android apps
5. **Advanced Filters** - More search criteria
6. **Social Sharing** - Share itineraries with friends

## 📝 License

Research implementation based on the paper by Umar et al., FAST NUCES Islamabad.

## 👥 Authors

- **Research Paper**: Muhammad Umar, Abdullah Naeem, Ammar Ahmed (FAST NUCES)
- **Implementation**: Enhanced with Voyant chat interface

---

**Status**: ✅ Production Ready | 🚀 Backend: Port 5000 | 🎨 Frontend: Port 8000

**Experience Voyant** - Your intelligent travel companion! 🧭✈️
