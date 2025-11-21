import random
from datetime import datetime
from typing import List, Dict


from src.apis.amadeus_client import AmadeusClient

class MockHotelAPI:
    """Hotel API using Amadeus with fallback to mock"""

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
        self.amadeus = AmadeusClient()

    def search_hotels(
        self, location: str, check_in: str, check_out: str, guests: int = 1
    ) -> List[Dict]:
        """Search for hotels"""
        if random.random() < self.failure_rate:
            raise Exception("Hotel API temporarily unavailable")

        check_in_date = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)
        nights = (check_out_date - check_in_date).days

        if self.amadeus.client:
            try:
                # Resolve location to IATA code
                loc_data = self.amadeus.get_location_coords(location)
                if loc_data and loc_data.get("iataCode"):
                    city_code = loc_data["iataCode"]
                    real_hotels = self.amadeus.search_hotel_offers(city_code, check_in, check_out, guests)
                    
                    hotels = []
                    for offer in real_hotels:
                        hotel_data = offer.get("hotel", {})
                        offers = offer.get("offers", [])
                        if not offers: continue
                        
                        price_obj = offers[0].get("price", {})
                        price_total = float(price_obj.get("total", 0))
                        
                        # Calculate per night roughly
                        price_per_night = price_total / max(1, nights)
                        
                        h = {
                            "hotel_id": hotel_data.get("hotelId"),
                            "name": hotel_data.get("name"),
                            "location": location,
                            "check_in": check_in,
                            "check_out": check_out,
                            "price_per_night": round(price_per_night, 2),
                            "total_price": round(price_total, 2),
                            "rating": float(hotel_data.get("rating", 0)) if hotel_data.get("rating") else 4.0, # Default if missing
                            "amenities": ["Standard Amenities"] # Amadeus basic offer search might not have full amenities list easily accessible
                        }
                        hotels.append(h)
                    
                    if hotels:
                        return sorted(hotels, key=lambda x: x["total_price"])
            except Exception as e:
                print(f"Amadeus hotel search failed: {e}. Falling back to mock.")

        # Fallback to mock
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
