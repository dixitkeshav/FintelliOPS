"""
Evaluation: sentiment accuracy vs labels, strategy metrics, ablation, latency.
"""
import logging
import time
from typing import Any, Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)


def sentiment_accuracy(predicted: list[str], labels: list[str]) -> dict[str, float]:
    """Accuracy and per-class metrics. Labels and predicted: 'positive'|'negative'|'neutral'."""
    if not predicted or len(predicted) != len(labels):
        return {"accuracy": 0.0, "macro_f1": 0.0}
    pred = [p.lower().strip() for p in predicted]
    lab = [l.lower().strip() for l in labels]
    correct = sum(1 for p, l in zip(pred, lab) if p == l)
    accuracy = correct / len(lab)

    # Macro F1
    for c in ["positive", "negative", "neutral"]:
        tp = sum(1 for p, l in zip(pred, lab) if p == c and l == c)
        fp = sum(1 for p, l in zip(pred, lab) if p == c and l != c)
        fn = sum(1 for p, l in zip(pred, lab) if l == c and p != c)
        prec = tp / (tp + fp) if (tp + fp) else 0
        rec = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
    # Simplified macro: average F1 over classes
    f1s = []
    for c in ["positive", "negative", "neutral"]:
        tp = sum(1 for p, l in zip(pred, lab) if p == c and l == c)
        fp = sum(1 for p, l in zip(pred, lab) if p == c and l != c)
        fn = sum(1 for p, l in zip(pred, lab) if l == c and p != c)
        prec = tp / (tp + fp) if (tp + fp) else 0
        rec = tp / (tp + fn) if (tp + fn) else 0
        f1s.append(2 * prec * rec / (prec + rec) if (prec + rec) else 0)
    macro_f1 = float(np.mean(f1s)) if f1s else 0.0

    return {"accuracy": round(accuracy, 4), "macro_f1": round(macro_f1, 4)}


def latency_benchmark(fn: Callable[[], Any], num_runs: int = 5) -> dict[str, float]:
    """Run fn num_runs times and return mean/std latency in seconds."""
    times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return {
        "mean_sec": round(float(np.mean(times)), 4),
        "std_sec": round(float(np.std(times)), 4),
        "runs": num_runs,
    }


def ablation_with_without_agents(
    with_agents_metric: float,
    without_agents_metric: float,
    metric_name: str = "sharpe",
) -> dict[str, Any]:
    """Ablation: compare metric with vs without agents."""
    diff = with_agents_metric - without_agents_metric
    return {
        "with_agents": with_agents_metric,
        "without_agents": without_agents_metric,
        "delta": round(diff, 4),
        "metric": metric_name,
    }
