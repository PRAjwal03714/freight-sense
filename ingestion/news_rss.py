"""
RSS Feed News Fetcher - Production Alternative to NewsAPI

Fetches from industry-specific supply chain news sources.
Better coverage, no rate limits, FREE.
"""

import feedparser
from datetime import datetime, timezone
from typing import List, Dict
import time

# Industry-specific RSS feeds
RSS_FEEDS = {
    'Supply Chain Dive': 'https://www.supplychaindive.com/feeds/news/',
    'JOC Maritime': 'https://www.joc.com/rss/maritime-news',
    'FreightWaves': 'https://www.freightwaves.com/feed',
    'Maritime Executive': 'https://www.maritime-executive.com/rss.xml',
    'gCaptain': 'https://gcaptain.com/feed/',
    'Logistics Management': 'https://www.logisticsmgmt.com/rss/topic/258',
}

def fetch_supply_chain_news_rss(max_articles: int = 50) -> List[Dict]:
    """
    Fetch recent supply chain news from RSS feeds.
    
    Args:
        max_articles: Maximum articles to fetch (default 50)
    
    Returns:
        List of article dictionaries with headline, source, published_at
    """
    articles = []
    seen_headlines = set()
    
    print("=" * 70)
    print("FETCHING NEWS FROM RSS FEEDS")
    print("=" * 70)
    
    for source_name, feed_url in RSS_FEEDS.items():
        try:
            print(f"\n📡 Fetching from {source_name}...")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:  # Feed parsing error
                print(f"  ⚠️  Warning: Feed may have issues")
            
            for entry in feed.entries[:10]:  # Get top 10 from each source
                headline = entry.title.strip()
                
                # Deduplicate
                if headline in seen_headlines:
                    continue
                seen_headlines.add(headline)
                
                # Parse date
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if published:
                    pub_date = datetime(*published[:6], tzinfo=timezone.utc)
                else:
                    pub_date = datetime.now(timezone.utc)
                
                articles.append({
                    'headline': headline,
                    'source': source_name,
                    'published_at': pub_date.isoformat(),
                    'url': entry.get('link', '')
                })
                
            print(f"  ✅ Found {len([a for a in articles if a['source'] == source_name])} articles")
            
        except Exception as e:
            print(f"  ❌ Error fetching {source_name}: {str(e)[:50]}")
            continue
        
        # Be nice to servers
        time.sleep(0.5)
    
    # Sort by date (newest first)
    articles.sort(key=lambda x: x['published_at'], reverse=True)
    
    print(f"\n✅ Total unique articles: {len(articles)}")
    return articles[:max_articles]


if __name__ == "__main__":
    # Test the fetcher
    articles = fetch_supply_chain_news_rss(max_articles=20)
    
    print("\n" + "=" * 70)
    print("SAMPLE HEADLINES")
    print("=" * 70)
    
    for i, article in enumerate(articles[:10], 1):
        print(f"\n{i}. {article['headline']}")
        print(f"   Source: {article['source']}")
        print(f"   Date: {article['published_at'][:10]}")