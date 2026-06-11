FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/ ./backend/

ENV PYTHONPATH=/app/backend
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app/backend

EXPOSE 8080

CMD ["gunicorn", "learning.hosted_app:app", "-b", "0.0.0.0:8080", "-w", "2", "--timeout", "120"]
