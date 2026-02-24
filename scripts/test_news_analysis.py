"""Supply Chain News Analysis - RSS Version with Unique Timestamps"""

import sys
sys.path.append(".")

from ingestion.news_rss import fetch_supply_chain_news_rss
from models.news_analyzer import NewsAnalyzer
import psycopg2
import os
from datetime import datetime, timedelta  # ← Add timedelta
from dotenv import load_dotenv
import json  # ← Make sure this is imported

load_dotenv()

def get_connection():
    """Get database connection - prioritize DATABASE_URL for Render."""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        print(f"📡 Connecting to RENDER database...")
        return psycopg2.connect(database_url)
    else:
        print(f"📡 Connecting to LOCAL database...")
        return psycopg2.connect(
            host=os.getenv("TIMESCALE_HOST", "localhost"),
            port=int(os.getenv("TIMESCALE_PORT", 5434)),
            dbname=os.getenv("TIMESCALE_DB", "freightsense"),
            user=os.getenv("TIMESCALE_USER", "postgres"),
            password=os.getenv("TIMESCALE_PASSWORD", "postgres")
        )

def main():
    print("=" * 70)
    print("SUPPLY CHAIN NEWS ANALYSIS - RSS VERSION")
    print("=" * 70)
    
    articles = fetch_supply_chain_news_rss(max_articles=30)
    
    if not articles:
        print("❌ No articles fetched!")
        return
    
    print(f"\n✅ Fetched {len(articles)} supply chain news articles\n")
    
    analyzer = NewsAnalyzer()
    conn = get_connection()
    cur = conn.cursor()
    
    stored = 0
    timestamp_offset = 0  # ← ADD THIS
    
    for article in articles:
        headline = article['headline']
        
        print("=" * 70)
        print(f"📰 Analyzing: '{headline[:70]}...'")
        
        analysis = analyzer.analyze(headline)
        
        locations = analysis['entities']['locations']
        orgs = analysis['entities']['organizations']
        print(f"   Entities: {locations} (locations), {orgs} (orgs)")
        print(f"   Sentiment: {analysis['sentiment']['label']} (risk: {analysis['sentiment']['risk_signal']:.2f})")
        
        if analysis['categories']:
            cat = analysis['categories'][0]
            print(f"   Primary category: {cat['category']}")
        
        try:
            pub_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
            
            # ADD THIS: Make each timestamp unique
            pub_date = pub_date + timedelta(seconds=timestamp_offset)
            timestamp_offset += 1
            
            cur.execute("""
                INSERT INTO news_events (
                    time, headline, source, 
                    affected_routes, risk_category, 
                    sentiment_score, raw_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                pub_date,
                headline,
                article['source'],
                locations,
                analysis['categories'][0]['category'] if analysis['categories'] else 'Unknown',
                analysis['sentiment']['risk_signal'],
                json.dumps(analysis)
            ))
            
            if cur.rowcount > 0:
                stored += 1
                print(f"   ✅ Stored in database")
            
        except Exception as e:
            print(f"   ⚠️  Storage error: {e}")
            conn.rollback()
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print(f"✅ Stored {stored} new articles in database")
    print("=" * 70)

if __name__ == "__main__":
    main()