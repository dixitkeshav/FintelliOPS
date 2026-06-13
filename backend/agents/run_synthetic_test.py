"""
Run the full agent pipeline on synthetic data and print evaluation report.

Usage:  cd backend && PYTHONPATH=. python3 -m agents.run_synthetic_test
        cd backend && PYTHONPATH=. python3 -m agents.run_synthetic_test NIFTY
"""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from agents.orchestrator import AgentOrchestrator
from agents.synthetic_data import aggregate_sentiment, load_synthetic_articles, list_synthetic_tickers


def main() -> int:
    ticker = (sys.argv[1] if len(sys.argv) > 1 else "RELIANCE").upper()
    articles = load_synthetic_articles(ticker)
    agg = aggregate_sentiment(articles)

    print(f"=== Synthetic pipeline test: {ticker} ===")
    print(f"Articles: {len(articles)} | Aggregate sentiment: {agg}")
    print(f"Available tickers: {', '.join(list_synthetic_tickers())}\n")

    orch = AgentOrchestrator()
    result = orch.run(
        articles,
        ticker=ticker,
        aggregate_sentiment=agg,
        news_meta={"source": "synthetic", "fetch_ms": 0, "sources": {"synthetic": len(articles)}},
    )

    eval_report = result.get("evaluation", {})
    print("--- Agent call status ---")
    for agent_id, card in (result.get("agents") or {}).items():
        sig = card.get("signal", "?")
        out = (card.get("output") or "")[:90]
        print(f"  [{agent_id}] called={card.get('called')} signal={sig}")
        print(f"    → {out}...")

    print("\n--- Evaluation ---")
    print(json.dumps(eval_report, indent=2))

    if eval_report.get("agents_missing"):
        print(f"\nFAILED: missing agents {eval_report['agents_missing']}")
        return 1
    if not eval_report.get("pipeline_completed"):
        print("\nFAILED: pipeline not fully completed")
        return 1

    print(f"\nPASSED — overall score {eval_report.get('overall_score')}%")
    print(f"Recommendation: {result.get('recommendation')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
