import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load env
load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

from src.apis.amadeus_client import AmadeusClient
from src.mock_apis.weather_api import MockWeatherAPI

def test_amadeus():
    print("\n--- Testing Amadeus Client ---")
    client = AmadeusClient()
    if not client.client:
        print("❌ Amadeus Client not initialized (check keys)")
        return

    # Test Flight Search
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
    
    print(f"Testing Flight Search (NYC -> LON) for {future_date}...")
    try:
        flights = client.search_flights("NYC", "LON", future_date)
        print(f"✅ Found {len(flights)} flight offers")
        if flights:
            print(f"   Sample Price: {flights[0]['price']['total']} {flights[0]['price']['currency']}")
    except Exception as e:
        print(f"❌ Flight Search Failed: {e}")

    # Test Hotel Search
    print(f"\nTesting Hotel Search (Paris) for {future_date}...")
    try:
        hotels = client.search_hotel_offers("PAR", future_date, return_date)
        print(f"✅ Found {len(hotels)} hotel offers")
        if hotels:
            print(f"   Sample Hotel: {hotels[0]['hotel']['name']}")
    except Exception as e:
        print(f"❌ Hotel Search Failed: {e}")

    # Test Activity Search
    print("\nTesting Activity Search (Barcelona)...")
    try:
        # Barcelona coords
        activities = client.search_activities(41.3874, 2.1686)
        print(f"✅ Found {len(activities)} activities")
        if activities:
            print(f"   Sample Activity: {activities[0]['name']}")
    except Exception as e:
        print(f"❌ Activity Search Failed: {e}")

def test_weather():
    print("\n--- Testing OpenWeatherMap ---")
    weather_api = MockWeatherAPI()
    if not weather_api.api_key:
        print("❌ OpenWeatherMap Key not found")
        return

    print("Testing Forecast (London)...")
    try:
        forecast = weather_api.get_forecast("London")
        print(f"✅ Retrieved {len(forecast)} days forecast")
        if forecast:
            print(f"   Sample: {forecast[0]['date']} - {forecast[0]['conditions']} ({forecast[0]['temperature_high']}°C)")
    except Exception as e:
        print(f"❌ Forecast Failed: {e}")

if __name__ == "__main__":
    test_amadeus()
    test_weather()
