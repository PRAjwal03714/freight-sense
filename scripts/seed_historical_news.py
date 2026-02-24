"""
Seed Database with Historical Supply Chain Events

This gives you diverse news data to test with.
"""

import sys
sys.path.append(".")

import psycopg2
import os
from datetime import datetime, timedelta
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

# Historical supply chain events (real events)
HISTORICAL_EVENTS = [
    {
        'headline': 'Shanghai port COVID lockdown causes massive shipping delays',
        'source': 'Reuters',
        'category': 'Port Congestion',
        'risk': 0.95,
        'locations': ['Shanghai', 'China'],
        'days_ago': 10
    },
    {
        'headline': 'Red Sea shipping attacks disrupt Middle East trade routes',
        'source': 'BBC',
        'category': 'Geopolitical Conflict',
        'risk': 0.92,
        'locations': ['Red Sea', 'Jeddah', 'Dubai'],
        'days_ago': 5
    },
    {
        'headline': 'Los Angeles port strike threatens West Coast supply chains',
        'source': 'CNBC',
        'category': 'Labor Strike',
        'risk': 0.88,
        'locations': ['Los Angeles', 'Long Beach'],
        'days_ago': 7
    },
    {
        'headline': 'Singapore port experiences record container volume surge',
        'source': 'Bloomberg',
        'category': 'Demand Surge',
        'risk': 0.65,
        'locations': ['Singapore'],
        'days_ago': 3
    },
    {
        'headline': 'Rotterdam port operations disrupted by severe weather',
        'source': 'Reuters',
        'category': 'Weather Event',
        'risk': 0.78,
        'locations': ['Rotterdam', 'Netherlands'],
        'days_ago': 8
    },
    {
        'headline': 'Mumbai port capacity expansion reduces congestion',
        'source': 'Economic Times',
        'category': 'Infrastructure',
        'risk': 0.35,
        'locations': ['Mumbai', 'India'],
        'days_ago': 4
    },
    {
        'headline': 'Typhoon disrupts Hong Kong and Shenzhen port operations',
        'source': 'South China Morning Post',
        'category': 'Weather Event',
        'risk': 0.90,
        'locations': ['Hong Kong', 'Shenzhen'],
        'days_ago': 6
    },
    {
        'headline': 'New York port automation improves efficiency',
        'source': 'Wall Street Journal',
        'category': 'Infrastructure',
        'risk': 0.25,
        'locations': ['New York', 'USA'],
        'days_ago': 12
    },
]

def seed_database():
    """Insert historical events into database."""
    
    conn = get_connection()
    cur = conn.cursor()
    
    print("=" * 70)
    print("SEEDING DATABASE WITH HISTORICAL EVENTS")
    print("=" * 70)
    
    inserted = 0
    
    for event in HISTORICAL_EVENTS:
        event_date = datetime.now() - timedelta(days=event['days_ago'])
        
        try:
            cur.execute("""
                INSERT INTO news_events (
                    time, headline, source, 
                    affected_routes, risk_category, 
                    sentiment_score
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                event_date,
                event['headline'],
                event['source'],
                event['locations'],
                event['category'],
                event['risk']
            ))
            
            inserted += cur.rowcount
            print(f"✅ {event['headline'][:60]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n✅ Inserted {inserted} historical events")
    print("\nNow run: python models/historical_matcher.py")
    print("This will index them in ChromaDB for similarity search\n")

if __name__ == "__main__":
    seed_database()