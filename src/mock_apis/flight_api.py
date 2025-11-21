import random
from datetime import datetime, timedelta
from typing import List, Dict


from src.apis.amadeus_client import AmadeusClient

class MockFlightAPI:
    """Flight API using Amadeus with fallback to mock"""

    AIRLINES = [
        "United Airlines",
        "Delta Air Lines",
        "American Airlines",
        "Southwest Airlines",
        "JetBlue",
    ]

    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate
        self._cache: Dict[str, List[Dict]] = {}
        self._request_count = 0
        self._last_reset = datetime.utcnow()
        self._rate_limit = 60  # requests per minute
        self.amadeus = AmadeusClient()

    def search_flights(
        self, origin: str, destination: str, date: str, passengers: int = 1
    ) -> List[Dict]:
        """Search for flights"""
        self._check_rate_limit()
        
        cache_key = f"{origin}-{destination}-{date}-{passengers}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if random.random() < self.failure_rate:
            raise Exception("Flight API temporarily unavailable")

        if self.amadeus.client:
            try:
                # Convert city names to IATA codes
                origin_code = origin
                dest_code = destination
                
                # Try to get IATA codes if inputs look like city names (not 3-letter codes)
                if len(origin) > 3:
                    origin_info = self.amadeus.get_location_coords(origin)
                    if origin_info and 'iataCode' in origin_info:
                        origin_code = origin_info['iataCode']
                    else:
                        print(f"Could not find IATA code for origin: {origin}")
                        raise Exception(f"Invalid origin city: {origin}")
                
                if len(destination) > 3:
                    dest_info = self.amadeus.get_location_coords(destination)
                    if dest_info and 'iataCode' in dest_info:
                        dest_code = dest_info['iataCode']
                    else:
                        print(f"Could not find IATA code for destination: {destination}")
                        raise Exception(f"Invalid destination city: {destination}")
                
                print(f"Searching flights: {origin} ({origin_code}) -> {destination} ({dest_code}) on {date}")
                real_flights = self.amadeus.search_flights(origin_code, dest_code, date, passengers)
                
                # Transform Amadeus response to our schema
                flights = []
                for offer in real_flights:
                    itineraries = offer.get("itineraries", [])
                    if not itineraries: continue
                    
                    segments = itineraries[0].get("segments", [])
                    if not segments: continue
                    
                    first_segment = segments[0]
                    last_segment = segments[-1]
                    
                    price = float(offer.get("price", {}).get("total", 0))
                    
                    flight = {
                        "flight_id": offer.get("id"),
                        "airline": first_segment.get("carrierCode"),
                        "flight_number": f"{first_segment.get('carrierCode')}{first_segment.get('number')}",
                        "origin": first_segment.get("departure", {}).get("iataCode"),
                        "destination": last_segment.get("arrival", {}).get("iataCode"),
                        "departure_time": first_segment.get("departure", {}).get("at"),
                        "arrival_time": last_segment.get("arrival", {}).get("at"),
                        "price": price,
                        "duration": itineraries[0].get("duration"),
                        "stops": len(segments) - 1
                    }
                    flights.append(flight)
                
                results = sorted(flights, key=lambda x: x["price"])
                self._cache[cache_key] = results
                return results
            except Exception as e:
                print(f"Amadeus search failed: {e}. Falling back to mock.")
        
        # Fallback to mock implementation
        flights = []
        for i in range(3):
            departure_time = datetime.fromisoformat(date) + timedelta(hours=6 + i * 4)
            arrival_time = departure_time + timedelta(hours=random.randint(2, 5))

            flight = {
                "flight_id": f"FL{random.randint(1000, 9999)}",
                "airline": random.choice(self.AIRLINES),
                "departure_time": departure_time.isoformat(),
                "arrival_time": arrival_time.isoformat(),
                "price": round(random.uniform(200, 800) * passengers, 2),
                "duration": f"{(arrival_time - departure_time).seconds // 3600}h {((arrival_time - departure_time).seconds % 3600) // 60}m",
                "stops": random.choice([0, 0, 0, 1]),
            }
            flights.append(flight)

        results = sorted(flights, key=lambda x: x["price"])
        self._cache[cache_key] = results
        return results

    def _check_rate_limit(self):
        """Check if rate limit exceeded"""
        now = datetime.utcnow()
        if (now - self._last_reset).seconds > 60:
            self._request_count = 0
            self._last_reset = now
        
        self._request_count += 1
        if self._request_count > self._rate_limit:
            raise Exception(f"Rate limit exceeded ({self._rate_limit} requests/min)")

    def get_flight_details(self, flight_id: str) -> Dict:
        """Get flight details by ID"""
        if random.random() < self.failure_rate:
            raise Exception("Flight API temporarily unavailable")

        return {
            "flight_id": flight_id,
            "status": "Available",
            "seats_available": random.randint(5, 50),
        }
