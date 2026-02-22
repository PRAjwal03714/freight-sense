import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Keywords that signal supply chain disruption risk
SUPPLY_CHAIN_KEYWORDS = [
    "port congestion", "shipping delay", "supply chain disruption",
    "freight rates", "container shortage", "vessel stuck",
    "trade route", "cargo delay", "logistics disruption",
    "suez canal", "panama canal", "strait of malacca"
]

def fetch_supply_chain_news(days_back: int = 1) -> list[dict]:
    """
    Fetches recent news headlines related to supply chain disruptions.
    These headlines feed directly into our DistilBERT NLP pipeline later.
    """
    api_key = os.getenv("NEWS_API_KEY")
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    query = " OR ".join(f'"{kw}"' for kw in SUPPLY_CHAIN_KEYWORDS[:4])

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 50,
        "apiKey": api_key
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    articles = []
    for article in data.get("articles", []):
        articles.append({
            "headline": article["title"],
            "source": article["source"]["name"],
            "published_at": article["publishedAt"],
            "url": article["url"],
            "description": article.get("description", "")
        })

    print(f"✅ Fetched {len(articles)} supply chain news articles")
    return articles

if __name__ == "__main__":
    news = fetch_supply_chain_news(days_back=2)
    for n in news[:5]:
        print(f"[{n['source']}] {n['headline']}")