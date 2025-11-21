from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional
import uuid
from datetime import datetime
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
import os

"""Load environment first to configure CrewAI before agent imports"""
_here = Path(__file__).resolve()
# Inner .env must take precedence
load_dotenv(_here.parents[2] / ".env", override=True)  # inner: OrchestratingIntelligence/.env
# Outer .env must not override inner values
load_dotenv(_here.parents[3] / ".env", override=False)  # outer/root: project/.env

# Ensure CrewAI uses Google Gemini and does not require OpenAI
os.environ.setdefault("CREWAI_LLM_PROVIDER", "google")
# Prevent CrewAI from crashing when probing OpenAI provider
os.environ.setdefault("OPENAI_API_KEY", "dummy")

from src.models.schemas import TravelRequest, TravelItinerary, PlanningStatus
from src.protocols.a2a_protocol import A2AProtocol
from src.protocols.mcp_context import MCPContext
from src.agents.meta_agent import MetaAgent
from src.agents.verification_agent import VerificationAgent
from src.agents.replanning_engine import ReplanningEngine

app = FastAPI(
    title="CrewAI Travel Planner",
    description="Multi-agent travel planning microservice with A2A protocol and MCP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

a2a_protocol = A2AProtocol()
mcp_context = MCPContext()

meta_agent = MetaAgent(a2a_protocol, mcp_context, failure_rate=0.0)
verification_agent = VerificationAgent(mcp_context)
replanning_engine = ReplanningEngine(meta_agent, verification_agent, mcp_context)

itineraries_store: Dict[str, TravelItinerary] = {}
active_websockets: list = []

# Store conversation history per WebSocket connection
conversation_histories: Dict[int, list] = {}

_gemini_model = None

def _ensure_gemini_model():
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model
    try:
        import google.generativeai as genai
    except Exception:
        print("[Gemini] google-generativeai not installed")
        return None
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    raw_model = os.environ.get("CREWAI_DEFAULT_MODEL") or ""
    model_name = raw_model.strip()
    # Remove surrounding quotes if present (e.g., "gemini-pro" or 'gemini-pro')
    if (model_name.startswith('"') and model_name.endswith('"')) or (
        model_name.startswith("'") and model_name.endswith("'")
    ):
        model_name = model_name[1:-1].strip()
    # Accept values like 'models/gemini-2.0-flash-lite' from UI copy-paste
    if model_name.startswith("models/"):
        model_name = model_name.split("/", 1)[1]
    if not api_key:
        print("[Gemini] No API key found in environment (GEMINI_API_KEY/GOOGLE_API_KEY)")
        return None
    if not model_name:
        print("[Gemini] No model set in env (CREWAI_DEFAULT_MODEL)")
        return None
    print(f"[Gemini] Initializing model: {model_name}")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        _gemini_model = model
        return _gemini_model
    except Exception as e:
        print(f"[Gemini] Failed to initialize model '{model_name}': {e}")
        return None

async def generate_gemini_response(prompt: str, conversation_history: list = None) -> str:
    """Call Gemini synchronously via a thread; return the text or an error message."""
    model = _ensure_gemini_model()
    if model is None:
        return (
            "[system] Gemini not configured. Ensure google-generativeai is installed, "
            "GEMINI_API_KEY is set, and CREWAI_DEFAULT_MODEL is a valid model in .env."
        )
    import asyncio
    def _call():
        try:
            system_prompt = (
                "You are an expert travel consultant for the 'Orchestrating Intelligence' agency. "
                "Your goal is to help users plan their perfect trip. "
                "When a user expresses interest in traveling, do NOT immediately generate a full itinerary. "
                "Instead, guide the user by asking clarifying questions ONE BY ONE. "
                "Do NOT ask for multiple details in a single message. "
                "Prioritize gathering information in this order if missing: "
                "1. Origin (departure city) "
                "2. Destination "
                "3. Travel Dates "
                "4. Number of travelers "
                "5. Budget "
                "6. Interests/Preferences "
                "Only when you have ALL required information (origin, destination, dates, travelers, budget), "
                "inform the user that you will now search for options. "
                "Keep your responses concise, friendly, and professional."
            )
            
            # Build conversation context
            context_parts = [system_prompt]
            if conversation_history:
                for msg in conversation_history:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    context_parts.append(f"{role}: {msg['content']}")
            
            context_parts.append(f"User: {prompt}")
            full_prompt = "\n\n".join(context_parts)
            
            resp = model.generate_content(full_prompt)
            # Handle candidates structure
            if hasattr(resp, "text") and resp.text:
                return resp.text
            # Fallback to first candidate
            cands = getattr(resp, "candidates", None) or []
            if cands and getattr(cands[0], "content", None):
                parts = getattr(cands[0].content, "parts", []) or []
                texts = []
                for p in parts:
                    t = getattr(p, "text", None)
                    if t:
                        texts.append(t)
                return "\n".join(texts) if texts else "[system] No content from model."
            return "[system] Empty response from model."
        except Exception as e:
            return f"[system] Gemini error: {e}"
    return await asyncio.to_thread(_call)

async def extract_travel_info(conversation_history: list) -> Optional[Dict]:
    """Extract travel planning information from conversation history using Gemini."""
    model = _ensure_gemini_model()
    if not model:
        return None
    
    # Build conversation text
    conv_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    extraction_prompt = f"""Based on this conversation, extract travel planning information.
Return ONLY a JSON object with these fields (use null for missing values):
{{
  "origin": "departure city",
  "destination": "destination city",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "budget": number,
  "travelers": number,
  "ready_to_plan": true/false (true only if ALL required fields are provided)
}}

Conversation:
{conv_text}

JSON:"""
    
    try:
        resp = await asyncio.to_thread(lambda: model.generate_content(extraction_prompt))
        text = resp.text if hasattr(resp, "text") else ""
        # Extract JSON from response
        import json as json_lib
        import re
        json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if json_match:
            data = json_lib.loads(json_match.group())
            return data
    except Exception as e:
        print(f"Info extraction error: {e}")
    return None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "CrewAI Travel Planner",
        "status": "operational",
        "version": "1.0.0",
        "description": "Multi-agent travel planning with A2A protocol and MCP",
        "agents": {
            "meta_agent": "Central coordinator",
            "flight_agent": "Flight booking specialist",
            "hotel_agent": "Accommodation specialist",
            "weather_agent": "Weather forecasting",
            "activity_agent": "Activity curator",
            "verification_agent": "Itinerary verification",
            "replanning_engine": "Failure recovery",
        },
    }


