import random
from datetime import datetime
from typing import List, Dict


class MockHotelAPI:
    """Mock Hotel API for demonstration purposes"""

    HOTELS = [
        {
            "name": "Grand Plaza Hotel",
            "amenities": ["WiFi", "Pool", "Gym", "Restaurant", "Spa"],
            "rating": 4.5,
        },
        {
            "name": "Downtown Comfort Inn",
            "amenities": ["WiFi", "Breakfast", "Parking"],
            "rating": 4.0,
        },
        {
            "name": "Luxury Suites",
            "amenities": ["WiFi", "Pool", "Gym", "Restaurant", "Spa", "Concierge"],
            "rating": 4.8,
        },
        {
            "name": "Budget Stay Hotel",
            "amenities": ["WiFi", "Parking"],
            "rating": 3.5,
        },
        {
            "name": "Riverside Resort",
            "amenities": ["WiFi", "Pool", "Beach Access", "Restaurant", "Bar"],
            "rating": 4.7,
        },
    ]

    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate

    def search_hotels(
        self, location: str, check_in: str, check_out: str, guests: int = 1
    ) -> List[Dict]:
        """Search for hotels"""
        if random.random() < self.failure_rate:
            raise Exception("Hotel API temporarily unavailable")

        check_in_date = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)
        nights = (check_out_date - check_in_date).days

        hotels = []
        for hotel_template in self.HOTELS:
            price_per_night = round(random.uniform(80, 300), 2)
            hotel = {
                "hotel_id": f"HTL{random.randint(1000, 9999)}",
                "name": hotel_template["name"],
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "price_per_night": price_per_night,
                "total_price": round(price_per_night * nights, 2),
                "rating": hotel_template["rating"],
                "amenities": hotel_template["amenities"],
            }
            hotels.append(hotel)

        return sorted(hotels, key=lambda x: x["total_price"])

    def get_hotel_details(self, hotel_id: str) -> Dict:
        """Get hotel details by ID"""
        if random.random() < self.failure_rate:
            raise Exception("Hotel API temporarily unavailable")

        return {
            "hotel_id": hotel_id,
            "availability": "Available",
            "rooms_available": random.randint(1, 20),
        }
