import random
from datetime import datetime, timedelta
from typing import List, Dict


class MockWeatherAPI:
    """Mock Weather API for demonstration purposes"""

    WEATHER_CONDITIONS = [
        "Sunny",
        "Partly Cloudy",
        "Cloudy",
        "Light Rain",
        "Rainy",
        "Thunderstorms",
        "Clear",
    ]

    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate

    def get_forecast(self, location: str, days: int = 7) -> List[Dict]:
        """Get weather forecast"""
        if random.random() < self.failure_rate:
            raise Exception("Weather API temporarily unavailable")

        forecast = []
        base_temp = random.uniform(15, 30)

        for i in range(days):
            date = (datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d")
            temp_variation = random.uniform(-5, 5)

            weather = {
                "location": location,
                "date": date,
                "temperature_high": round(base_temp + temp_variation + random.uniform(0, 8), 1),
                "temperature_low": round(base_temp + temp_variation - random.uniform(0, 5), 1),
                "conditions": random.choice(self.WEATHER_CONDITIONS),
                "precipitation_chance": random.randint(0, 100),
            }
            forecast.append(weather)

        return forecast

    def get_current_weather(self, location: str) -> Dict:
        """Get current weather"""
        if random.random() < self.failure_rate:
            raise Exception("Weather API temporarily unavailable")

        return {
            "location": location,
            "temperature": round(random.uniform(15, 30), 1),
            "conditions": random.choice(self.WEATHER_CONDITIONS),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 30),
        }
