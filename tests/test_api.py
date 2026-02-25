"""
Basic API Tests - Portfolio Project

Shows understanding of testing principles without over-engineering.
"""
"""
Basic API Tests - Portfolio Project
"""

import sys
import os

# Add parent directory to path so pytest can find api module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app

import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root_endpoint():
    """Test API health check."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "FreightSense API"

def test_routes_endpoint():
    """Test route listing returns valid ports."""
    response = client.get("/api/routes")
    assert response.status_code == 200
    data = response.json()
    assert "origins" in data
    assert len(data["origins"]) > 0

def test_risk_endpoint_valid_route():
    """Test risk calculation for valid route."""
    response = client.post("/api/explain", json={
        "origin": "Shanghai",
        "destination": "Los Angeles"
    })
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert 0 <= data["risk_score"] <= 100
    assert "confidence" in data

def test_risk_endpoint_same_ports():
    """Test validation rejects same origin/destination."""
    response = client.post("/api/explain", json={
        "origin": "Shanghai",
        "destination": "Shanghai"
    })
    assert response.status_code == 422  # Validation error

def test_risk_endpoint_invalid_port():
    """Test validation rejects invalid ports."""
    response = client.post("/api/explain", json={
        "origin": "FakePort",
        "destination": "Los Angeles"
    })
    assert response.status_code == 422