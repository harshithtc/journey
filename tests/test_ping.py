import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ping_success():
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "journey-backend"
