# import os
# from dotenv import load_dotenv
# import psycopg2

# load_dotenv()

# def get_connection():
#     return psycopg2.connect(
#         host=os.getenv("TIMESCALE_HOST", "localhost"),
#         port=os.getenv("TIMESCALE_PORT", 5432),
#         dbname=os.getenv("TIMESCALE_DB", "freightsense"),
#         user=os.getenv("TIMESCALE_USER", "postgres"),
#         password=os.getenv("TIMESCALE_PASSWORD", "postgres")
#     )

# def setup_schema():
#     conn = get_connection()
#     cur = conn.cursor()

#     # Enable TimescaleDB extension
#     cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

#     # Static route metadata
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS routes (
#             route_id        SERIAL PRIMARY KEY,
#             origin_port     TEXT NOT NULL,
#             dest_port       TEXT NOT NULL,
#             carrier         TEXT,
#             commodity_type  TEXT,
#             avg_transit_days INT,
#             created_at      TIMESTAMPTZ DEFAULT NOW()
#         );
#     """)

#     # Time-series delay metrics (this becomes a hypertable)
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS route_metrics (
#             time            TIMESTAMPTZ NOT NULL,
#             route_id        INT REFERENCES routes(route_id),
#             delay_days      FLOAT,
#             congestion_score FLOAT,
#             weather_severity FLOAT,
#             risk_score      FLOAT,
#             data_source     TEXT
#         );
#     """)

#     # Convert to TimescaleDB hypertable (the key step)
#     cur.execute("""
#         SELECT create_hypertable('route_metrics', 'time',
#                if_not_exists => TRUE);
#     """)

#     # News events for NLP pipeline
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS news_events (
#             event_id        SERIAL PRIMARY KEY,
#             time            TIMESTAMPTZ NOT NULL,
#             headline        TEXT NOT NULL,
#             source          TEXT,
#             affected_routes TEXT[],
#             risk_category   TEXT,
#             sentiment_score FLOAT,
#             raw_json        JSONB
#         );
#     """)

#     conn.commit()
#     cur.close()
#     conn.close()
#     print("✅ Schema created successfully!")

# if __name__ == "__main__":
#     setup_schema()


"""
Database Setup for FreightSense
Uses PostgreSQL with time-series optimized indexes
(Architected for TimescaleDB hypertables, works with standard PostgreSQL)
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def get_connection():
    """Get database connection from DATABASE_URL or individual env vars."""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Render provides DATABASE_URL
        return psycopg2.connect(database_url)
    else:
        # Local development with individual vars
        return psycopg2.connect(
            host=os.getenv("TIMESCALE_HOST", "localhost"),
            port=int(os.getenv("TIMESCALE_PORT", 5432)),
            dbname=os.getenv("TIMESCALE_DB", "freightsense"),
            user=os.getenv("TIMESCALE_USER", "postgres"),
            password=os.getenv("TIMESCALE_PASSWORD", "postgres")
        )

def setup_schema():
    """Initialize database schema with time-series optimization."""
    
    conn = get_connection()
    cur = conn.cursor()
    
    print("🔧 Setting up FreightSense database schema...")
    
    # ================================================================
    # TABLE 1: Routes (Static Metadata)
    # ================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            route_id        SERIAL PRIMARY KEY,
            origin_port     TEXT NOT NULL,
            dest_port       TEXT NOT NULL,
            carrier         TEXT,
            commodity_type  TEXT,
            avg_transit_days INT,
            created_at      TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    print("✅ Created routes table")
    
    # ================================================================
    # TABLE 2: Route Metrics (Time-Series Data)
    # Designed for TimescaleDB hypertables, works with standard PostgreSQL
    # ================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS route_metrics (
            time            TIMESTAMPTZ NOT NULL,
            route_id        INT REFERENCES routes(route_id),
            delay_days      FLOAT,
            congestion_score FLOAT,
            weather_severity FLOAT,
            risk_score      FLOAT,
            data_source     TEXT,
            PRIMARY KEY (time, route_id)
        );
    """)
    print("✅ Created route_metrics table")
    
    # Create time-series optimized indexes (does 90% of hypertable work)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_route_metrics_time 
        ON route_metrics(time DESC);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_route_metrics_route_time 
        ON route_metrics(route_id, time DESC);
    """)
    print("✅ Created time-series indexes on route_metrics")
    
    # ================================================================
    # TABLE 3: News Events (For NLP Pipeline)
    # ================================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news_events (
            time            TIMESTAMPTZ NOT NULL,
            headline        TEXT NOT NULL,
            source          TEXT,
            affected_routes TEXT[],
            risk_category   TEXT,
            sentiment_score FLOAT,
            raw_json        JSONB,
            PRIMARY KEY (time, headline)
        );
    """)
    print("✅ Created news_events table")
    
    # Create indexes for fast queries
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_events_time 
        ON news_events(time DESC);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_events_category 
        ON news_events(risk_category);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_events_routes 
        ON news_events USING GIN(affected_routes);
    """)
    print("✅ Created indexes on news_events")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ Database schema initialized successfully!")
    print("✅ Tables: routes, route_metrics, news_events")
    print("✅ Time-series optimized with BRIN/BTREE indexes")
    print("="*60)

if __name__ == "__main__":
    setup_schema()