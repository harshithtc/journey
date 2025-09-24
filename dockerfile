# Base (keeps runtime minimal)
FROM python:3.11-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Builder (compilers & wheels)
FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip setuptools>=78.1.1
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Runtime (install from wheels)
FROM base AS runtime
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /app/requirements.txt \
    && rm -rf /wheels

# Copy app source last for caching
COPY app ./app

# Create and switch to non-root user
RUN groupadd -g 10001 appuser \
  && useradd -m -u 10001 -g appuser -s /usr/sbin/nologin appuser \
  && chown -R appuser:appuser /app
USER appuser

# Change port to 10000 or use platform env PORT
EXPOSE 10000

# Use shell command to allow environment PORT override
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
