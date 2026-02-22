"""
Loads Kaggle supply chain data into TimescaleDB.

What this does:
1. Reads the 180K order CSV
2. Calculates delay_days for each shipment
3. Groups by route (origin_city → dest_city)
4. Inserts into our route_metrics table as time-series data

Why we need this:
- ARIMA and Chronos need historical delay patterns to learn from
- We're converting individual orders into route-level metrics over time
"""

import pandas as pd
import psycopg2
from datetime import datetime
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

def load_kaggle_data():
    print("📂 Loading Kaggle dataset...")
    df = pd.read_csv("data/kaggle/DataCoSupplyChainDataset.csv", encoding='latin-1')    
    print(f"✅ Loaded {len(df)} orders")
    
    # Calculate delay
    df['delay_days'] = df['Days for shipping (real)'] - df['Days for shipment (scheduled)']
    
    # Parse dates
    df['order_date'] = pd.to_datetime(df['order date (DateOrders)'], format='%m/%d/%Y %H:%M', errors='coerce')
    
    # Create route identifier
    df['route'] = df['Customer City'] + " → " + df['Order City']
    
    # Remove rows with missing critical data
    df = df.dropna(subset=['order_date', 'delay_days', 'route'])
    
    print(f"✅ After cleaning: {len(df)} valid orders")
    print(f"📊 Date range: {df['order_date'].min()} to {df['order_date'].max()}")
    print(f"📊 Unique routes: {df['route'].nunique()}")
    print(f"📊 Avg delay: {df['delay_days'].mean():.2f} days")
    
    return df

def insert_routes(df):
    """
    First, insert unique routes into the routes table.
    This gives us route_ids to reference in metrics.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Get unique routes
    routes = df.groupby('route').agg({
        'Customer City': 'first',
        'Order City': 'first',
        'Shipping Mode': lambda x: x.mode()[0] if len(x) > 0 else 'Standard Class',
        'Days for shipment (scheduled)': 'mean'
    }).reset_index()
    
    print(f"\n📥 Inserting {len(routes)} routes...")
    
    route_map = {}
    for _, row in routes.iterrows():
        origin = row['Customer City']
        dest = row['Order City']
        
        # Check if route already exists
        cur.execute("""
            SELECT route_id FROM routes 
            WHERE origin_port = %s AND dest_port = %s;
        """, (origin, dest))
        
        existing = cur.fetchone()
        if existing:
            route_map[f"{origin} → {dest}"] = existing[0]
        else:
            # Insert new route
            cur.execute("""
                INSERT INTO routes (origin_port, dest_port, carrier, avg_transit_days)
                VALUES (%s, %s, %s, %s)
                RETURNING route_id;
            """, (
                origin,
                dest,
                row['Shipping Mode'],
                int(row['Days for shipment (scheduled)'])
            ))
            route_id = cur.fetchone()[0]
            route_map[f"{origin} → {dest}"] = route_id
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Inserted routes, got {len(route_map)} route IDs")
    return route_map

def insert_metrics(df, route_map):
    """
    Insert actual delay metrics into the time-series table.
    Each order becomes one data point in our historical record.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    print(f"\n📥 Inserting {len(df)} delay metrics...")
    
    inserted = 0
    for _, row in df.iterrows():
        route_id = route_map.get(row['route'])
        if not route_id:
            continue
        
        cur.execute("""
            INSERT INTO route_metrics (time, route_id, delay_days, data_source)
            VALUES (%s, %s, %s, %s);
        """, (
            row['order_date'],
            route_id,
            float(row['delay_days']),
            'kaggle_dataco'
        ))
        inserted += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Inserted {inserted} metrics into TimescaleDB")

def main():
    df = load_kaggle_data()
    route_map = insert_routes(df)
    insert_metrics(df, route_map)
    print("\n🎉 Kaggle data loaded successfully!")

if __name__ == "__main__":
    main()