@app.post("/plan-trip", response_model=TravelItinerary)
async def plan_trip(request: TravelRequest):
    """
    Create a comprehensive travel itinerary using multi-agent system
    """
    if not request.request_id:
        request.request_id = str(uuid.uuid4())

    try:
        itinerary = await meta_agent.process_travel_request(request)

        itinerary = await replanning_engine.adaptive_recovery(itinerary, request)

        itineraries_store[request.request_id] = itinerary

        await broadcast_update(
            {
                "type": "itinerary_update",
                "request_id": request.request_id,
                "status": itinerary.status.value,
                "total_cost": itinerary.total_cost,
            }
        )

        return itinerary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {str(e)}")


@app.get("/itinerary/{request_id}", response_model=TravelItinerary)
async def get_itinerary(request_id: str):
    """Retrieve a specific travel itinerary"""
    if request_id not in itineraries_store:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    return itineraries_store[request_id]


@app.get("/itineraries")
async def list_itineraries():
    """List all itineraries"""
    return {
        "count": len(itineraries_store),
        "itineraries": [
            {
                "request_id": itin.request_id,
                "status": itin.status.value,
                "total_cost": itin.total_cost,
                "created_at": itin.created_at.isoformat(),
            }
            for itin in itineraries_store.values()
        ],
    }


@app.post("/simulate-failure")
async def simulate_failure(
    request_id: str, failure_type: str, component: str
):
    """Simulate a failure and trigger re-planning"""
    if request_id not in itineraries_store:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    itinerary = itineraries_store[request_id]
    original_request = TravelRequest(
        request_id=request_id,
        origin=mcp_context.get_context("travel_request", "api")["origin"],
        destination=mcp_context.get_context("travel_request", "api")["destination"],
        start_date=mcp_context.get_context("travel_request", "api")["start_date"],
        end_date=mcp_context.get_context("travel_request", "api")["end_date"],
        budget=mcp_context.get_context("travel_request", "api")["budget"],
    )

    recovered_itinerary = await replanning_engine.handle_failure(
        failure_type, component, itinerary, original_request
    )

    itineraries_store[request_id] = recovered_itinerary

    return {
        "message": f"Simulated {failure_type} failure for {component}",
        "recovery_status": recovered_itinerary.status.value,
        "logs": recovered_itinerary.agent_logs[-5:],
    }


