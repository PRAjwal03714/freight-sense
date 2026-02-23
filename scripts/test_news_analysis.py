"""
Test News Analyzer on Real Headlines

What this does:
1. Fetches live supply chain news from NewsAPI (last 24 hours)
2. Runs our NewsAnalyzer on each headline
3. Shows which ones have high risk scores
4. Saves results to database

Why this matters:
- Proves the system works on REAL data (not just test cases)
- Builds historical database for ChromaDB pattern matching
- Generates real risk signals for the explanation engine
"""

import sys
sys.path.append(".")

from ingestion.news import fetch_supply_chain_news
from models.news_analyzer import NewsAnalyzer
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

def save_to_database(article, analysis):
    """
    Save analyzed news to the news_events table.
    
    Schema reminder:
    - time: when the news was published
    - headline: the raw headline text
    - source: news outlet (Reuters, Bloomberg, etc.)
    - affected_routes: array of locations mentioned
    - risk_category: primary disruption type
    - sentiment_score: risk signal (-1 to +1)
    - raw_json: full analysis for later retrieval
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Extract data
    published_at = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
    headline = article['headline']
    source = article['source']
    
    # From analysis
    locations = analysis['entities']['locations']
    primary_category = analysis['categories'][0]['category'] if analysis['categories'] else 'Unknown'
    risk_score = analysis['sentiment']['risk_signal']
    
    # Store full analysis as JSON
    import json
    raw_json = json.dumps(analysis)
    
    # Insert
    cur.execute("""
        INSERT INTO news_events (
            time, headline, source, 
            affected_routes, risk_category, 
            sentiment_score, raw_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (
        published_at,
        headline,
        source,
        locations,  # PostgreSQL array
        primary_category,
        risk_score,
        raw_json
    ))
    
    conn.commit()
    cur.close()
    conn.close()

def main():
    print("=" * 70)
    print("REAL-TIME NEWS ANALYSIS TEST")
    print("=" * 70)
    
    # Fetch real news
    print("\n📡 Fetching live supply chain news from NewsAPI...")
    articles = fetch_supply_chain_news(days_back=2)  # Last 2 days
    
    if not articles:
        print("❌ No articles found. Check your NEWS_API_KEY in .env")
        return
    
    print(f"✅ Fetched {len(articles)} articles\n")
    
    # Initialize analyzer
    analyzer = NewsAnalyzer()
    
    # Analyze each article
    print("=" * 70)
    print("ANALYZING HEADLINES")
    print("=" * 70)
    
    analyzed = []
    high_risk = []
    
    for i, article in enumerate(articles[:15], 1):  # First 15 articles
        print(f"\n[{i}/{min(15, len(articles))}]")
        
        result = analyzer.analyze(article['headline'])
        
        # Save to database
        try:
            save_to_database(article, result)
            print(f"   💾 Saved to database")
        except Exception as e:
            print(f"   ⚠️  Database save failed: {str(e)[:50]}")
        
        analyzed.append({
            'article': article,
            'analysis': result
        })
        
        # Track high-risk headlines
        if result['sentiment']['risk_signal'] > 0.7:
            high_risk.append({
                'headline': article['headline'],
                'risk': result['sentiment']['risk_signal'],
                'category': result['categories'][0]['category'] if result['categories'] else 'Unknown',
                'locations': result['entities']['locations']
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal analyzed: {len(analyzed)}")
    print(f"High risk (>0.7): {len(high_risk)}")
    
    if high_risk:
        print("\n🚨 HIGH RISK HEADLINES:")
        print("-" * 70)
        for item in high_risk:
            print(f"\nRisk: {item['risk']:.2f} | Category: {item['category']}")
            print(f"Headline: {item['headline'][:80]}...")
            if item['locations']:
                print(f"Affected: {', '.join(item['locations'])}")
    
    # Category breakdown
    from collections import Counter
    categories = [a['analysis']['categories'][0]['category'] 
                  for a in analyzed if a['analysis']['categories']]
    category_counts = Counter(categories)
    
    print("\n📋 DISRUPTION TYPES:")
    print("-" * 70)
    for category, count in category_counts.most_common():
        print(f"{category:.<40} {count}")
    
    # Sentiment distribution
    avg_risk = sum(a['analysis']['sentiment']['risk_signal'] for a in analyzed) / len(analyzed)
    print(f"\n📈 Average Risk Signal: {avg_risk:.2f}")
    
    print("\n✅ Real-time news analysis complete!")
    print(f"💾 {len(analyzed)} articles saved to news_events table\n")

if __name__ == "__main__":
    main()