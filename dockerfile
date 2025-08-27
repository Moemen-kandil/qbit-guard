# Dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY src/guard.py /app/guard.py
COPY src/watcher.py /app/watcher.py

ENTRYPOINT ["python", "/app/watcher.py"]