@app.get("/system/health")
async def system_health():
    """Get system health status"""
    return {
        "a2a_protocol": {
            "registered_agents": len(a2a_protocol.agents),
            "message_history_count": len(a2a_protocol.message_history),
        },
        "mcp_context": {
            "context_entries": len(mcp_context.context_store),
            "access_log_count": len(mcp_context.access_log),
        },
        "agent_health": verification_agent.check_agent_health(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/system/a2a-messages")
async def get_a2a_messages(agent_id: str = None):
    """Get A2A protocol message history"""
    messages = a2a_protocol.get_message_history(agent_id)
    return {"count": len(messages), "messages": messages[-50:]}


@app.get("/system/mcp-context")
async def get_mcp_context():
    """Get MCP context snapshot"""
    return {
        "context": mcp_context.get_full_context(),
        "dependencies": mcp_context.dependencies,
        "conflicts": mcp_context.detect_conflicts(),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time agent updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    # Create a unique session ID for this connection
    session_id = id(websocket)
    conversation_histories[session_id] = []

    try:
        while True:
            data = await websocket.receive_text()
            print(f"[WebSocket] Received message: {data}")
            
            # Add user message to history
            conversation_histories[session_id].append({
                "role": "user",
                "content": data
            })
            
            # Echo user message in a structured format
            await websocket.send_text(json.dumps({"type": "user", "text": data}))
            
            # Check if we have enough info to plan the trip
            travel_info = await extract_travel_info(conversation_histories[session_id])
            print(f"[WebSocket] Travel info extracted: {travel_info}")
            
            if travel_info and travel_info.get("ready_to_plan"):
                # User has provided enough information - call the agent system
                try:
                    # Validate all required fields are present and not None
                    required_fields = ["origin", "destination", "start_date", "end_date", "budget"]
                    missing_fields = [f for f in required_fields if not travel_info.get(f)]
                    
                    if missing_fields:
                        # Not actually ready - continue conversation
                        reply = await generate_gemini_response(data, conversation_histories[session_id])
                    else:
                        # Create TravelRequest
                        request = TravelRequest(
                            request_id=str(uuid.uuid4()),
                            origin=str(travel_info["origin"]),
                            destination=str(travel_info["destination"]),
                            start_date=str(travel_info["start_date"]),
                            end_date=str(travel_info["end_date"]),
                            budget=float(travel_info["budget"]),
                            travelers=int(travel_info.get("travelers", 1))
                        )
                        
                        # Send status update
                        await websocket.send_text(json.dumps({
                            "type": "system",
                            "text": "Perfect! I have all the information I need. Let me search for the best options for you... 🔍"
                        }))
                        
                        # Call MetaAgent to get real travel data
                        itinerary = await meta_agent.process_travel_request(request)
                        
                        # Build comprehensive data for Gemini to format
                        travel_data = {
                            "origin": request.origin,
                            "destination": request.destination,
                            "dates": f"{request.start_date} to {request.end_date}",
                            "travelers": request.travelers,
                            "budget": request.budget,
                            "selected_outbound": None,
                            "selected_return": None,
                            "selected_hotel": None,
                            "weather": [],
                            "activities": [],
                            "total_cost": itinerary.total_cost
                        }
                        
                        if itinerary.outbound_flight:
                            travel_data["selected_outbound"] = {
                                "airline": itinerary.outbound_flight.airline,
                                "flight_number": getattr(itinerary.outbound_flight, 'flight_number', 'N/A'),
                                "departure": itinerary.outbound_flight.departure_time,
                                "arrival": itinerary.outbound_flight.arrival_time,
                                "duration": itinerary.outbound_flight.duration,
                                "stops": itinerary.outbound_flight.stops,
                                "price": itinerary.outbound_flight.price
                            }
                        
                        if itinerary.return_flight:
                            travel_data["selected_return"] = {
                                "airline": itinerary.return_flight.airline,
                                "flight_number": getattr(itinerary.return_flight, 'flight_number', 'N/A'),
                                "departure": itinerary.return_flight.departure_time,
                                "arrival": itinerary.return_flight.arrival_time,
                                "duration": itinerary.return_flight.duration,
                                "stops": itinerary.return_flight.stops,
                                "price": itinerary.return_flight.price
                            }
                        
                        if itinerary.hotel:
                            travel_data["selected_hotel"] = {
                                "name": itinerary.hotel.name,
                                "location": itinerary.hotel.location,
                                "check_in": itinerary.hotel.check_in,
                                "check_out": itinerary.hotel.check_out,
                                "price_per_night": itinerary.hotel.price_per_night,
                                "total_price": itinerary.hotel.total_price,
                                "rating": itinerary.hotel.rating,
                                "amenities": itinerary.hotel.amenities
                            }
                        
                        if itinerary.weather_forecast:
                            for w in itinerary.weather_forecast:
                                travel_data["weather"].append({
                                    "date": w.date,
                                    "conditions": w.conditions,
                                    "temp_high": w.temperature_high,
                                    "temp_low": w.temperature_low,
                                    "precipitation": w.precipitation_chance
                                })
                        
                        if itinerary.activities:
                            for a in itinerary.activities[:5]:  # Limit to top 5
                                travel_data["activities"].append({
                                    "name": a.name,
                                    "description": a.description,
                                    "location": a.location,
                                    "duration": a.duration,
                                    "price": a.price,
                                    "category": a.category
                                })
                        
                        # Format through Gemini for conversational presentation
                        import json as json_lib
                        formatting_prompt = f"""You are a professional travel consultant. Format this travel itinerary data into a beautiful, well-organized, conversational response for the user.

Travel Data:
{json_lib.dumps(travel_data, indent=2)}

Create a response that:
1. Starts with an enthusiastic greeting about their trip
2. Shows the selected flights with ALL details (airline, flight number, times, duration, stops, price)
3. Shows the selected hotel with ALL details (name, location, rating, price per night, total, amenities)
4. Shows the weather forecast for each day
5. Lists the top activities with descriptions and prices
6. Ends with the total cost and a friendly closing

Use emojis (✈️, 🏨, 🌤️, 🎯, 💰) and make it engaging and easy to read. Use markdown formatting with headers and bullet points."""
                        
                        try:
                            reply = await generate_gemini_response(formatting_prompt, [])
                            print(f"Gemini formatted response: {reply[:100]}...")
                        except Exception as format_error:
                            print(f"Gemini formatting failed: {format_error}. Using simple format.")
                            # Fallback to simple formatting
                            reply = f"""🎉 Great news! I found some excellent options for your trip from {request.origin} to {request.destination}!

✈️ **Flights**
- Outbound: {travel_data['selected_outbound']['airline']} {travel_data['selected_outbound']['flight_number']} - ${travel_data['selected_outbound']['price']}
- Return: {travel_data['selected_return']['airline']} {travel_data['selected_return']['flight_number']} - ${travel_data['selected_return']['price']}

🏨 **Hotel**
{travel_data['selected_hotel']['name']} - ${travel_data['selected_hotel']['total_price']} total

💰 **Total Cost**: ${travel_data['total_cost']}
"""
                    
                except Exception as e:
                    reply = f"I encountered an error while planning your trip: {str(e)}. Let me try to help you differently."
            else:
                # Continue conversation - not ready to plan yet
                print(f"[WebSocket] Not ready to plan, continuing conversation")
                reply = await generate_gemini_response(data, conversation_histories[session_id])
                print(f"[WebSocket] Gemini response: {reply[:100]}...")
            
            # Add assistant response to history
            conversation_histories[session_id].append({
                "role": "assistant",
                "content": reply
            })
            
            await websocket.send_text(json.dumps({"type": "agent", "text": reply}))
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        # Clean up conversation history
        if session_id in conversation_histories:
            del conversation_histories[session_id]


async def broadcast_update(message: dict):
    """Broadcast updates to all connected WebSocket clients"""
    disconnected = []
    for ws in active_websockets:
        try:
            await ws.send_text(json.dumps(message))
        except:
            disconnected.append(ws)

    for ws in disconnected:
        active_websockets.remove(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
