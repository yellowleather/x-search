# Use official Python runtime as base image
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY workers ./workers

EXPOSE 8080

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
