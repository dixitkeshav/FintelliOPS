"""
Base agent with role and memory. All specialized agents inherit from this.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentMemory:
    """Simple in-memory store per agent. Can be backed by Redis later."""
    items: list[dict] = field(default_factory=list)
    max_items: int = 50

    def add(self, data: dict) -> None:
        self.items.append(data)
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items:]

    def recent(self, n: int = 10) -> list:
        return self.items[-n:]


class BaseAgent(ABC):
    """Base class for all agents. Each has a role and memory."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.memory = AgentMemory()

    @abstractmethod
    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute agent logic. Returns a dict with findings/recommendations."""
        pass

    def _remember(self, data: dict) -> None:
        self.memory.add(data)
