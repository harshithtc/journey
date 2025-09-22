import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_plan_trip_validation_error():
    """Test with invalid date range"""
    tomorrow = date.today() + timedelta(days=1)
    today = date.today()
    
    response = client.post("/plan_trip", json={
        "city": "Paris",
        "start_date": str(tomorrow),  # start after end
        "end_date": str(today)
    })
    assert response.status_code == 422

def test_plan_trip_too_long():
    """Test with trip longer than 30 days"""
    start_date = date.today()
    end_date = start_date + timedelta(days=31)
    
    response = client.post("/plan_trip", json={
        "city": "Tokyo",
        "start_date": str(start_date),
        "end_date": str(end_date)
    })
    assert response.status_code == 422

def test_plan_trip_fallback():
    """Test fallback itinerary (when AI fails)"""
    start_date = date.today()
    end_date = start_date + timedelta(days=2)
    
    response = client.post("/plan_trip", json={
        "city": "London",
        "start_date": str(start_date),
        "end_date": str(end_date)
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "London"
    assert data["start_date"] == str(start_date)
    assert data["end_date"] == str(end_date)
    assert len(data["days"]) == 3  # 3 days total
    assert all("day" in day and "activities" in day for day in data["days"])
