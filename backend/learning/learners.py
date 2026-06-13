"""Learner data helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent / "data" / "learner_performance.json"


def load_all_learners() -> list[dict[str, Any]]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def load_learner(learner_id: str) -> dict[str, Any] | None:
    for learner in load_all_learners():
        if learner["learner_id"] == learner_id:
            return learner
    return None


def known_learner_ids() -> list[str]:
    return [l["learner_id"] for l in load_all_learners()]
