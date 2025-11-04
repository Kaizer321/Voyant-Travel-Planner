from crewai import Agent, Task
from typing import Dict, Any
from src.mock_apis.hotel_api import MockHotelAPI
from src.protocols.a2a_protocol import AgentInterface
from src.protocols.mcp_context import MCPContext


class HotelAgent(AgentInterface):
    """
    Hotel Agent: Manages hotel and alternative lodging searches.
    Ensures accommodation availability aligns with flight arrival times
    and weather conditions at the destination.
    """

    def __init__(self, agent_id: str = "hotel_agent", failure_rate: float = 0.0):
        super().__init__(agent_id)
        self.api = MockHotelAPI(failure_rate=failure_rate)
        self.agent = Agent(
            role="Accommodation Specialist",
            goal="Find the best hotel options matching location, amenities, and budget preferences",
            backstory="Experienced hotel concierge with extensive knowledge of accommodations worldwide. "
            "Skilled at matching travelers with perfect stays based on their needs and preferences.",
            verbose=True,
            allow_delegation=False,
        )

    async def receive_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages from other agents"""
        msg_type = message.get("type", "")

        if msg_type == "search_hotels":
            return await self.search_hotels(message.get("content", {}))
        elif msg_type == "get_details":
            return await self.get_hotel_details(message.get("content", {}))
        else:
            return {"status": "error", "message": "Unknown message type"}

    async def search_hotels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for hotels based on parameters"""
        try:
            location = params.get("location")
            check_in = params.get("check_in")
            check_out = params.get("check_out")
            guests = params.get("guests", 1)

            hotels = self.api.search_hotels(location, check_in, check_out, guests)

            return {
                "status": "success",
                "agent": self.agent_id,
                "data": hotels,
                "message": f"Found {len(hotels)} hotels in {location}",
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_id,
                "message": f"Hotel search failed: {str(e)}",
            }

    async def get_hotel_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed hotel information"""
        try:
            hotel_id = params.get("hotel_id")
            details = self.api.get_hotel_details(hotel_id)

            return {
                "status": "success",
                "agent": self.agent_id,
                "data": details,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_id,
                "message": f"Failed to get hotel details: {str(e)}",
            }

    def create_task(self, description: str, context: MCPContext = None) -> Task:
        """Create a CrewAI task for this agent"""
        return Task(
            description=description,
            agent=self.agent,
            expected_output="Hotel search results with pricing, amenities, and ratings",
        )
