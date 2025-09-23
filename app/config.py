import os
from decouple import config

# First check OS environment variables (production),
# fallback to .env if running locally
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY") or config("PERPLEXITY_API_KEY")
PERPLEXITY_BASE_URL = os.getenv("PERPLEXITY_BASE_URL") or config("PERPLEXITY_BASE_URL", default="https://api.perplexity.ai")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL") or config("PERPLEXITY_MODEL", default="sonar-pro")
