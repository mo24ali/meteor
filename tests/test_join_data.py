import pandas as pd
import pytest

from src.silver.join_data import enrich_weather_with_cities, load_city_metadata

META_CSV = "city,lat,lng,country,admin_name\n" \
           "Casablanca,33.5992,-7.62,Morocco,Casablanca-Settat\n" \
           "Rabat,34.0209,-6.8416,Morocco,Rabat-Salé-Kénitra\n"

WEATHER_CSV = "city_name,date,temp_max_celsius\n" \
              "Casablanca,2026-09-15,28.0\n" \
              "Rabat,2026-09-15,26.0\n"