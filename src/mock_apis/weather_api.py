import random
from datetime import datetime, timedelta
from typing import List, Dict
import requests
import os

class MockWeatherAPI:
    """Weather API using OpenWeatherMap with fallback to mock"""

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
        self.api_key = os.getenv("OPENWEATHER_API_KEY")

    def _get_coords(self, location: str):
        if not self.api_key: return None
        try:
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={self.api_key}"
            resp = requests.get(url)
            if resp.status_code == 200 and resp.json():
                return resp.json()[0]
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None

    def get_forecast(self, location: str, days: int = 7) -> List[Dict]:
        """Get weather forecast"""
        if random.random() < self.failure_rate:
            raise Exception("Weather API temporarily unavailable")

        if self.api_key:
            coords = self._get_coords(location)
            if coords:
                try:
                    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={coords['lat']}&lon={coords['lon']}&units=metric&appid={self.api_key}"
                    resp = requests.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        forecast = []
                        # OWM returns 3-hour steps. We'll pick one per day (roughly every 8th item)
                        for item in data.get("list", [])[::8]:
                            weather = {
                                "location": location,
                                "date": item.get("dt_txt", "").split(" ")[0],
                                "temperature_high": item.get("main", {}).get("temp_max"),
                                "temperature_low": item.get("main", {}).get("temp_min"),
                                "conditions": item.get("weather", [{}])[0].get("main"),
                                "precipitation_chance": int(item.get("pop", 0) * 100),
                            }
                            forecast.append(weather)
                        return forecast[:days]
                except Exception as e:
                    print(f"OWM forecast error: {e}")

        # Fallback to mock
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

        if self.api_key:
            coords = self._get_coords(location)
            if coords:
                try:
                    url = f"http://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&units=metric&appid={self.api_key}"
                    resp = requests.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        return {
                            "location": location,
                            "temperature": data.get("main", {}).get("temp"),
                            "conditions": data.get("weather", [{}])[0].get("main"),
                            "humidity": data.get("main", {}).get("humidity"),
                            "wind_speed": data.get("wind", {}).get("speed"),
                        }
                except Exception as e:
                    print(f"OWM weather error: {e}")

        # Fallback to mock
        return {
            "location": location,
            "temperature": round(random.uniform(15, 30), 1),
            "conditions": random.choice(self.WEATHER_CONDITIONS),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 30),
        }
