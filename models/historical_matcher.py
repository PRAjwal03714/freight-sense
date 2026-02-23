"""
Historical Pattern Matching with ChromaDB

What this does:
1. Stores analyzed news events as vector embeddings
2. Finds similar past events when new disruptions occur
3. Powers the "Similar Historical Events" section of risk explanations

Why ChromaDB:
- Semantic search (finds meaning, not just keywords)
- Fast vector similarity search
- Persists data locally (no cloud dependency)

HuggingFace Tasks Used:
- Task #5: Sentence Similarity (all-MiniLM-L6-v2)

How it works:
- "Red Sea attacks" → [0.23, -0.45, ..., 0.12] (384D vector)
- ChromaDB finds closest vectors → similar past events
- Even if words are different, meaning is captured
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import json
from datetime import datetime

class HistoricalEventStore:
    """
    Vector database for supply chain disruption events.
    
    Architecture:
    - ChromaDB: Stores vectors + metadata
    - SentenceTransformer: Converts text → vectors
    - Persistent storage: Data saved between runs
    """
    
    def __init__(self, persist_directory="data/chromadb"):
        """
        Initialize ChromaDB and embedding model.
        
        First run: Creates new database
        Future runs: Loads existing database
        """
        print("🔧 Initializing Historical Event Store...")
        
        # Create ChromaDB client with persistence
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Create or load collection
        try:
            self.collection = self.client.get_collection("supply_chain_events")
            print(f"   ✅ Loaded existing collection ({self.collection.count()} events)")
        except:
            self.collection = self.client.create_collection(
                name="supply_chain_events",
                metadata={"description": "Supply chain disruption events with embeddings"}
            )
            print("   ✅ Created new collection")
        
        # Load sentence transformer for embeddings
        print("   Loading sentence transformer model...")
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("   ✅ Embedder ready (384-dimensional vectors)\n")
    
    def add_event(self, 
                  headline: str,
                  event_date: datetime,
                  category: str,
                  risk_score: float,
                  locations: List[str],
                  source: str,
                  full_analysis: Dict = None):
        """
        Add a disruption event to the vector database.
        
        Args:
            headline: News headline text
            event_date: When it happened
            category: Weather, Geopolitical, etc.
            risk_score: Disruption severity (0-1)
            locations: Affected ports/regions
            source: News outlet
            full_analysis: Complete NewsAnalyzer output
        
        What happens:
        1. Convert headline to 384D vector
        2. Store vector + metadata in ChromaDB
        3. Persisted to disk automatically
        """
        
        # Generate embedding
        embedding = self.embedder.encode(headline).tolist()
        
        # Prepare metadata
        metadata = {
            "date": event_date.isoformat(),
            "category": category,
            "risk_score": risk_score,
            "locations": json.dumps(locations),  # Store as JSON string
            "source": source,
            "year": event_date.year,
            "month": event_date.month
        }
        
        # Store full analysis if provided
        if full_analysis:
            metadata["full_analysis"] = json.dumps(full_analysis)
        
        # Generate unique ID
        event_id = f"{event_date.isoformat()}_{hash(headline) % 10000}"
        
        # Add to ChromaDB
        self.collection.add(
            ids=[event_id],
            embeddings=[embedding],
            documents=[headline],
            metadatas=[metadata]
        )
    
    def find_similar_events(self, 
                           query_headline: str,
                           n_results: int = 5,
                           min_similarity: float = 0.5) -> List[Dict]:
        """
        Find historical events similar to a new headline.
        
        Args:
            query_headline: New event to match
            n_results: How many similar events to return
            min_similarity: Threshold (0-1, higher = more similar)
        
        Returns:
            List of similar events with similarity scores
            
        Example:
        >>> store.find_similar_events("Red Sea shipping attacked", n_results=3)
        [
            {
                "headline": "U.S.-Iran tensions threaten tankers",
                "similarity": 0.87,
                "date": "2026-02-20",
                "category": "Geopolitical Conflict",
                "risk_score": 0.99,
                "locations": ["Iran", "U.S."]
            },
            ...
        ]
        """
        
        if self.collection.count() == 0:
            return []
        
        # Convert query to embedding
        query_embedding = self.embedder.encode(query_headline).tolist()
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        similar_events = []
        
        for i in range(len(results['ids'][0])):
            # ChromaDB returns distances, convert to similarity
            # Distance 0 = identical, distance 2 = opposite
            # Similarity = 1 - (distance / 2)
            distance = results['distances'][0][i]
            similarity = 1 - (distance / 2)
            
            # Filter by minimum similarity
            if similarity < min_similarity:
                continue
            
            metadata = results['metadatas'][0][i]
            
            event = {
                "headline": results['documents'][0][i],
                "similarity": round(similarity, 3),
                "date": metadata['date'],
                "category": metadata['category'],
                "risk_score": metadata['risk_score'],
                "locations": json.loads(metadata['locations']),
                "source": metadata['source']
            }
            
            # Include full analysis if available
            if 'full_analysis' in metadata:
                event['full_analysis'] = json.loads(metadata['full_analysis'])
            
            similar_events.append(event)
        
        return similar_events
    
    def get_events_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Get all events of a specific category."""
        results = self.collection.get(
            where={"category": category},
            limit=limit
        )
        
        events = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            events.append({
                "headline": results['documents'][i],
                "date": metadata['date'],
                "category": metadata['category'],
                "risk_score": metadata['risk_score'],
                "locations": json.loads(metadata['locations'])
            })
        
        return events
    
    def get_statistics(self) -> Dict:
        """Get summary statistics about stored events."""
        total = self.collection.count()
        
        if total == 0:
            return {"total": 0}
        
        # Get all metadata
        all_data = self.collection.get()
        
        # Category breakdown
        from collections import Counter
        categories = [m['category'] for m in all_data['metadatas']]
        category_counts = Counter(categories)
        
        # Average risk by category
        category_risks = {}
        for cat in category_counts.keys():
            risks = [m['risk_score'] for m in all_data['metadatas'] if m['category'] == cat]
            category_risks[cat] = round(sum(risks) / len(risks), 3) if risks else 0
        
        return {
            "total": total,
            "categories": dict(category_counts),
            "avg_risk_by_category": category_risks
        }


