# Base (keeps runtime minimal)
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Builder (compilers live only here)
FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc \
    && rm -rf /var/lib/apt/lists/*    # keep image small
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Runtime (no compilers, install from wheels)
FROM base AS runtime
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /app/requirements.txt \
    && rm -rf /wheels

# App code last for better caching
COPY app ./app

# Create and switch to non-root user
RUN groupadd -g 10001 appuser \
 && useradd -m -u 10001 -g appuser -s /usr/sbin/nologin appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 80
# FastAPI’s CLI is the current recommended simple entrypoint
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
