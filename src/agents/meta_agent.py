import os
from crewai import Agent, Crew, Task, Process, LLM
from typing import Dict, Any, List
from datetime import datetime
from src.models.schemas import TravelRequest, TravelItinerary, PlanningStatus, FlightDetails, HotelDetails, ActivityDetails, WeatherInfo
from src.protocols.a2a_protocol import A2AProtocol
from src.protocols.mcp_context import MCPContext
from src.agents.flight_agent import FlightAgent
from src.agents.hotel_agent import HotelAgent
from src.agents.weather_agent import WeatherAgent
from src.agents.activity_agent import ActivityAgent


class MetaAgent:
    """
    Meta-Agent: Central coordinator responsible for:
    - Parsing user requests and extracting planning constraints
    - Decomposing complex itineraries into manageable sub-tasks (Hierarchical Task Decomposition)
    - Orchestrating agent collaboration through A2A protocol
    - Monitoring overall system health and performance
    """

    def __init__(
        self,
        a2a_protocol: A2AProtocol,
        mcp_context: MCPContext,
        failure_rate: float = 0.0,
    ):
        self.a2a_protocol = a2a_protocol
        self.mcp_context = mcp_context
        self.failure_rate = failure_rate

        self.flight_agent = FlightAgent(failure_rate=failure_rate)
        self.hotel_agent = HotelAgent(failure_rate=failure_rate)
        self.weather_agent = WeatherAgent(failure_rate=failure_rate)
        self.activity_agent = ActivityAgent(failure_rate=failure_rate)

        self.a2a_protocol.register_agent("flight_agent", self.flight_agent)
        self.a2a_protocol.register_agent("hotel_agent", self.hotel_agent)
        self.a2a_protocol.register_agent("weather_agent", self.weather_agent)
        self.a2a_protocol.register_agent("activity_agent", self.activity_agent)

        self.meta_agent = Agent(
            role="Travel Planning Coordinator",
            goal="Orchestrate all travel agents to create a comprehensive, optimized travel itinerary",
            backstory="Senior travel planning manager with expertise in coordinating complex multi-agent systems. "
            "Ensures all aspects of travel are seamlessly integrated and optimized.",
            verbose=True,
            allow_delegation=True,
            llm=LLM(model=os.getenv("CREWAI_DEFAULT_MODEL", "gemini-1.5-flash")),
        )

    async def process_travel_request(
        self, request: TravelRequest
    ) -> TravelItinerary:
        """
        Process travel request through hierarchical task decomposition.
        The Meta-Agent breaks down the request into:
        1. Flight Booking (Outbound & Return)
        2. Hotel Booking (Dependent on Flights)
        3. Weather Forecast (Dependent on Location/Dates)
        4. Activity Recommendations (Dependent on Weather & Hotel)
        """
        itinerary = TravelItinerary(
            request_id=request.request_id,
            status=PlanningStatus.IN_PROGRESS,
            agent_logs=[],
        )

        self.mcp_context.set_context(
            "travel_request",
            request.model_dump(),
            "meta_agent",
            dependencies=[],
        )

        itinerary.agent_logs.append(
            f"[{datetime.utcnow().isoformat()}] Meta-Agent: Processing travel request {request.request_id}"
        )

        try:
            outbound_flight = await self._book_outbound_flight(request)
            if outbound_flight:
                itinerary.outbound_flight = outbound_flight
                itinerary.agent_logs.append(
                    f"[{datetime.utcnow().isoformat()}] Flight Agent: Outbound flight booked - {outbound_flight.flight_id}"
                )
                self.mcp_context.set_context(
                    "outbound_flight",
                    outbound_flight.model_dump(),
                    "flight_agent",
                    dependencies=["travel_request"],
                )

            return_flight = await self._book_return_flight(request)
            if return_flight:
                itinerary.return_flight = return_flight
                itinerary.agent_logs.append(
                    f"[{datetime.utcnow().isoformat()}] Flight Agent: Return flight booked - {return_flight.flight_id}"
                )
                self.mcp_context.set_context(
                    "return_flight",
                    return_flight.model_dump(),
                    "flight_agent",
                    dependencies=["travel_request"],
                )

            hotel = await self._book_hotel(request)
            if hotel:
                itinerary.hotel = hotel
                itinerary.agent_logs.append(
                    f"[{datetime.utcnow().isoformat()}] Hotel Agent: Accommodation booked - {hotel.name}"
                )
                self.mcp_context.set_context(
                    "hotel", hotel.model_dump(), "hotel_agent", dependencies=["outbound_flight"]
                )

            weather_forecast = await self._get_weather_forecast(request)
            itinerary.weather_forecast = weather_forecast
            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Weather Agent: Retrieved {len(weather_forecast)}-day forecast"
            )
            self.mcp_context.set_context(
                "weather_forecast",
                [w.model_dump() for w in weather_forecast],
                "weather_agent",
                dependencies=["travel_request"],
            )

            activities = await self._recommend_activities(request, weather_forecast)
            itinerary.activities = activities
            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Activity Agent: Recommended {len(activities)} activities"
            )
            self.mcp_context.set_context(
                "activities",
                [a.model_dump() for a in activities],
                "activity_agent",
                dependencies=["weather_forecast", "hotel"],
            )

            itinerary.total_cost = self._calculate_total_cost(itinerary)
            itinerary.remaining_budget = request.budget - itinerary.total_cost
            itinerary.status = PlanningStatus.COMPLETED

            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Meta-Agent: Travel planning completed. Total cost: ${itinerary.total_cost:.2f}"
            )

        except Exception as e:
            itinerary.status = PlanningStatus.FAILED
            itinerary.agent_logs.append(
                f"[{datetime.utcnow().isoformat()}] Meta-Agent: Error - {str(e)}"
            )

        return itinerary

    async def _book_outbound_flight(self, request: TravelRequest) -> FlightDetails | None:
        """Book outbound flight"""
        response = await self.a2a_protocol.send_message(
            "meta_agent",
            "flight_agent",
            "search_flights",
            {
                "origin": request.origin,
                "destination": request.destination,
                "date": request.start_date,
                "passengers": request.travelers,
            },
        )

        if response.get("status") == "success" and response.get("data"):
            flights = response["data"]
            for flight in flights:
                if flight["price"] <= request.budget * 0.4:
                    return FlightDetails(**flight)
            return FlightDetails(**flights[0]) if flights else None
        return None

    async def _book_return_flight(self, request: TravelRequest) -> FlightDetails | None:
        """Book return flight"""
        response = await self.a2a_protocol.send_message(
            "meta_agent",
            "flight_agent",
            "search_flights",
            {
                "origin": request.destination,
                "destination": request.origin,
                "date": request.end_date,
                "passengers": request.travelers,
            },
        )

        if response.get("status") == "success" and response.get("data"):
            flights = response["data"]
            for flight in flights:
                if flight["price"] <= request.budget * 0.4:
                    return FlightDetails(**flight)
            return FlightDetails(**flights[0]) if flights else None
        return None

    async def _book_hotel(self, request: TravelRequest) -> HotelDetails | None:
        """Book hotel"""
        response = await self.a2a_protocol.send_message(
            "meta_agent",
            "hotel_agent",
            "search_hotels",
            {
                "location": request.destination,
                "check_in": request.start_date,
                "check_out": request.end_date,
                "guests": request.travelers,
            },
        )

        if response.get("status") == "success" and response.get("data"):
            hotels = response["data"]
            for hotel in hotels:
                if hotel["total_price"] <= request.budget * 0.4:
                    return HotelDetails(**hotel)
            return HotelDetails(**hotels[0]) if hotels else None
        return None

    async def _get_weather_forecast(self, request: TravelRequest) -> List[WeatherInfo]:
        """Get weather forecast"""
        from datetime import datetime, timedelta

        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        days = (end_date - start_date).days + 1

        response = await self.a2a_protocol.send_message(
            "meta_agent",
            "weather_agent",
            "get_forecast",
            {"location": request.destination, "days": days},
        )

        if response.get("status") == "success" and response.get("data"):
            return [WeatherInfo(**w) for w in response["data"]]
        return []

    async def _recommend_activities(
        self, request: TravelRequest, weather_forecast: List[WeatherInfo]
    ) -> List[ActivityDetails]:
        """Recommend activities"""
        preferences = request.preferences or {}
        category = preferences.get("activity_preference", "Sightseeing")

        response = await self.a2a_protocol.send_message(
            "meta_agent",
            "activity_agent",
            "search_activities",
            {
                "location": request.destination,
                "category": category,
                "max_results": 3,
            },
        )

        if response.get("status") == "success" and response.get("data"):
            return [ActivityDetails(**a) for a in response["data"][:3]]
        return []

    def _calculate_total_cost(self, itinerary: TravelItinerary) -> float:
        """Calculate total cost of itinerary"""
        total = 0.0

        if itinerary.outbound_flight:
            total += itinerary.outbound_flight.price
        if itinerary.return_flight:
            total += itinerary.return_flight.price
        if itinerary.hotel:
            total += itinerary.hotel.total_price

        for activity in itinerary.activities:
            total += activity.price

        return round(total, 2)
