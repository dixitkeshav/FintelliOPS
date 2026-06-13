"""
Fabric IQ — Semantic business understanding layer.

DEMO: networkx knowledge graph over fabric_semantic_model.json.
PRODUCTION: Microsoft Fabric REST APIs with ontology-driven
entity resolution, skill gap analysis, and semantic search
over unified business entities.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class FabricIQClient:
    """Semantic layer over certification ontology and learner performance."""

    def __init__(self) -> None:
        model_path = DATA_DIR / "fabric_semantic_model.json"
        learner_path = DATA_DIR / "learner_performance.json"
        self.model = json.loads(model_path.read_text(encoding="utf-8"))
        self.learners = json.loads(learner_path.read_text(encoding="utf-8"))
        self.learners_by_id = {l["learner_id"]: l for l in self.learners}
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        cert_by_id = {c["id"]: c for c in self.model.get("certifications", [])}

        for cert in self.model.get("certifications", []):
            graph.add_node(f"cert:{cert['id']}", type="certification", **cert)

        for role in self.model.get("roles", []):
            graph.add_node(f"role:{role['name']}", type="role", **role)
            primary = role.get("primary_certification")
            if primary and primary in cert_by_id:
                graph.add_edge(
                    f"role:{role['name']}",
                    f"cert:{primary}",
                    relation="requires",
                )

        for cert in self.model.get("certifications", []):
            for skill in cert.get("skills", []):
                graph.add_node(f"skill:{skill}", type="skill", name=skill)
                graph.add_edge(f"cert:{cert['id']}", f"skill:{skill}", relation="tests")

        for team in self.model.get("teams", []):
            graph.add_node(f"team:{team['id']}", type="team", **team)

        for learner in self.learners:
            cert_id = learner.get("certification")
            if cert_id:
                graph.add_node(f"learner:{learner['learner_id']}", type="learner", **learner)
                graph.add_edge(
                    f"learner:{learner['learner_id']}",
                    f"cert:{cert_id}",
                    relation="pursuing",
                )
            team_id = learner.get("team_id")
            if team_id:
                graph.add_edge(f"learner:{learner['learner_id']}", f"team:{team_id}", relation="member_of")

        return graph

    def get_certification_for_role(self, role: str) -> dict[str, Any]:
        role_node = f"role:{role}"
        if role_node not in self.graph:
            for node, data in self.graph.nodes(data=True):
                if data.get("type") == "role" and data.get("name", "").lower() == role.lower():
                    role_node = node
                    break

        cert_ids = [
            target.replace("cert:", "")
            for _, target, edge_data in self.graph.out_edges(role_node, data=True)
            if edge_data.get("relation") == "requires" and target.startswith("cert:")
        ]

        if not cert_ids:
            return {"cert_id": None, "skills": [], "recommended_hours": 20, "prerequisites": []}

        cert_id = cert_ids[0]
        cert_data = self.graph.nodes.get(f"cert:{cert_id}", {})
        return {
            "cert_id": cert_id,
            "name": cert_data.get("name", cert_id),
            "skills": cert_data.get("skills", []),
            "recommended_hours": cert_data.get("recommended_hours", 20),
            "prerequisites": cert_data.get("prerequisites", []),
        }

    def get_skill_gaps(self, learner_id: str, target_cert: str) -> list[str]:
        learner = self.learners_by_id.get(learner_id, {})
        current_skills = set(learner.get("skills", []))
        cert_node = f"cert:{target_cert}"
        required_skills = {
            self.graph.nodes[target].get("name", target.replace("skill:", ""))
            for _, target, edge_data in self.graph.out_edges(cert_node, data=True)
            if edge_data.get("relation") == "tests" and target.startswith("skill:")
        }
        return sorted(required_skills - current_skills)

    def get_team_readiness(self, team_id: str) -> dict[str, Any]:
        team_learners = [l for l in self.learners if l.get("team_id") == team_id]
        if not team_learners:
            return {
                "team_id": team_id,
                "avg_practice_score": 0.0,
                "pass_rate": 0.0,
                "risk_areas": [],
                "ready_count": 0,
                "total_count": 0,
            }

        scores = [l.get("practice_score_avg", 0) for l in team_learners]
        avg_score = sum(scores) / len(scores)
        pass_count = sum(1 for l in team_learners if l.get("exam_outcome") == "Pass")
        ready_count = sum(1 for s in scores if s >= 75)

        cert_scores: dict[str, list[float]] = {}
        for learner in team_learners:
            cert_scores.setdefault(learner.get("certification", "unknown"), []).append(
                learner.get("practice_score_avg", 0)
            )
        risk_areas = [
            cert for cert, vals in cert_scores.items() if sum(vals) / len(vals) < 70
        ]

        return {
            "team_id": team_id,
            "avg_practice_score": round(avg_score, 1),
            "pass_rate": round(pass_count / len(team_learners), 2),
            "risk_areas": risk_areas,
            "ready_count": ready_count,
            "total_count": len(team_learners),
        }

    def get_study_hours_recommendation(self, cert_id: str, current_score: float) -> int:
        cert_data = self.graph.nodes.get(f"cert:{cert_id}", {})
        recommended = cert_data.get("recommended_hours", 20)
        if current_score < 60:
            hours = recommended * 1.5
        elif current_score < 75:
            hours = recommended
        else:
            hours = recommended * 0.7
        return round(hours)

    def health_check(self) -> dict[str, Any]:
        cert_count = sum(
            1 for _, d in self.graph.nodes(data=True) if d.get("type") == "certification"
        )
        role_count = sum(1 for _, d in self.graph.nodes(data=True) if d.get("type") == "role")
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "certifications": cert_count,
            "roles": role_count,
        }
