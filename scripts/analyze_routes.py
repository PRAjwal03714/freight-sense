"""
Analyzes which routes have enough data for time-series modeling.

Why we need this:
- ARIMA needs at least 30-50 data points to learn patterns
- Some routes only have 2-3 shipments (not enough)
- We want a route with consistent traffic over time

What this does:
- Finds routes with 100+ shipments
- Shows their delay patterns
- Helps us pick a route for baseline testing
"""

import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("TIMESCALE_HOST", "localhost"),
        port=os.getenv("TIMESCALE_PORT", 5434),
        dbname=os.getenv("TIMESCALE_DB", "freightsense"),
        user=os.getenv("TIMESCALE_USER", "postgres"),
        password=os.getenv("TIMESCALE_PASSWORD", "postgres")
    )

def find_busy_routes():
    """Find routes with the most data points."""
    conn = get_connection()
    
    query = """
        SELECT 
            r.route_id,
            r.origin_port,
            r.dest_port,
            COUNT(*) as num_shipments,
            AVG(rm.delay_days) as avg_delay,
            STDDEV(rm.delay_days) as delay_stddev,
            MIN(rm.time) as first_shipment,
            MAX(rm.time) as last_shipment
        FROM routes r
        JOIN route_metrics rm ON r.route_id = rm.route_id
        GROUP BY r.route_id, r.origin_port, r.dest_port
        HAVING COUNT(*) >= 100
        ORDER BY num_shipments DESC
        LIMIT 20;
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print("\n📊 Top 20 Routes by Volume:\n")
    print(df.to_string(index=False))
    
    return df

def get_route_timeseries(route_id):
    """Get time-series data for a specific route."""
    conn = get_connection()
    
    query = """
        SELECT 
            time,
            delay_days
        FROM route_metrics
        WHERE route_id = %s
        ORDER BY time ASC;
    """
    
    df = pd.read_sql(query, conn, params=(route_id,))
    conn.close()
    
    return df

if __name__ == "__main__":
    print("🔍 Finding routes with sufficient data for modeling...")
    routes_df = find_busy_routes()
    
    if len(routes_df) > 0:
        # Get the busiest route
        top_route = routes_df.iloc[0]
        print(f"\n🎯 Top route: {top_route['origin_port']} → {top_route['dest_port']}")
        print(f"   Shipments: {top_route['num_shipments']}")
        print(f"   Avg delay: {top_route['avg_delay']:.2f} days")
        print(f"   Time span: {top_route['first_shipment']} to {top_route['last_shipment']}")