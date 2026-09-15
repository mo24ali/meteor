import os
import json
import time
import requests
from datetime import datetime
from src.bronze.fetch_cities import load_moroccan_cities

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def fetch_weather_for_city(lat: float, lng: float, retries: int = 3, backoff_factor: float = 2.0) -> dict:
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "weather_code"
        ],
        "timezone": "auto"
    }
    
  
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
            response.raise_for_status() 
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f" Attempt {attempt} failed: {e}")
            if attempt == retries:
                raise e
            
            sleep_time = backoff_factor ** attempt
            time.sleep(sleep_time)

def run_bronze_ingestion():
    
    cities_df = load_moroccan_cities()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join("data", "bronze", today_str)
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    for _, row in cities_df.iterrows():
        city_name = row['city']
        lat, lng = row['lat'], row['lng']
        
        print(f" Ingesting weather data for {city_name}...")
        try:
            raw_data = fetch_weather_for_city(lat, lng)
            
            
            payload = {
                "city": city_name,
                "latitude": lat,
                "longitude": lng,
                "ingested_at": datetime.now().isoformat(),
                "raw_api_response": raw_data
            }
            results.append(payload)
            
            
            time.sleep(1.2)
            
        except Exception as err:
            print(f" Skipped {city_name} due to persistent error: {err}")
    
    file_path = os.path.join(output_dir, "raw_weather_snapshot.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f" Bronze Ingestion Complete! Raw snapshot saved to {file_path}")

if __name__ == "__main__":
    run_bronze_ingestion()      