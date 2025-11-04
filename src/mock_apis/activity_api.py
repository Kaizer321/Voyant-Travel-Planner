import random
from typing import List, Dict


class MockActivityAPI:
    """Mock Activity API for demonstration purposes"""

    ACTIVITIES = {
        "Sightseeing": [
            {"name": "City Walking Tour", "duration": "3h", "price_range": (30, 50)},
            {"name": "Museum Visit", "duration": "2h", "price_range": (15, 35)},
            {"name": "Architectural Tour", "duration": "4h", "price_range": (40, 70)},
        ],
        "Adventure": [
            {"name": "Kayaking", "duration": "2h", "price_range": (40, 60)},
            {"name": "Hiking Expedition", "duration": "5h", "price_range": (50, 80)},
            {"name": "Zip Lining", "duration": "3h", "price_range": (60, 100)},
        ],
        "Cultural": [
            {"name": "Cooking Class", "duration": "3h", "price_range": (60, 90)},
            {"name": "Traditional Dance Show", "duration": "2h", "price_range": (35, 55)},
            {"name": "Art Gallery Tour", "duration": "2h", "price_range": (20, 40)},
        ],
        "Relaxation": [
            {"name": "Spa Day", "duration": "4h", "price_range": (80, 150)},
            {"name": "Beach Day", "duration": "full day", "price_range": (0, 20)},
            {"name": "Yoga Session", "duration": "1h", "price_range": (25, 45)},
        ],
    }

    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate

    def search_activities(
        self, location: str, category: str = None, max_results: int = 5
    ) -> List[Dict]:
        """Search for activities"""
        if random.random() < self.failure_rate:
            raise Exception("Activity API temporarily unavailable")

        activities = []
        categories = [category] if category else list(self.ACTIVITIES.keys())

        for cat in categories:
            for activity_template in self.ACTIVITIES.get(cat, []):
                price = round(
                    random.uniform(
                        activity_template["price_range"][0],
                        activity_template["price_range"][1],
                    ),
                    2,
                )

                activity = {
                    "activity_id": f"ACT{random.randint(1000, 9999)}",
                    "name": activity_template["name"],
                    "description": f"Enjoy {activity_template['name']} in {location}",
                    "location": location,
                    "date": "flexible",
                    "duration": activity_template["duration"],
                    "price": price,
                    "category": cat,
                }
                activities.append(activity)

                if len(activities) >= max_results:
                    break

            if len(activities) >= max_results:
                break

        return activities[:max_results]

    def get_activity_details(self, activity_id: str) -> Dict:
        """Get activity details by ID"""
        if random.random() < self.failure_rate:
            raise Exception("Activity API temporarily unavailable")

        return {
            "activity_id": activity_id,
            "availability": "Available",
            "spots_available": random.randint(1, 15),
        }
