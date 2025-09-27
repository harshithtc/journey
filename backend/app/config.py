# app/config.py
import os
from decouple import config

# App meta
APP_NAME = os.getenv("APP_NAME") or config("APP_NAME", default="Journey Backend API")

# External AI service (Perplexity)
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY") or config("PERPLEXITY_API_KEY", default="")
PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL") or config("PERPLEXITY_BASE_URL", default="https://api.perplexity.ai")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL") or config("PERPLEXITY_MODEL", default="sonar-pro")

# Database (Render injects this; .env for local)
DATABASE_URL = os.getenv("DATABASE_URL") or config(
    "DATABASE_URL",
    default="postgresql://postgres:postgres@localhost:5432/tourplanner",
)
