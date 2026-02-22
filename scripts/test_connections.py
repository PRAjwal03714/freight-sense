"""
Run this to verify all your connections work before Week 2.
Think of this as your system health check.
"""
import sys
sys.path.append(".")

def test_database():
    print("\n--- Testing TimescaleDB ---")
    from scripts.setup_db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"✅ Connected: {version[:50]}...")
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    tables = [row[0] for row in cur.fetchall()]
    print(f"✅ Tables: {tables}")
    conn.close()

def test_redis():
    print("\n--- Testing Redis ---")
    import redis, os
    from dotenv import load_dotenv
    load_dotenv()
    r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379)
    r.set("freightsense_test", "ok")
    val = r.get("freightsense_test")
    print(f"✅ Redis working: {val}")

def test_weather_api():
    print("\n--- Testing Weather API ---")
    try:
        from ingestion.weather import fetch_weather
        result = fetch_weather("Singapore")
        print(f"✅ Weather API working: {result}")
    except Exception as e:
        print(f"⚠️  Weather API skipped (will use mock data): {str(e)[:60]}")

def test_news_api():
    print("\n--- Testing News API ---")
    from ingestion.news import fetch_supply_chain_news
    articles = fetch_supply_chain_news(days_back=1)
    print(f"✅ News API working: {len(articles)} articles fetched")

if __name__ == "__main__":
    test_database()
    test_redis()
    test_weather_api()
    test_news_api()
    print("\n🚀 Core systems operational! Ready for Day 2.")