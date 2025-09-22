from decouple import config

PERPLEXITY_API_KEY = config("PERPLEXITY_API_KEY")
PERPLEXITY_BASE_URL = config("PERPLEXITY_BASE_URL", default="https://api.perplexity.ai")
PERPLEXITY_MODEL = config("PERPLEXITY_MODEL", default="sonar-pro")

