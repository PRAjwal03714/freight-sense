"""
Weather Data Fetcher - Production Version with Redis Caching

Enhancements:
- Redis caching (5 min TTL)
- Uses port registry for accurate coordinates
- Better error handling
- Fallback to city name if port not in registry
"""

import os
import requests
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Try to import Redis cache
try:
    from utils.cache import cache
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False
    cache = None

def fetch_weather(city: str) -> Dict:
    """
    Fetch current weather for a port using OpenWeatherMap API.
    
    WITH REDIS CACHING:
    - First request: Fetches from API (1 sec)
    - Subsequent requests: Returns from cache (0.001 sec)
    - Cache expires after 5 minutes
    
    Args:
        city: Port name (e.g., "Shanghai", "Los Angeles")
    
    Returns:
        Dict with weather data including severity score (0-1)
    """
    
    # Check cache first
    if CACHE_ENABLED and cache:
        cache_key = f"weather:{city}"
        cached = cache.get(cache_key)
        
        if cached:
            print(f"  ⚡ {city}: Using cached weather")
            return cached
    
    # Cache miss - fetch from API
    print(f"  🌐 {city}: Fetching from API...")
    
    # Try to get coordinates from port registry
    try:
        from api.ports import get_port_info
        port_info = get_port_info(city)
        
        if port_info:
            # Use exact coordinates
            lat = port_info["lat"]
            lon = port_info["lon"]
        else:
            # Port not in registry, use city name search
            return fetch_weather_by_name(city)
            
    except (ImportError, Exception):
        # If port registry not available, use city name
        return fetch_weather_by_name(city)
    
    # Fetch weather using coordinates
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    if not API_KEY:
        raise ValueError("OPENWEATHER_API_KEY not set in .env")
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract weather data
        wind_speed = data["wind"]["speed"]
        rain_mm = data.get("rain", {}).get("1h", 0)
        
        # Calculate severity score (0-1)
        wind_score = min(wind_speed / 20.0, 1.0)
        rain_score = min(rain_mm / 50.0, 1.0)
        severity = round((wind_score * 0.7) + (rain_score * 0.3), 3)
        
        result = {
            "city": city,
            "temperature_c": round(data["main"]["temp"], 2),
            "wind_speed_ms": round(wind_speed, 2),
            "rain_mm_1h": round(rain_mm, 2),
            "weather_condition": data["weather"][0]["description"],
            "weather_severity": severity
        }
        
        # Cache for 5 minutes (300 seconds)
        if CACHE_ENABLED and cache:
            cache.set(f"weather:{city}", result, ttl=300)
            print(f"  💾 {city}: Cached for 5 min")
        
        return result
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Weather API error for {city}: {str(e)}")


def fetch_weather_by_name(city: str) -> Dict:
    """
    Fallback: Fetch weather using city name instead of coordinates.
    Also uses Redis caching.
    """
    
    # Check cache
    if CACHE_ENABLED and cache:
        cache_key = f"weather:name:{city}"
        cached = cache.get(cache_key)
        if cached:
            return cached
    
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    if not API_KEY:
        raise ValueError("OPENWEATHER_API_KEY not set in .env")
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        wind_speed = data["wind"]["speed"]
        rain_mm = data.get("rain", {}).get("1h", 0)
        
        wind_score = min(wind_speed / 20.0, 1.0)
        rain_score = min(rain_mm / 50.0, 1.0)
        severity = round((wind_score * 0.7) + (rain_score * 0.3), 3)
        
        result = {
            "city": city,
            "temperature_c": round(data["main"]["temp"], 2),
            "wind_speed_ms": round(wind_speed, 2),
            "rain_mm_1h": round(rain_mm, 2),
            "weather_condition": data["weather"][0]["description"],
            "weather_severity": severity
        }
        
        # Cache for 5 minutes
        if CACHE_ENABLED and cache:
            cache.set(f"weather:name:{city}", result, ttl=300)
        
        return result
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Weather API error for {city}: {str(e)}")


def fetch_all_ports() -> List[Dict]:
    """Fetch weather for all ports in registry."""
    results = []
    
    try:
        from api.ports import get_all_ports
        ports = get_all_ports()
    except ImportError:
        ports = ["Los Angeles", "Shanghai", "Rotterdam", "Singapore", "Dubai", "New York"]
    
    print(f"Fetching weather for {len(ports)} ports...")
    
    for city in ports:
        try:
            weather = fetch_weather(city)
            results.append(weather)
            print(f"  ✅ {city}: {weather['weather_severity']}")
        except Exception as e:
            print(f"  ❌ {city}: {str(e)[:50]}")
    
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("WEATHER DATA FETCH - ALL PORTS")
    print("=" * 70)
    
    data = fetch_all_ports()
    
    print(f"\n✅ Successfully fetched {len(data)} ports\n")