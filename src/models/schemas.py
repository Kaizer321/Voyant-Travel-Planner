from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PlanningStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RE_PLANNING = "re_planning"


class TravelRequest(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    origin: str = Field(..., description="Starting location")
    destination: str = Field(..., description="Destination location")
    start_date: str = Field(..., description="Trip start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Trip end date (YYYY-MM-DD)")
    budget: float = Field(..., description="Total budget in USD")
    travelers: int = Field(default=1, description="Number of travelers")
    preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="User preferences"
    )


class FlightDetails(BaseModel):
    flight_id: str
    airline: str
    departure_time: str
    arrival_time: str
    price: float
    duration: str
    stops: int = 0


class HotelDetails(BaseModel):
    hotel_id: str
    name: str
    location: str
    check_in: str
    check_out: str
    price_per_night: float
    total_price: float
    rating: float
    amenities: List[str] = Field(default_factory=list)


class WeatherInfo(BaseModel):
    location: str
    date: str
    temperature_high: float
    temperature_low: float
    conditions: str
    precipitation_chance: int


class ActivityDetails(BaseModel):
    activity_id: str
    name: str
    description: str
    location: str
    date: str
    duration: str
    price: float
    category: str


class TravelItinerary(BaseModel):
    request_id: str
    status: PlanningStatus
    outbound_flight: Optional[FlightDetails] = None
    return_flight: Optional[FlightDetails] = None
    hotel: Optional[HotelDetails] = None
    weather_forecast: List[WeatherInfo] = Field(default_factory=list)
    activities: List[ActivityDetails] = Field(default_factory=list)
    total_cost: float = 0.0
    remaining_budget: float = 0.0
    agent_logs: List[str] = Field(default_factory=list)
    verification_results: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMessage(BaseModel):
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VerificationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
