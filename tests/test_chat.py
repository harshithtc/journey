# tests/test_chat.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_validation_error():
    """Missing required field"""
    response = client.post("/chat", json={})
    assert response.status_code == 422

def test_chat_empty_query():
    """Empty query should short-circuit and still return 200 with empty reply"""
    response = client.post("/chat", json={"query": ""})
    assert response.status_code == 200
    assert response.json()["reply"] == ""

@patch("app.main.safe_perplexity_call")
def test_chat_success(mock_api_call):
    mock_api_call.return_value = "Hello from mock AI"
    response = client.post("/chat", json={"query": "Hello"})
    assert response.status_code == 200
    assert response.json()["reply"] == "Hello from mock AI"
    mock_api_call.assert_called_once_with("Hello")

@patch("app.main.safe_perplexity_call")
def test_chat_api_failure(mock_api_call):
    from fastapi import HTTPException
    mock_api_call.side_effect = HTTPException(status_code=500, detail="API Error")
    response = client.post("/chat", json={"query": "Hello"})
    assert response.status_code == 500
