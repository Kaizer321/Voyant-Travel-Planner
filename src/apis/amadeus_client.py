import os
from amadeus import Client, ResponseError
from typing import Dict, List, Any, Optional
from datetime import datetime

class AmadeusClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AmadeusClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        api_key = os.getenv("AMADEUS_API_KEY")
        api_secret = os.getenv("AMADEUS_API_SECRET")
        
        if not api_key or not api_secret:
            print("Warning: Amadeus API credentials not found in environment variables.")
            self.client = None
        else:
            try:
                self.client = Client(
                    client_id=api_key,
                    client_secret=api_secret
                )
                print("Amadeus Client initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize Amadeus Client: {e}")
                self.client = None

    def search_flights(self, origin: str, destination: str, departure_date: str, adults: int = 1) -> List[Dict]:
        if not self.client:
            raise Exception("Amadeus client not initialized")
        
        try:
            response = self.client.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                adults=adults,
                max=10
            )
            return response.data
        except ResponseError as error:
            raise Exception(f"Amadeus Flight Search Error: {error}")

    def search_hotel_offers(self, city_code: str, check_in: str, check_out: str, adults: int = 1) -> List[Dict]:
        if not self.client:
            raise Exception("Amadeus client not initialized")
            
        try:
            # Get hotels in city first (limit to 5 for demo to avoid huge requests)
            hotels_resp = self.client.reference_data.locations.hotels.by_city.get(
                cityCode=city_code
            )
            hotel_ids = [h['hotelId'] for h in hotels_resp.data[:5]]
            
            if not hotel_ids:
                return []

            # Get offers for these hotels
            response = self.client.shopping.hotel_offers_search.get(
                hotelIds=','.join(hotel_ids),
                checkInDate=check_in,
                checkOutDate=check_out,
                adults=adults
            )
            return response.data
        except ResponseError as error:
            print(f"Amadeus Hotel Search Error: {error}")
            return []
            
    def search_activities(self, latitude: float, longitude: float) -> List[Dict]:
        if not self.client:
            raise Exception("Amadeus client not initialized")
            
        try:
            response = self.client.shopping.activities.get(
                latitude=latitude,
                longitude=longitude,
                radius=20
            )
            return response.data
        except ResponseError as error:
            raise Exception(f"Amadeus Activity Search Error: {error}")

    def get_location_coords(self, keyword: str) -> Optional[Dict[str, float]]:
        """Helper to get coordinates for a city name"""
        if not self.client:
             raise Exception("Amadeus client not initialized")
             
        try:
            response = self.client.reference_data.locations.get(
                keyword=keyword,
                subType="CITY"
            )
            if response.data:
                geo = response.data[0]['geoCode']
                return {"latitude": geo['latitude'], "longitude": geo['longitude'], "iataCode": response.data[0]['iataCode']}
            return None
        except ResponseError as error:
            print(f"Location search error: {error}")
            return None
