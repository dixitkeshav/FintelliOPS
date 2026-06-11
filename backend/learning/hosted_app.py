"""
Minimal WSGI entrypoint for Foundry Hosted Agent deployment.

Exposes /health and /run for container orchestration outside Django.
"""
from __future__ import annotations

import json
import os
import sys

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from learning.agents.orchestrator import LearningOrchestrator


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/health" and method == "GET":
        body = json.dumps({"status": "ok", "service": "enterprise-learning-orchestrator"}).encode()
        start_response("200 OK", [("Content-Type", "application/json")])
        return [body]

    if path == "/run" and method == "POST":
        try:
            length = int(environ.get("CONTENT_LENGTH", 0))
            raw = environ["wsgi.input"].read(length) if length else b"{}"
            payload = json.loads(raw.decode() or "{}")
            result = LearningOrchestrator().run(
                learner_id=payload.get("learner_id", "L-1001"),
                topics=payload.get("topics"),
                team=payload.get("team", "TEAM-A"),
                certification=payload.get("certification"),
            )
            body = json.dumps(result).encode()
            start_response("200 OK", [("Content-Type", "application/json")])
            return [body]
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode()
            start_response("500 Internal Server Error", [("Content-Type", "application/json")])
            return [body]

    start_response("404 Not Found", [("Content-Type", "application/json")])
    return [json.dumps({"error": "not found"}).encode()]
