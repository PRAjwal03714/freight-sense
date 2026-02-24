"""
Global Port Registry - Production Data

Contains 50+ major container ports with validated coordinates.
"""

from typing import Dict, List, Optional

GLOBAL_PORTS = {
    # Asia-Pacific
    "Shanghai": {"country": "China", "region": "Asia", "lat": 31.23, "lon": 121.47},
    "Singapore": {"country": "Singapore", "region": "Asia", "lat": 1.29, "lon": 103.85},
    "Shenzhen": {"country": "China", "region": "Asia", "lat": 22.54, "lon": 114.06},
    "Ningbo": {"country": "China", "region": "Asia", "lat": 29.87, "lon": 121.55},
    "Hong Kong": {"country": "China", "region": "Asia", "lat": 22.28, "lon": 114.16},
    "Guangzhou": {"country": "China", "region": "Asia", "lat": 23.13, "lon": 113.26},
    "Qingdao": {"country": "China", "region": "Asia", "lat": 36.07, "lon": 120.38},
    "Busan": {"country": "South Korea", "region": "Asia", "lat": 35.18, "lon": 129.08},
    "Tianjin": {"country": "China", "region": "Asia", "lat": 39.14, "lon": 117.18},
    "Port Klang": {"country": "Malaysia", "region": "Asia", "lat": 3.00, "lon": 101.39},
    "Kaohsiung": {"country": "Taiwan", "region": "Asia", "lat": 22.62, "lon": 120.28},
    "Tokyo": {"country": "Japan", "region": "Asia", "lat": 35.65, "lon": 139.84},
    "Yokohama": {"country": "Japan", "region": "Asia", "lat": 35.44, "lon": 139.64},
    "Manila": {"country": "Philippines", "region": "Asia", "lat": 14.60, "lon": 120.98},
    "Jakarta": {"country": "Indonesia", "region": "Asia", "lat": -6.21, "lon": 106.85},
    "Bangkok": {"country": "Thailand", "region": "Asia", "lat": 13.75, "lon": 100.50},
    "Ho Chi Minh City": {"country": "Vietnam", "region": "Asia", "lat": 10.82, "lon": 106.63},
    "Chennai": {"country": "India", "region": "Asia", "lat": 13.08, "lon": 80.27},
    "Mumbai": {"country": "India", "region": "Asia", "lat": 19.08, "lon": 72.88},
    
    # Europe
    "Rotterdam": {"country": "Netherlands", "region": "Europe", "lat": 51.92, "lon": 4.48},
    "Antwerp": {"country": "Belgium", "region": "Europe", "lat": 51.22, "lon": 4.40},
    "Hamburg": {"country": "Germany", "region": "Europe", "lat": 53.55, "lon": 9.99},
    "Valencia": {"country": "Spain", "region": "Europe", "lat": 39.47, "lon": -0.38},
    "Barcelona": {"country": "Spain", "region": "Europe", "lat": 41.38, "lon": 2.17},
    "Piraeus": {"country": "Greece", "region": "Europe", "lat": 37.95, "lon": 23.64},
    "Felixstowe": {"country": "UK", "region": "Europe", "lat": 51.96, "lon": 1.35},
    "Le Havre": {"country": "France", "region": "Europe", "lat": 49.49, "lon": 0.11},
    "Genoa": {"country": "Italy", "region": "Europe", "lat": 44.41, "lon": 8.93},
    "Bremen": {"country": "Germany", "region": "Europe", "lat": 53.08, "lon": 8.80},
    
    # North America
    "Los Angeles": {"country": "USA", "region": "Americas", "lat": 33.74, "lon": -118.27},
    "Long Beach": {"country": "USA", "region": "Americas", "lat": 33.77, "lon": -118.19},
    "New York": {"country": "USA", "region": "Americas", "lat": 40.71, "lon": -74.01},
    "Savannah": {"country": "USA", "region": "Americas", "lat": 32.08, "lon": -81.09},
    "Houston": {"country": "USA", "region": "Americas", "lat": 29.76, "lon": -95.37},
    "Seattle": {"country": "USA", "region": "Americas", "lat": 47.61, "lon": -122.33},
    "Oakland": {"country": "USA", "region": "Americas", "lat": 37.80, "lon": -122.27},
    "Norfolk": {"country": "USA", "region": "Americas", "lat": 36.85, "lon": -76.29},
    "Charleston": {"country": "USA", "region": "Americas", "lat": 32.78, "lon": -79.93},
    "Vancouver": {"country": "Canada", "region": "Americas", "lat": 49.28, "lon": -123.12},
    "Montreal": {"country": "Canada", "region": "Americas", "lat": 45.50, "lon": -73.57},
    "Santos": {"country": "Brazil", "region": "Americas", "lat": -23.96, "lon": -46.33},
    "Cartagena": {"country": "Colombia", "region": "Americas", "lat": 10.39, "lon": -75.51},
    
    # Middle East & Africa
    "Dubai": {"country": "UAE", "region": "Middle East", "lat": 25.28, "lon": 55.31},
    "Jeddah": {"country": "Saudi Arabia", "region": "Middle East", "lat": 21.54, "lon": 39.17},
    "Port Said": {"country": "Egypt", "region": "Middle East", "lat": 31.26, "lon": 32.30},
    "Durban": {"country": "South Africa", "region": "Africa", "lat": -29.86, "lon": 31.03},
    "Cape Town": {"country": "South Africa", "region": "Africa", "lat": -33.92, "lon": 18.42},
    "Lagos": {"country": "Nigeria", "region": "Africa", "lat": 6.45, "lon": 3.40},
    "Mombasa": {"country": "Kenya", "region": "Africa", "lat": -4.05, "lon": 39.67},
    
    # Oceania
    "Sydney": {"country": "Australia", "region": "Oceania", "lat": -33.87, "lon": 151.21},
    "Melbourne": {"country": "Australia", "region": "Oceania", "lat": -37.81, "lon": 144.96},
    "Brisbane": {"country": "Australia", "region": "Oceania", "lat": -27.47, "lon": 153.03},
    "Auckland": {"country": "New Zealand", "region": "Oceania", "lat": -36.84, "lon": 174.76},
}

def get_all_ports() -> List[str]:
    """Get sorted list of all port names."""
    return sorted(GLOBAL_PORTS.keys())

def get_port_info(port_name: str) -> Optional[Dict]:
    """Get detailed info for a port."""
    return GLOBAL_PORTS.get(port_name)

def validate_port(port_name: str) -> bool:
    """Check if port exists in registry."""
    return port_name in GLOBAL_PORTS

def get_ports_by_region(region: str) -> List[str]:
    """Get all ports in a specific region."""
    return [
        name for name, info in GLOBAL_PORTS.items()
        if info["region"] == region
    ]