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

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logger = setup_logging()

# ------------------------------------------------------------------------------
# Rate limiting
# ------------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ------------------------------------------------------------------------------
# Lifespan: do one-time startup work (e.g., table creation for dev)
# Prefer Alembic for production migrations.
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
# App
# ------------------------------------------------------------------------------
app = FastAPI(title=APP_NAME, version="1.0.0", lifespan=lifespan)

# SlowAPI wiring
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers (additional feature modules) with explicit tags for documentation
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
# Health
# ------------------------------------------------------------------------------
@app.get("/ping")
async def ping():
    logger.info("Health check requested")
    return {"status": "ok", "service": "journey-backend"}

# ------------------------------------------------------------------------------
# Chat
# ------------------------------------------------------------------------------
@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, chat_request: ChatRequest):
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
# Trip planning
# ------------------------------------------------------------------------------
@app.post("/plan_trip", response_model=ItineraryResponse)
@limiter.limit("5/minute")
async def plan_trip(request: Request, req: PlanTripRequest) -> ItineraryResponse:
    logger.info(
        "Trip planning request received",
        extra={
            "city": req.city,
            "start_date": str(req.start_date),
            "end_date": str(req.end_date),
            "trip_days": (req.end_date - req.start_date).days + 1,
        },
    )

    system_msg = "You are a travel planner that responds strictly with valid JSON for the requested schema."
    user_prompt = f"""
    Generate a day-wise itinerary for city "{req.city}" from "{req.start_date}" to "{req.end_date}".
    Return strictly valid JSON only, matching exactly:
    {{
        "city": "{req.city}",
        "start_date": "{req.start_date}",
        "end_date": "{req.end_date}",
        "days": [
            {{
                "day": 1,
                "date": "{req.start_date}",
                "summary": "One-sentence highlight for the day",
                "activities": ["Short actionable activity 1", "Activity 2", "Activity 3"]
            }}
        ]
    }}
    No extra text before or after the JSON, no markdown, no code fences.
    """

    try:
        ai_response = safe_itinerary_call(system_msg, user_prompt)
        data = json.loads(ai_response)
        itinerary = ItineraryResponse.model_validate(data)
        logger.info("AI itinerary generated successfully")
        return itinerary

    except (json.JSONDecodeError, ValueError, HTTPException) as e:
        logger.warning("AI itinerary failed, using fallback", extra={"error": str(e)})

        total_days = (req.end_date - req.start_date).days + 1
        suggestions = [
            f"Explore iconic landmarks in {req.city}",
            "Sample local cuisine at a recommended spot",
            "Visit a museum, gallery, or cultural center",
            "Walk through scenic neighborhoods or parks",
        ]

        days: list[DayPlan] = []
        for i in range(total_days):
            day_date = req.start_date + timedelta(days=i)
            activities = suggestions[:3] if i % 2 == 0 else suggestions[1:]
            days.append(
                DayPlan(
                    day=i + 1,
                    date=day_date,
                    summary=f"Discover highlights of {req.city}",
                    activities=activities,
                )
            )

        fallback_itinerary = ItineraryResponse(
            city=req.city,
            start_date=req.start_date,
            end_date=req.end_date,
            days=days,
        )

        logger.info("Fallback itinerary generated")
        return fallback_itinerary

# ------------------------------------------------------------------------------
# Local entrypoint (Render uses its own start command)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=bool(os.getenv("RELOAD", "0") == "1"),
    )