def main():
    """Demo: Load recent news from database and build ChromaDB index."""
    
    print("=" * 70)
    print("HISTORICAL EVENT STORE - DEMO")
    print("=" * 70)
    
    # Initialize store
    store = HistoricalEventStore()
    
    # Load recent news from TimescaleDB
    print("\n📥 Loading recent news events from database...")
    
    import psycopg2
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    conn = psycopg2.connect(
        host=os.getenv("TIMESCALE_HOST", "localhost"),
        port=os.getenv("TIMESCALE_PORT", 5434),
        dbname=os.getenv("TIMESCALE_DB", "freightsense"),
        user=os.getenv("TIMESCALE_USER", "postgres"),
        password=os.getenv("TIMESCALE_PASSWORD", "postgres")
    )
    
    cur = conn.cursor()
    cur.execute("""
        SELECT time, headline, source, risk_category, 
               sentiment_score, affected_routes, raw_json
        FROM news_events
        ORDER BY time DESC
        LIMIT 50;
    """)
    
    events = cur.fetchall()
    cur.close()
    conn.close()
    
    print(f"✅ Loaded {len(events)} events from database\n")
    
    # Add to ChromaDB
    print("📥 Adding events to ChromaDB...")
    
    for event in events:
        time, headline, source, category, risk_score, locations, raw_json = event
        
        store.add_event(
            headline=headline,
            event_date=time,
            category=category if category else "Unknown",
            risk_score=float(risk_score) if risk_score else 0.5,
            locations=locations if locations else [],
            source=source,
            full_analysis=raw_json if raw_json else None        )
    
    print(f"✅ Added {len(events)} events to vector database\n")
    
    # Test similarity search
    print("=" * 70)
    print("🔍 SIMILARITY SEARCH TEST")
    print("=" * 70)
    
    test_queries = [
        "Middle East shipping disruptions",
        "Port congestion in Asia",
        "Weather delays at major ports"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 70)
        
        similar = store.find_similar_events(query, n_results=3)
        
        if not similar:
            print("   No similar events found")
            continue
        
        for i, event in enumerate(similar, 1):
            print(f"\n{i}. Similarity: {event['similarity']:.2%} | Risk: {event['risk_score']:.2f}")
            print(f"   {event['headline'][:80]}...")
            print(f"   Category: {event['category']} | Date: {event['date'][:10]}")
            if event['locations']:
                print(f"   Locations: {', '.join(event['locations'][:3])}")
    
    # Statistics
    print("\n" + "=" * 70)
    print("📊 DATABASE STATISTICS")
    print("=" * 70)
    
    stats = store.get_statistics()
    print(f"\nTotal events: {stats['total']}")
    
    if 'categories' in stats:
        print("\nEvents by category:")
        for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
            avg_risk = stats['avg_risk_by_category'].get(cat, 0)
            print(f"  {cat:.<35} {count:>3} (avg risk: {avg_risk:.2f})")
    
    print("\n✅ Historical Event Store demo complete!\n")

    # Test similarity search
    print("=" * 70)
    print("🔍 SIMILARITY SEARCH TEST")
    print("=" * 70)
    
    # First, show what we have
    print("\n📋 Events in database:")
    all_events = store.collection.get()
    for i, headline in enumerate(all_events['documents'][:5], 1):
        print(f"{i}. {headline}")
    
    # Test with queries similar to what we actually have
    test_queries = [
        "Iran tensions affecting oil shipping",  # Similar to our geopolitical news
        "U.S. conflict with Middle East",        # Also similar
        "Manufacturing demand increasing",        # Similar to demand surge
    ]
    
    print("\n" + "=" * 70)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 70)
        
        # Lower the similarity threshold to 0.3 to see more results
        similar = store.find_similar_events(query, n_results=3, min_similarity=0.3)
        
        if not similar:
            print("   No similar events found (threshold: 0.3)")
            continue
        
        for i, event in enumerate(similar, 1):
            print(f"\n{i}. Similarity: {event['similarity']:.2%} | Risk: {event['risk_score']:.2f}")
            print(f"   {event['headline'][:80]}...")
            print(f"   Category: {event['category']} | Date: {event['date'][:10]}")
            if event['locations']:
                print(f"   Locations: {', '.join(event['locations'][:3])}")


if __name__ == "__main__":
    main()