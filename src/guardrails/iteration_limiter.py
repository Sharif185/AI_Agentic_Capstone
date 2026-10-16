"""Iteration limiter — reads the agent's real state, does not own counters."""
from __future__ import annotations

from typing import Any, Dict


def _get(state: Any, *names, default: int = 0) -> int:
    """Read a counter from state, tolerant of common attribute names."""
    for name in names:
        if hasattr(state, name):
            try:
                return int(getattr(state, name))
            except (TypeError, ValueError):
                continue
    return default


class IterationLimiter:
    def __init__(
        self,
        max_iterations: int = 5,
        max_tool_calls: int = 3,
        max_rag_calls: int = 2,
        logger=None,
    ) -> None:
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls
        self.max_rag_calls = max_rag_calls
        self.logger = logger

    # -------- full-loop check (iteration cap) -------- #
    def check(self, state: Any) -> Dict[str, Any]:
        iterations = _get(state, "iterations", "iteration_count", "iteration")
        if iterations >= self.max_iterations:
            self._trigger("iteration_limit", iterations)
            return {"allowed": False, "reason": "max_iterations"}

        tool_calls = _get(state, "tool_call_count", "tool_calls", "tool_calls_made")
        if tool_calls > self.max_tool_calls:
            self._trigger("tool_call_limit", tool_calls)
            return {"allowed": False, "reason": "max_tool_calls"}

        rag_calls = _get(state, "rag_call_count", "rag_calls", "rag_calls_made")
        if rag_calls > self.max_rag_calls:
            self._trigger("rag_call_limit", rag_calls)
            return {"allowed": False, "reason": "max_rag_calls"}

        return {"allowed": True, "reason": None}

    # -------- per-operation checks -------- #
    def check_tool(self, state: Any) -> Dict[str, Any]:
        tool_calls = _get(state, "tool_call_count", "tool_calls", "tool_calls_made")
        if tool_calls >= self.max_tool_calls:
            self._trigger("tool_call_limit", tool_calls)
            return {"allowed": False, "reason": "max_tool_calls"}
        return {"allowed": True, "reason": None}

    def check_rag(self, state: Any) -> Dict[str, Any]:
        rag_calls = _get(state, "rag_call_count", "rag_calls", "rag_calls_made")
        if rag_calls >= self.max_rag_calls:
            self._trigger("rag_call_limit", rag_calls)
            return {"allowed": False, "reason": "max_rag_calls"}
        return {"allowed": True, "reason": None}

    def _trigger(self, guardrail: str, value: int) -> None:
        if self.logger is not None:
            try:
                self.logger.log_guardrail_trigger(
                    guardrail, value, f"limit reached (value={value})", decision="stop"
                )
            except Exception:
                pass