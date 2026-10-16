"""Tool allow-list with per-tool rate limits and approval policy."""
from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Any, Dict, Optional


class ToolAllowlist:
    # Exactly the three permitted tools.
    ALLOWED_TOOLS = {"get_course_info", "create_support_ticket", "check_ticket_status"}

    RATE_LIMITS = {
        "get_course_info": 5,
        "create_support_ticket": 3,
        "check_ticket_status": 5,
    }

    APPROVAL_REQUIRED = {"create_support_ticket"}

    def __init__(self, logger=None) -> None:
        self.logger = logger
        self._counts: Dict[str, int] = defaultdict(int)
        self._blocked: Dict[str, int] = defaultdict(int)
        self._lock = Lock()

    # --- decisions --------------------------------------------------- #
    def is_allowed(self, tool_name: str) -> bool:
        return tool_name in self.ALLOWED_TOOLS

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self.APPROVAL_REQUIRED

    def check_rate_limit(self, tool_name: str) -> bool:
        limit = self.RATE_LIMITS.get(tool_name)
        if limit is None:
            return False
        with self._lock:
            return self._counts.get(tool_name, 0) < limit

    # --- recording --------------------------------------------------- #
    def record_call(self, tool_name: str) -> None:
        with self._lock:
            self._counts[tool_name] += 1

    def record_blocked(self, tool_name: str, reason: str) -> None:
        with self._lock:
            self._blocked[tool_name] += 1
        if self.logger is not None:
            try:
                self.logger.log_guardrail_trigger(
                    "tool_allowlist", tool_name, reason, decision="block"
                )
            except Exception:
                pass

    # --- introspection ---------------------------------------------- #
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counts": dict(self._counts),
                "blocked": dict(self._blocked),
                "limits": dict(self.RATE_LIMITS),
                "allowed": sorted(self.ALLOWED_TOOLS),
            }

    def reset(self) -> None:
        """Call at the start of each agent run so counters are run-scoped."""
        with self._lock:
            self._counts.clear()
            self._blocked.clear()