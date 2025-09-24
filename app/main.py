import os
import json
import time
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import APP_NAME, DATABASE_URL
from app.db.session import Base, engine
from app.routers import tours

from app.models.chat_models import ChatRequest
from app.models.itinerary_models import PlanTripRequest, DayPlan, ItineraryResponse
from app.services.perplexity_service import safe_perplexity_call, safe_itinerary_call
from app.services.logging_config import setup_logging

from pydantic import BaseModel
from typing import Optional

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logger = setup_logging()

# ------------------------------------------------------------------------------
# Rate limiting
# ------------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ------------------------------------------------------------------------------
# Lifespan
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_: FastAPI):
    if not DATABASE_URL:
        logger.error("DATABASE_URL is not set, cannot connect to DB")
        raise RuntimeError("DATABASE_URL must be set before starting the app")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured at startup")
    except Exception as e:
        logger.error("Failed to create tables at startup", extra={"error": str(e)})
    yield

# ------------------------------------------------------------------------------
# App creation
# ------------------------------------------------------------------------------
app = FastAPI(title=APP_NAME, version="1.0.0", lifespan=lifespan)

# SlowAPI integration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing app routers
app.include_router(tours, tags=["Tours"])

# ------------------------------------------------------------------------------
# Request logging middleware
# ------------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(
        "Incoming request",
        extra={"method": request.method, "url": str(request.url), "client_ip": request.client.host},
    )
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
        },
    )
    return response

# ------------------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------------------
@app.get("/ping")
async def ping():
    logger.info("Health check requested")
    return {"status": "ok", "service": "journey-backend"}

# ------------------------------------------------------------------------------
# Conversational chat state and questions
# ------------------------------------------------------------------------------
chat_state = {}

CONVERSATION_QUESTIONS = [
    ("day", "Which day are you planning your tour?"),
    ("location", "Which city/country/region do you want to visit?"),
    ("date", "What are your preferred travel dates?"),
    ("travel_style", "Are you looking for luxury, mid-range, or budget travel?"),
    ("budget", "Approximate budget per person (including accommodation, food, transport, activities)?"),
    ("accommodation", "Do you prefer hotels, hostels, resorts, or homestays?"),
    ("activities", "What kind of experiences are you interested in? (nature, adventure, cultural experiences, shopping, nightlife)"),
    ("transportation", "How do you prefer to travel locally? (rental car, public transport, walking, bike)"),
    ("dining", "Do you have any dietary restrictions or food interests?"),
    ("special_requests", "Any special requests, accessibility needs, or events you want included?")
]

class ChatInput(BaseModel):
    user_id: Optional[str] = "default_user"  # In production: get from actual session or auth
    day: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    travel_style: Optional[str] = None
    budget: Optional[str] = None
    accommodation: Optional[str] = None
    activities: Optional[str] = None
    transportation: Optional[str] = None
    dining: Optional[str] = None
    special_requests: Optional[str] = None
    query: Optional[str] = None

@app.post("/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, chat_input: ChatInput):
    user_id = chat_input.user_id or "default_user"
    if user_id not in chat_state:
        chat_state[user_id] = {}

    state = chat_state[user_id]

    # Update conversation state with any new info from client
    for key, _ in CONVERSATION_QUESTIONS:
        val = getattr(chat_input, key, None)
        if val is not None:
            state[key] = val

    # Ask the next unanswered question
    for key, question in CONVERSATION_QUESTIONS:
        if key not in state:
            return {"response": question}

    # All questions answered: create prompt and call Perplexity API
    prompt = f"""
You are a professional travel planner AI. Based on these user preferences, create a detailed day-wise itinerary:
{json.dumps(state, indent=2)}
Return just the JSON formatted itinerary without extra text.
"""

    try:
        ai_response = await safe_perplexity_call(prompt)
    except Exception as e:
        logger.error("Perplexity API call failed", exc_info=e)
        ai_response = "Sorry, I couldn't generate the itinerary at this time."

    # Clear conversation state
    chat_state.pop(user_id, None)

    return {"response": ai_response}

# ------------------------------------------------------------------------------
# Legacy chat endpoint using external AI call (kept for backward compatibility)
# ------------------------------------------------------------------------------
@app.post("/legacy_chat")
@limiter.limit("10/minute")
async def legacy_chat(request: Request, chat_request: ChatRequest):
    logger.info("Chat request received", extra={"query_length": len(chat_request.query or "")})
    q = (chat_request.query or "").strip()
    if q == "":
        logger.info("Empty query short-circuited")
        return {"reply": ""}
    try:
        reply = safe_perplexity_call(q)
        logger.info("Chat response generated successfully")
        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in chat endpoint", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")

# ------------------------------------------------------------------------------
# Your other existing endpoints like /plan_trip etc.
# ------------------------------------------------------------------------------
