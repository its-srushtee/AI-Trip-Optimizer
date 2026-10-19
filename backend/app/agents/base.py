"""Base agent interface. Each agent mutates the shared workflow state dict."""
from typing import Any


class BaseAgent:
    name: str = "base"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
