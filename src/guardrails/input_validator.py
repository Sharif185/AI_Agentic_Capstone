"""Input validation guardrails.

Detects prompt injection and prohibited topics. Returns a structured
result; the caller (GuardrailManager / Agent) is responsible for acting
on it. Prohibited topics are REFUSED, not merely flagged.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional


class InputValidator:
    MAX_INPUT_LENGTH = 500
    MIN_INPUT_LENGTH = 1

    INJECTION_PATTERNS = [
        r"ignore\s+(previous|all|prior)\s+instructions",
        r"ignore\s+the\s+(above|previous)\s+(rules|instructions)",
        r"you\s+are\s+now\s+",
        r"from\s+now\s+on\s+you\s+(are|will)",
        r"forget\s+(your|all|previous)\s+(instructions|rules|context)",
        r"disregard\s+(your|all|the)\s+(rules|instructions)",
        r"repeat\s+(everything|all|your)\s+(in\s+your\s+)?(context|prompt|instructions)",
        r"what\s+(are|is)\s+your\s+(real\s+|actual\s+)?(system\s+)?prompt",
        r"reveal\s+your\s+(system\s+)?prompt",
        r"pretend\s+(to\s+be|you\s+are)",
        r"act\s+as\s+(if\s+you\s+are\s+)?(a\s+)?(different|new|another)",
        r"admin\s+(password|credential|credentials)",
        r"give\s+me\s+(the\s+)?admin",
    ]

    PROHIBITED_TOPICS = [
        r"\bchange\s+my\s+grade\b",
        r"\bchange\s+(the\s+)?grade\s+(from|to)\b",
        r"\baccess\s+(my\s+|the\s+|other\s+)?(student\s+)?records?\b",
        r"\bapprove\s+(my|the)\s+admission",
        r"\badmit\s+me\b",
        r"\bprocess\s+(a\s+)?refund\b",
        r"\bmake\s+(a\s+)?payment\b",
        r"\bhack\b",
    ]

    def __init__(self, logger=None) -> None:
        self.logger = logger
        self.injection_regex = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        self.prohibited_regex = [re.compile(p, re.IGNORECASE) for p in self.PROHIBITED_TOPICS]

    def validate(self, user_input: Any) -> Dict[str, Any]:
        if not isinstance(user_input, str) or len(user_input.strip()) < self.MIN_INPUT_LENGTH:
            self._log("input_length", user_input, "empty_or_short")
            return {"valid": False, "reason": "Empty input", "action": "reject_empty"}

        if len(user_input) > self.MAX_INPUT_LENGTH:
            self._log("input_length", user_input, f"too_long:{len(user_input)}")
            return {"valid": False, "reason": "Input too long", "action": "reject_too_long"}

        for regex in self.injection_regex:
            if regex.search(user_input):
                self._log("prompt_injection", user_input, regex.pattern)
                return {
                    "valid": False,
                    "reason": "Prompt injection attempt detected",
                    "action": "refuse_injection",
                    "matched_pattern": regex.pattern,
                }

        for regex in self.prohibited_regex:
            if regex.search(user_input):
                self._log("prohibited_topic", user_input, regex.pattern)
                # IMPORTANT: refused, not merely flagged.
                return {
                    "valid": False,
                    "reason": f"Prohibited topic: {regex.pattern}",
                    "action": "refuse_prohibited",
                    "matched_pattern": regex.pattern,
                }

        return {"valid": True, "action": "allow", "reason": None}

    def _log(self, guardrail: str, user_input: Any, reason: str) -> None:
        if self.logger is not None:
            try:
                self.logger.log_guardrail_trigger(guardrail, user_input, reason)
            except Exception:
                pass