from crewai import Agent, Task
from typing import Dict, Any
from src.mock_apis.weather_api import MockWeatherAPI
from src.protocols.a2a_protocol import AgentInterface
from src.protocols.mcp_context import MCPContext


class WeatherAgent(AgentInterface):
    """
    Weather Agent: Provides real-time and forecasted weather information.
    Enables proactive itinerary adjustments and alerts other agents about
    potential weather-related disruptions.
    """

    def __init__(self, agent_id: str = "weather_agent", failure_rate: float = 0.0):
        super().__init__(agent_id)
        self.api = MockWeatherAPI(failure_rate=failure_rate)
        self.agent = Agent(
            role="Weather Forecasting Specialist",
            goal="Provide accurate weather forecasts and alerts for travel destinations",
            backstory="Meteorologist with expertise in travel weather patterns. "
            "Helps travelers prepare for weather conditions and plan activities accordingly.",
            verbose=True,
            allow_delegation=False,
        )

    async def receive_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages from other agents"""
        msg_type = message.get("type", "")

        if msg_type == "get_forecast":
            return await self.get_forecast(message.get("content", {}))
        elif msg_type == "get_current":
            return await self.get_current_weather(message.get("content", {}))
        else:
            return {"status": "error", "message": "Unknown message type"}

    async def get_forecast(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather forecast"""
        try:
            location = params.get("location")
            days = params.get("days", 7)

            forecast = self.api.get_forecast(location, days)

            return {
                "status": "success",
                "agent": self.agent_id,
                "data": forecast,
                "message": f"Retrieved {days}-day forecast for {location}",
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_id,
                "message": f"Weather forecast failed: {str(e)}",
            }

    async def get_current_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current weather"""
        try:
            location = params.get("location")
            weather = self.api.get_current_weather(location)

            return {
                "status": "success",
                "agent": self.agent_id,
                "data": weather,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.agent_id,
                "message": f"Failed to get current weather: {str(e)}",
            }

    def create_task(self, description: str, context: MCPContext = None) -> Task:
        """Create a CrewAI task for this agent"""
        return Task(
            description=description,
            agent=self.agent,
            expected_output="Weather forecast with temperatures, conditions, and precipitation chances",
        )
