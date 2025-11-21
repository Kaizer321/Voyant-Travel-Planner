import os
from crewai import Agent, Task, LLM
from typing import Dict, Any
from src.mock_apis.flight_api import MockFlightAPI
from src.protocols.a2a_protocol import AgentInterface
from src.protocols.mcp_context import MCPContext


class FlightAgent(AgentInterface):
    """
    Flight Agent: Handles flight search, booking, and schedule optimization.
    Coordinates with other agents to ensure flight schedules align with
    accommodation check-in times and activity bookings.
    """

    def __init__(self, agent_id: str = "flight_agent", failure_rate: float = 0.0):
        super().__init__(agent_id)
        self.api = MockFlightAPI(failure_rate=failure_rate)
        self.agent = Agent(
            role="Flight Booking Specialist",
            goal="Find the best flight options that match user preferences and budget constraints",
            backstory="Expert in airline operations with access to multiple flight booking systems. "
            "Skilled at finding optimal flight combinations considering price, duration, and convenience.",
            verbose=True,
            allow_delegation=False,
            llm=LLM(model=os.getenv("CREWAI_DEFAULT_MODEL", "gemini-1.5-flash")),
        )

    async def receive_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages from other agents"""
        msg_type = message.get("type", "")

        if msg_type == "search_flights":
            return await self.search_flights(message.get("content", {}))
        elif msg_type == "get_details":
            return await self.get_flight_details(message.get("content", {}))
        else:
            return {"status": "error", "message": "Unknown message type"}

    async def search_flights(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for flights based on parameters"""
        try:
            origin = params.get("origin")
            destination = params.get("destination")
            date = params.get("date")
            passengers = params.get("passengers", 1)

            flights = self.api.search_flights(origin, destination, date, passengers)

            return {
                "status": "success",
                "agent": self.agent_id,
                "data": flights,
                "message": f"Found {len(flights)} flights from {origin} to {destination}",
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_id,
                "message": f"Flight search failed: {str(e)}",
            }

    async def get_flight_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed flight information"""
        try:
            flight_id = params.get("flight_id")
            details = self.api.get_flight_details(flight_id)

            return {
                "status": "success",
                "agent": self.agent_id,
                "data": details,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_id,
                "message": f"Failed to get flight details: {str(e)}",
            }

    def create_task(self, description: str, context: MCPContext = None) -> Task:
        """Create a CrewAI task for this agent"""
        context_data = context.get_full_context() if context else {}
        return Task(
            description=description,
            agent=self.agent,
            expected_output="Flight search results with prices, times, and airline details",
        )
