"""Central guardrail manager — coordinates all four guardrails."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .input_validator import InputValidator
from .output_validator import OutputValidator
from .tool_allowlist import ToolAllowlist
from .iteration_limiter import IterationLimiter


class GuardrailManager:
    def __init__(
        self,
        logger=None,
        max_iterations: int = 5,
        max_tool_calls: int = 3,
        max_rag_calls: int = 2,
    ) -> None:
        self.logger = logger
        self.input_validator = InputValidator(logger)
        self.output_validator = OutputValidator(logger)
        self.tool_allowlist = ToolAllowlist(logger)
        self.iteration_limiter = IterationLimiter(
            max_iterations, max_tool_calls, max_rag_calls, logger
        )
        self.trigger_counts = {
            "input_refused": 0,
            "output_flagged": 0,
            "tool_blocked": 0,
            "iteration_blocked": 0,
        }

    # --- input --- #
    def validate_input(self, user_input: str) -> Dict[str, Any]:
        try:
            result = self.input_validator.validate(user_input)
        except Exception as exc:
            if self.logger:
                self.logger.log_validation_failure("input", str(exc), user_input)
            return {"valid": False, "reason": f"validator error: {exc}", "action": "reject_error"}
        if not result.get("valid"):
            self.trigger_counts["input_refused"] += 1
        return result

    # --- output --- #
    def validate_output(
        self,
        response: str,
        context_used: bool = False,
        sources: Optional[list] = None,
    ) -> Dict[str, Any]:
        try:
            result = self.output_validator.validate(response, context_used, sources)
        except Exception as exc:
            if self.logger:
                self.logger.log_validation_failure("output", str(exc), response)
            return {"valid": True, "warnings": [f"validator error: {exc}"], "action": "allow"}
        if not result.get("valid"):
            self.trigger_counts["output_flagged"] += 1
        return result

    # --- tools --- #
    def check_tool(self, tool_name: str) -> Dict[str, Any]:
        if not self.tool_allowlist.is_allowed(tool_name):
            self.trigger_counts["tool_blocked"] += 1
            self.tool_allowlist.record_blocked(tool_name, "not_in_allowlist")
            return {"allowed": False, "reason": "not_in_allowlist"}

        if not self.tool_allowlist.check_rate_limit(tool_name):
            self.trigger_counts["tool_blocked"] += 1
            self.tool_allowlist.record_blocked(tool_name, "rate_limit")
            return {"allowed": False, "reason": "rate_limit"}

        self.tool_allowlist.record_call(tool_name)
        return {
            "allowed": True,
            "requires_approval": self.tool_allowlist.requires_approval(tool_name),
        }

    # --- iteration --- #
    def check_iteration(self, state: Any) -> Dict[str, Any]:
        try:
            result = self.iteration_limiter.check(state)
        except Exception as exc:
            if self.logger:
                self.logger.log_validation_failure("iteration", str(exc), None)
            return {"allowed": False, "reason": "limiter_error"}
        if not result.get("allowed"):
            self.trigger_counts["iteration_blocked"] += 1
        return result

    def check_tool_limit(self, state: Any) -> Dict[str, Any]:
        return self.iteration_limiter.check_tool(state)

    def check_rag(self, state: Any) -> Dict[str, Any]:
        return self.iteration_limiter.check_rag(state)

    # --- summary --- #
    def get_summary(self) -> Dict[str, Any]:
        return {
            "triggers": dict(self.trigger_counts),
            "tool_calls": self.tool_allowlist.get_stats(),
        }

    def reset(self) -> None:
        self.trigger_counts = {k: 0 for k in self.trigger_counts}
        self.tool_allowlist.reset()