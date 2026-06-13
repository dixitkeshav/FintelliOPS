"""
Fabric IQ — Semantic business understanding for FintelliOps.

DEMO: networkx knowledge graph over fabric_ontology.json.
  Models sectors, companies, macro correlations, risk thresholds
  as a connected graph with typed edges.

PRODUCTION: Microsoft Fabric REST APIs with ontology-driven
  entity resolution over real market taxonomy data.
  Fabric IQ SDK would replace this with:
    from microsoft.fabric import FabricClient
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)

ONTOLOGY_PATH = Path(__file__).resolve().parent.parent / "fintelliops_data" / "fabric_ontology.json"


class FabricIQClient:
    """Semantic layer for sectors, macro correlations, and risk thresholds."""

    def __init__(self) -> None:
        self.ontology = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
        self.graph = self._build_graph()
        logger.info(
            "FabricIQ: graph loaded — %s nodes, %s edges",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )

    def _build_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        sector_by_name = {s["name"]: s for s in self.ontology.get("sectors", [])}

        for sector in self.ontology.get("sectors", []):
            graph.add_node(sector["id"], type="sector", **sector)

        for sector in self.ontology.get("sectors", []):
            for company in sector.get("companies", []):
                graph.add_node(company, type="company")
                graph.add_edge(company, sector["id"], relation="belongs_to")

        for corr in self.ontology.get("macro_correlations", []):
            indicator = corr["indicator"]
            if indicator not in graph:
                graph.add_node(indicator, type="macro_indicator")
            sector_name = corr["sector"]
            sector_id = sector_by_name.get(sector_name, {}).get("id", sector_name)
            graph.add_edge(
                indicator,
                sector_id,
                relation="correlates_with",
                direction=corr.get("direction"),
                strength=corr.get("strength"),
            )

        return graph

    def get_sector_context(self, sector_name: str) -> dict[str, Any]:
        for node, data in self.graph.nodes(data=True):
            if data.get("type") == "sector" and data.get("name") == sector_name:
                return dict(data)
        return {}

    def get_macro_correlations(self, indicator: str) -> list[dict[str, Any]]:
        correlations = [
            c for c in self.ontology.get("macro_correlations", [])
            if c.get("indicator") == indicator
        ]
        return sorted(correlations, key=lambda x: x.get("strength", 0), reverse=True)

    def get_risk_threshold(self, score: float) -> dict[str, Any]:
        thresholds = self.ontology.get("risk_thresholds", {})
        for level, data in thresholds.items():
            if score <= data.get("max_score", 10):
                return {"level": level, **data}
        high = thresholds.get("high", {})
        return {"level": "high", **high}

    def get_companies_for_sector(self, sector_id: str) -> list[str]:
        data = self.graph.nodes.get(sector_id, {})
        return list(data.get("companies", []))

    def get_sector_for_company(self, company: str) -> str:
        for _, target, edge_data in self.graph.out_edges(company, data=True):
            if edge_data.get("relation") == "belongs_to":
                sector_data = self.graph.nodes.get(target, {})
                return sector_data.get("name", target)
        return ""

    def health_check(self) -> dict[str, Any]:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "sectors": sum(1 for _, d in self.graph.nodes(data=True) if d.get("type") == "sector"),
            "companies": sum(1 for _, d in self.graph.nodes(data=True) if d.get("type") == "company"),
            "macro_indicators": sum(
                1 for _, d in self.graph.nodes(data=True) if d.get("type") == "macro_indicator"
            ),
        }
