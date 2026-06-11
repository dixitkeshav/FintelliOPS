"""API views for the enterprise learning certification multi-agent system."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from learning.agents.orchestrator import LearningOrchestrator, LEARNING_PIPELINE_STEPS
from learning.foundry_client import get_foundry_status
from learning.iq import WorkIQ, FoundryIQ, FabricIQ
from learning.mcp_learn import is_mcp_available

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"


@api_view(["GET"])
def learning_health(request):
    """Health check for the learning certification subsystem."""
    return Response({
        "status": "ok",
        "challenge": "Reasoning Agents — Enterprise Learning Certification",
        "agents": [s[1] for s in LEARNING_PIPELINE_STEPS if s[0] not in ("intake", "recommendation")],
        "iq_layers": ["Work IQ", "Foundry IQ", "Fabric IQ"],
        "foundry": get_foundry_status(),
        "mcp_learn": is_mcp_available(),
        "synthetic_data_only": True,
    })


@api_view(["GET"])
def learning_learners(request):
    """List synthetic learners."""
    with open(DATA_DIR / "learner_performance.json", encoding="utf-8") as f:
        learners = json.load(f)
    return Response({"learners": learners, "count": len(learners)})


@api_view(["GET"])
def learning_teams(request):
    """List synthetic teams from work signals."""
    with open(DATA_DIR / "work_signals.json", encoding="utf-8") as f:
        signals = json.load(f)
    teams = sorted({s["team"] for s in signals})
    return Response({"teams": teams})


@api_view(["POST"])
def learning_run(request):
    """
    Run the full enterprise learning certification pipeline.

    Body: { "learner_id": "L-1001", "topics": ["..."], "team": "TEAM-A", "certification": "AZ-204" }
    """
    body = request.data if hasattr(request, "data") else {}
    learner_id = body.get("learner_id", "L-1001")
    topics = body.get("topics") or ["Azure fundamentals", "Exam preparation"]
    team = body.get("team", "TEAM-A")
    certification = body.get("certification")

    try:
        orchestrator = LearningOrchestrator()
        result = orchestrator.run(
            learner_id=learner_id,
            topics=topics if isinstance(topics, list) else [topics],
            team=team,
            certification=certification,
        )
        return Response(result)
    except Exception as e:
        logger.exception("Learning pipeline failed: %s", e)
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
def learning_iq_status(request):
    """Inspect IQ layer connectivity and sample retrieval."""
    foundry = FoundryIQ()
    fabric = FabricIQ()
    work = WorkIQ()
    learner_id = request.query_params.get("learner_id", "L-1001")

    return Response({
        "foundry_iq": {
            "sources": foundry.list_sources(),
            "sample_retrieval": foundry.retrieve("AZ-204 certification study", top_k=2),
        },
        "fabric_iq": {
            "skill_gaps": fabric.compute_skill_gaps(learner_id),
            "team_summary": fabric.team_readiness_summary("TEAM-A"),
        },
        "work_iq": {
            "engagement_context": work.engagement_context(learner_id),
        },
    })


@api_view(["GET"])
def learning_docs(request):
    """List synthetic knowledge documents (Foundry IQ sources)."""
    docs_dir = DATA_DIR / "documents"
    docs = []
    for path in sorted(docs_dir.glob("*.md")):
        docs.append({
            "id": path.stem,
            "title": path.stem.replace("_", " ").title(),
            "size_bytes": path.stat().st_size,
        })
    return Response({"documents": docs, "synthetic": True})
