# Backend Dockerfile — Sprint 1
# Multi-stage không cần thiết cho sprint 1; giữ đơn giản (KISS).

FROM python:3.12-slim

WORKDIR /app

# Cài dependency hệ thống cho asyncpg/psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    libglib2.0-0 libsm6 libxext6 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
