"""REST API endpoints for the learning certification pipeline."""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from learning.agents.orchestrator import LearningOrchestrator
from learning.foundry_client import FoundryClient
from learning.iq.fabric_iq import FabricIQClient
from learning.iq.foundry_iq import FoundryIQClient
from learning.iq.work_iq import WorkIQClient
from learning.learners import known_learner_ids, load_learner

logger = logging.getLogger(__name__)

_orchestrator: LearningOrchestrator | None = None
_last_result: dict[str, Any] | None = None


def _get_orchestrator() -> LearningOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LearningOrchestrator()
    return _orchestrator


def _format_agent_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "output": result.get("output", ""),
        "iq_layers_used": result.get("iq_layers_used", []),
        "citations": result.get("citations", []),
        "fabric_entities": result.get("fabric_entities", []),
        "work_signals": result.get("work_signals", {}),
        "completed": result.get("completed", False),
        "error": result.get("error"),
    }


def _build_response(context: dict[str, Any], orch: LearningOrchestrator) -> dict[str, Any]:
    agents_out = {
        name: _format_agent_result(result)
        for name, result in context.get("agents", {}).items()
    }
    return {
        "pipeline_completed": context.get("pipeline_completed", False),
        "learner": context.get("learner"),
        "recommendation": context.get("recommendation", ""),
        "agents": agents_out,
        "all_citations": context.get("all_citations", []),
        "evaluation": context.get("evaluation", {}),
        "iq_health": {
            "foundry_iq": orch.foundry_iq.health_check(),
            "fabric_iq": orch.fabric_iq.health_check(),
            "work_iq": orch.work_iq.health_check(),
            "llm": orch.foundry_client.health_check(),
        },
        "pipeline_start": context.get("pipeline_start"),
        "pipeline_end": context.get("pipeline_end"),
    }


@api_view(["POST"])
def learning_run(request: Request) -> Response:
    learner_id = request.data.get("learner_id", "")
    team_id = request.data.get("team_id", "TEAM-A")
    topics = request.data.get("topics", [])

    if not learner_id or learner_id not in known_learner_ids():
        return Response(
            {"error": f"Invalid learner_id. Known: {known_learner_ids()}"},
            status=400,
        )

    if not isinstance(topics, list) or not topics:
        return Response({"error": "topics must be a non-empty list"}, status=400)

    try:
        global _last_result
        orch = _get_orchestrator()
        context = orch.run(learner_id=learner_id, team_id=team_id, topics=topics)
        _last_result = context
        return Response(_build_response(context, orch))
    except Exception as exc:
        logger.error("Learning pipeline failed: %s", exc, exc_info=True)
        return Response({"error": str(exc)}, status=500)


@api_view(["GET"])
def learning_health(request: Request) -> Response:
    orch = _get_orchestrator()
    foundry_health = orch.foundry_iq.health_check()
    return Response(
        {
            "status": "ok",
            "agents": 5,
            "iq_layers": ["foundry_iq", "fabric_iq", "work_iq"],
            "llm_provider": orch.foundry_client.provider,
            "azure_search_mode": foundry_health.get("mode", "local_fallback"),
            "mcp_learn_enabled": getattr(settings, "MCP_LEARN_ENABLED", False),
        }
    )


@api_view(["GET"])
def learning_status(request: Request) -> Response:
    if _last_result is None:
        return Response({"status": "idle", "agents_completed": 0, "agents": {}})
    agents = _last_result.get("agents", {})
    completed = sum(1 for a in agents.values() if a.get("completed"))
    return Response(
        {
            "status": "completed" if _last_result.get("pipeline_completed") else "running",
            "agents_completed": completed,
            "agents_total": 5,
            "agents": {
                name: {
                    "completed": r.get("completed", False),
                    "agent_name": name,
                }
                for name, r in agents.items()
            },
        }
    )


@api_view(["GET"])
def learning_learners(request: Request) -> Response:
    learners = []
    for lid in known_learner_ids():
        learner = load_learner(lid)
        if learner:
            learners.append(learner)
    return Response({"learners": learners})


@api_view(["GET"])
def learning_topics(request: Request) -> Response:
    model = FabricIQClient().model
    topics: list[str] = []
    for cert in model.get("certifications", []):
        topics.append(cert["id"])
        topics.extend(cert.get("skills", []))
    return Response({"topics": sorted(set(topics))})
