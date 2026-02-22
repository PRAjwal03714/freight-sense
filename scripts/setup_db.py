import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("TIMESCALE_HOST", "localhost"),
        port=os.getenv("TIMESCALE_PORT", 5432),
        dbname=os.getenv("TIMESCALE_DB", "freightsense"),
        user=os.getenv("TIMESCALE_USER", "postgres"),
        password=os.getenv("TIMESCALE_PASSWORD", "postgres")
    )

def setup_schema():
    conn = get_connection()
    cur = conn.cursor()

    # Enable TimescaleDB extension
    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # Static route metadata
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

    # Time-series delay metrics (this becomes a hypertable)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS route_metrics (
            time            TIMESTAMPTZ NOT NULL,
            route_id        INT REFERENCES routes(route_id),
            delay_days      FLOAT,
            congestion_score FLOAT,
            weather_severity FLOAT,
            risk_score      FLOAT,
            data_source     TEXT
        );
    """)

    # Convert to TimescaleDB hypertable (the key step)
    cur.execute("""
        SELECT create_hypertable('route_metrics', 'time',
               if_not_exists => TRUE);
    """)

    # News events for NLP pipeline
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news_events (
            event_id        SERIAL PRIMARY KEY,
            time            TIMESTAMPTZ NOT NULL,
            headline        TEXT NOT NULL,
            source          TEXT,
            affected_routes TEXT[],
            risk_category   TEXT,
            sentiment_score FLOAT,
            raw_json        JSONB
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Schema created successfully!")

if __name__ == "__main__":
    setup_schema()