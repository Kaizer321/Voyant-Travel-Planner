import random
from datetime import datetime, timedelta
from typing import List, Dict


class MockFlightAPI:
    """Mock Flight API for demonstration purposes"""

    AIRLINES = [
        "United Airlines",
        "Delta Air Lines",
        "American Airlines",
        "Southwest Airlines",
        "JetBlue",
    ]

    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate

    def search_flights(
        self, origin: str, destination: str, date: str, passengers: int = 1
    ) -> List[Dict]:
        """Search for flights"""
        if random.random() < self.failure_rate:
            raise Exception("Flight API temporarily unavailable")

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

        return sorted(flights, key=lambda x: x["price"])

    def get_flight_details(self, flight_id: str) -> Dict:
        """Get flight details by ID"""
        if random.random() < self.failure_rate:
            raise Exception("Flight API temporarily unavailable")

        return {
            "flight_id": flight_id,
            "status": "Available",
            "seats_available": random.randint(5, 50),
        }
