# app/services/logging_config.py
import logging
import os
from pythonjsonlogger.json import JsonFormatter  # updated import path

def setup_logging():
    root = logging.getLogger()

    # Avoid duplicate handlers in reload/test runs
    if root.handlers:
        return logging.getLogger(__name__)

    root.setLevel(logging.INFO)

    if os.getenv("ENV", "dev") == "prod":
        formatter = JsonFormatter()  # structured JSON in production
    else:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Optional: reduce noise
    logging.getLogger("uvicorn.access").disabled = True

    return logging.getLogger(__name__)
