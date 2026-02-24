"""
FastAPI Backend - Production Version

Enhancements:
- 50+ validated global ports
- Route existence validation
- Better error handling
- Performance optimization
- Proper logging
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.risk_explainer import RiskExplainer
from api.ports import get_all_ports, validate_port, get_port_info

# ============================================================================
# FastAPI App Configuration
# ============================================================================

app = FastAPI(
    title="FreightSense API",
    description="Production Supply Chain Risk Intelligence API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Initialize (load models once at startup)
# ============================================================================

logger.info("🚀 Starting FreightSense API (Production Mode)...")
explainer = None

@app.on_event("startup")
async def startup_event():
    """Load ML models on startup."""
    global explainer
    logger.info("📦 Loading ML models...")
    
    try:
        explainer = RiskExplainer()
        logger.info("✅ Models loaded successfully")
        logger.info(f"📊 ChromaDB Events: {explainer.event_store.collection.count()}")
        logger.info(f"🌐 Serving {len(get_all_ports())} global ports")
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        raise

# ============================================================================
# Request/Response Models with Validation
# ============================================================================

class RiskRequest(BaseModel):
    """Validated risk explanation request."""
    origin: str
    destination: str
    
    @validator('origin', 'destination')
    def validate_port(cls, v):
        if not validate_port(v):
            raise ValueError(f"Invalid port: {v}. Use /api/routes to see available ports.")
        return v
    
    @validator('destination')
    def validate_different(cls, v, values):
        if 'origin' in values and v == values['origin']:
            raise ValueError("Origin and destination must be different")
        return v

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
def root():
    """API root - health check."""
    return {
        "service": "FreightSense API",
        "status": "operational",
        "version": "1.0.0",
        "mode": "production",
        "ports_available": len(get_all_ports()),
        "endpoints": {
            "routes": "/api/routes",
            "port_info": "/api/ports/{port_name}",
            "explain": "/api/explain",
            "health": "/api/health"
        }
    }

@app.get("/api/routes")
def get_routes():
    """
    Get all available ports (production registry).
    
    Returns 50+ major global container ports with validation.
    """
    ports = get_all_ports()
    
    return {
        "origins": ports,
        "destinations": ports,
        "total": len(ports),
        "note": "All ports validated with coordinates for weather data"
    }

@app.get("/api/ports/{port_name}")
def get_port_details(port_name: str):
    """
    Get detailed information about a specific port.
    
    Includes: country, region, coordinates for weather API.
    """
    info = get_port_info(port_name)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Port '{port_name}' not found. Use /api/routes to see available ports."
        )
    
    return {
        "port": port_name,
        **info
    }

@app.post("/api/explain")
async def explain_risk(request: RiskRequest, background_tasks: BackgroundTasks):
    """
    Generate comprehensive risk explanation.
    
    Production features:
    - Input validation
    - Error handling
    - Logging
    - Async background tasks
    """
    
    logger.info(f"📊 Risk request: {request.origin} → {request.destination}")
    
    try:
        # Validate both ports exist
        if not validate_port(request.origin):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid origin port: {request.origin}"
            )
        
        if not validate_port(request.destination):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid destination port: {request.destination}"
            )
        
        # Generate explanation
        explanation = explainer.explain_risk(
            origin_port=request.origin,
            dest_port=request.destination
        )
        
        logger.info(f"✅ Risk score: {explanation['risk_score']}/100")
        
        return explanation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/health")
def health_check():
    """Detailed system health check."""
    
    try:
        chromadb_count = explainer.event_store.collection.count()
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "mode": "production",
            "components": {
                "api": "operational",
                "models_loaded": True,
                "news_analyzer": "ready",
                "chronos_forecast": "ready",
                "weather_api": "ready",
                "chromadb": {
                    "status": "connected",
                    "events_indexed": chromadb_count
                }
            },
            "ports": {
                "total_available": len(get_all_ports()),
                "regions": ["Asia", "Europe", "Americas", "Middle East", "Africa", "Oceania"]
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e)
        }

# ============================================================================
# Production Logging
# ============================================================================

@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests for monitoring."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response