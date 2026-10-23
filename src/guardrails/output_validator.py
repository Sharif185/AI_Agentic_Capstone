"""Output validation guardrails.

Flags (a) hallucination-marker language and (b) missing citations when
RAG context was used. This is a heuristic — it produces explainable
warnings, not proofs. Callers decide the enforcement policy.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional


class OutputValidator:
    HALLUCINATION_MARKERS = [
        r"according\s+to\s+my\s+(knowledge|training)",
        r"\bI\s+(believe|think|assume|guess)\b",
        r"\bprobably\b",
        r"\bmight\s+be\b",
        r"\bmaybe\b",
        r"\bin\s+my\s+opinion\b",
    ]

    # Language that is *fine* — do not flag it even if it contains a marker
    # word. Keeps false positives down.
    SAFE_PHRASES = [
        r"I\s+don'?t\s+have\s+that\s+information",
        r"not\s+found",
        r"would\s+you\s+like\s+me\s+to\s+create\s+a\s+support\s+ticket",
        r"please\s+contact\s+the\s+relevant\s+office",
    ]

    def __init__(self, logger=None) -> None:
        self.logger = logger
        self.hallucination_regex = [re.compile(p, re.IGNORECASE) for p in self.HALLUCINATION_MARKERS]
        self.safe_regex = [re.compile(p, re.IGNORECASE) for p in self.SAFE_PHRASES]

    def validate(
        self,
        response: str,
        context_used: bool = False,
        sources: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        warnings: List[str] = []

        if not isinstance(response, str) or not response.strip():
            warnings.append("Empty response")
            return self._result(warnings, response)

        # If the response is a safe, honest refusal/fallback, do not flag markers.
        is_safe = any(r.search(response) for r in self.safe_regex)
        if not is_safe:
            for regex in self.hallucination_regex:
                if regex.search(response):
                    warnings.append(f"Possible ungrounded language: {regex.pattern}")

        if context_used:
            source_list = [s for s in (sources or []) if s]
            if source_list:
                # Real check: at least one source identifier must appear in the text.
                if not any(str(s).lower() in response.lower() for s in source_list):
                    warnings.append("RAG context used but no source cited")
            else:
                # No source metadata available — fall back to lexical check.
                if not any(tok in response.lower() for tok in ("source", "document", "according to")):
                    warnings.append("RAG context used but no source citation found")

        return self._result(warnings, response)

    def _result(self, warnings: List[str], response: str) -> Dict[str, Any]:
        valid = len(warnings) == 0
        action = "allow" if valid else "flag_ungrounded"
        if not valid and self.logger is not None:
            try:
                self.logger.log_guardrail_trigger(
                    "output_validation",
                    response[:100],
                    "; ".join(warnings),
                    decision=action,
                )
            except Exception:
                pass
        return {"valid": valid, "warnings": warnings, "action": action}