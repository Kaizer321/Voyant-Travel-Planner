from crewai import Agent, Task
from typing import Dict, Any
from src.mock_apis.activity_api import MockActivityAPI
from src.protocols.a2a_protocol import AgentInterface
from src.protocols.mcp_context import MCPContext


class ActivityAgent(AgentInterface):
    """
    Activity Agent: Recommends and books activities, tours, and experiences.
    Coordinates with Weather Agent to suggest weather-appropriate activities
    and with Flight/Hotel Agents to optimize activity scheduling.
    """

    def __init__(self, agent_id: str = "activity_agent", failure_rate: float = 0.0):
        super().__init__(agent_id)
        self.api = MockActivityAPI(failure_rate=failure_rate)
        self.agent = Agent(
            role="Activity and Experience Curator",
            goal="Recommend and book engaging activities that match traveler interests and schedule",
            backstory="Local experiences expert with deep knowledge of destinations worldwide. "
            "Specializes in creating memorable travel experiences tailored to individual preferences.",
            verbose=True,
            allow_delegation=False,
        )

    async def receive_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages from other agents"""
        msg_type = message.get("type", "")

        if msg_type == "search_activities":
            return await self.search_activities(message.get("content", {}))
        elif msg_type == "get_details":
            return await self.get_activity_details(message.get("content", {}))
        else:
            return {"status": "error", "message": "Unknown message type"}

    async def search_activities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for activities based on parameters"""
        try:
            location = params.get("location")
            category = params.get("category")
            max_results = params.get("max_results", 5)

            activities = self.api.search_activities(location, category, max_results)

            return {
                "status": "success",
                "agent": self.agent_id,
                "data": activities,
                "message": f"Found {len(activities)} activities in {location}",
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_id,
                "message": f"Activity search failed: {str(e)}",
            }

    async def get_activity_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed activity information"""
        try:
            activity_id = params.get("activity_id")
            details = self.api.get_activity_details(activity_id)

            return {
                "status": "success",
                "agent": self.agent_id,
                "data": details,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_id,
                "message": f"Failed to get activity details: {str(e)}",
            }

    def create_task(self, description: str, context: MCPContext = None) -> Task:
        """Create a CrewAI task for this agent"""
        return Task(
            description=description,
            agent=self.agent,
            expected_output="Activity recommendations with descriptions, pricing, and scheduling details",
        )
