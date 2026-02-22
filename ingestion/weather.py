import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Major port cities we track
PORT_CITIES = {
    "Los Angeles":    {"lat": 33.7295, "lon": -118.2620},
    "Shanghai":       {"lat": 31.2304, "lon": 121.4737},
    "Rotterdam":      {"lat": 51.9244, "lon": 4.4777},
    "Singapore":      {"lat": 1.3521,  "lon": 103.8198},
    "Dubai":          {"lat": 25.2048, "lon": 55.2708},
    "New York":       {"lat": 40.6840, "lon": -74.0440},
}

def fetch_weather(city: str) -> dict:
    """
    Fetches current weather for a port city.
    Returns a dict with temperature, wind speed, and a 
    weather_severity score (0-1) we compute from wind + rain.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    coords = PORT_CITIES.get(city)
    if not coords:
        raise ValueError(f"Unknown port city: {city}")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": coords["lat"],
        "lon": coords["lon"],
        "appid": api_key,
        "units": "metric"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    wind_speed = data["wind"]["speed"]           # m/s
    rain_mm = data.get("rain", {}).get("1h", 0)  # mm in last hour

    # Simple severity: normalize wind (>20 m/s = severe) + rain factor
    wind_score = min(wind_speed / 20.0, 1.0)
    rain_score = min(rain_mm / 50.0, 1.0)
    severity = round((wind_score * 0.7) + (rain_score * 0.3), 3)

    return {
        "city": city,
        "temperature_c": data["main"]["temp"],
        "wind_speed_ms": wind_speed,
        "rain_mm_1h": rain_mm,
        "weather_condition": data["weather"][0]["description"],
        "weather_severity": severity
    }

def fetch_all_ports() -> list[dict]:
    """Fetch weather for all tracked port cities."""
    results = []
    for city in PORT_CITIES:
        try:
            results.append(fetch_weather(city))
            print(f"  ✅ {city}")
        except Exception as e:
            print(f"  ❌ {city}: {e}")
    return results

if __name__ == "__main__":
    print("Fetching weather for all port cities...")
    data = fetch_all_ports()
    for d in data:
        print(f"{d['city']}: severity={d['weather_severity']}, wind={d['wind_speed_ms']}m/s")