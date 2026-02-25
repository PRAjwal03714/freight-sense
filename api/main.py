"""
FastAPI Backend - Production Version
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
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
    description="ML-powered supply chain risk intelligence",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://freightsense.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://freightsense.*\.vercel\.app$",
)

# ============================================================================
# Startup Event - DO NOT load models at startup (memory constraints)
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting FreightSense API (Production Mode)...")
    logger.info("✅ API ready! (Models will lazy-load on first request)")
    logger.info(f"🌐 Serving {len(get_all_ports())} global ports")

# ============================================================================
# Request/Response Models
# ============================================================================

class RiskRequest(BaseModel):
    """Validated risk explanation request."""
    origin: str
    destination: str
    
    @validator('origin', 'destination')
    def validate_port(cls, v):
        if not validate_port(v):
            raise ValueError(f"Invalid port: {v}")
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
        "ports_available": len(get_all_ports())
    }

@app.get("/api/routes")
def get_routes():
    """Get all available ports."""
    ports = get_all_ports()
    
    return {
        "origins": ports,
        "destinations": ports,
        "total": len(ports),
        "note": "All ports validated with coordinates for weather data"
    }

@app.get("/api/ports/{port_name}")
def get_port_details(port_name: str):
    """Get detailed information about a specific port."""
    info = get_port_info(port_name)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Port '{port_name}' not found"
        )
    
    return {"port": port_name, **info}

@app.post("/api/explain")
async def explain_risk(request: RiskRequest):
    """
    Generate comprehensive risk explanation.
    Models are loaded on first request (lazy loading).
    """
    logger.info("POST /api/explain")
    logger.info(f"📊 Risk request: {request.origin} → {request.destination}")
    
    try:
        # Create explainer on each request (lightweight due to lazy loading)
        explainer = RiskExplainer()
        
        # Generate explanation
        explanation = explainer.explain_risk(
            origin_port=request.origin,
            dest_port=request.destination
        )
        
        logger.info(f"✅ Risk score: {explanation['risk_score']}/100")
        logger.info("Status: 200")
        return explanation
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        logger.info("Status: 500")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health")
def health_check():
    """Simple health check."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

# ============================================================================
# Request Logging
# ============================================================================

@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response