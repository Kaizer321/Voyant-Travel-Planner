from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid
from datetime import datetime
import asyncio
import json

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

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"echo": data}))
    except WebSocketDisconnect:
        active_websockets.remove(websocket)


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
