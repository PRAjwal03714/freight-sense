"""
Weather data fetching with Redis caching
"""

import os
import requests
import redis
from dotenv import load_dotenv

load_dotenv()

# Initialize Redis
redis_url = os.getenv("REDIS_URL")
if redis_url:
    cache = redis.from_url(redis_url, decode_responses=True)
    print("✅ Redis cache connected")
else:
    cache = None
    print("⚠️  Redis not configured, running without cache")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

def fetch_weather(port_name: str) -> dict:
    """
    Fetch weather for a port with Redis caching (5-min TTL).
    """
    
    # Try cache first
    if cache:
        cache_key = f"weather:{port_name}"
        cached = cache.get(cache_key)
        if cached:
            import json
            print(f"   💨 Cache HIT for {port_name}")
            return json.loads(cached)
    
    # Cache miss - fetch from API
    print(f"   🌐 Fetching fresh weather for {port_name}...")
    
    # Get port coordinates (simplified - you can expand this)
    # Get port coordinates from JSON
    # Get port coordinates from ports.py
    from api.ports import GLOBAL_PORTS
    port_data = GLOBAL_PORTS.get(port_name)

    if port_data:
        port_info = {
            'lat': port_data['lat'],
            'lon': port_data['lon']
        }
    else:
        port_info = None
    
    if not port_info:
        return {
            'port': port_name,
            'weather_condition': 'Unknown',
            'weather_severity': 0.3,
            'temperature_c': 20,
            'wind_speed_ms': 5
        }
    
    # Call OpenWeather API
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': port_info['lat'],
        'lon': port_info['lon'],
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric'
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Calculate severity
        wind_speed = data['wind']['speed']
        weather_main = data['weather'][0]['main'].lower()
        
        severity = 0.2
        if 'rain' in weather_main or 'drizzle' in weather_main:
            severity = 0.5
        elif 'storm' in weather_main or 'thunderstorm' in weather_main:
            severity = 0.9
        elif wind_speed > 15:
            severity = 0.7
        elif wind_speed > 10:
            severity = 0.5
        
        result = {
            'port': port_name,
            'weather_condition': data['weather'][0]['description'],
            'weather_severity': severity,
            'temperature_c': data['main']['temp'],
            'wind_speed_ms': wind_speed
        }
        
        # Cache for 5 minutes (300 seconds)
        if cache:
            import json
            cache.setex(f"weather:{port_name}", 300, json.dumps(result))
            print(f"   💾 Cached weather for {port_name} (5-min TTL)")
        
        return result
        
    except Exception as e:
        print(f"   ⚠️  Weather API error: {str(e)}")
        return {
            'port': port_name,
            'weather_condition': 'Unknown',
            'weather_severity': 0.3,
            'temperature_c': 20,
            'wind_speed_ms': 5
        }