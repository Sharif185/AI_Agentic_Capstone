"""Structured logging for the Student Support Agent.

Captures six layers of events (model calls, RAG retrievals, tool calls,
approvals, agent iterations, guardrail events) as JSON Lines on disk and
readable text on the console.

Privacy: a small set of sensitive keys is redacted at emit-time. Do not
log full API keys, passwords, tokens, credentials, or full student records.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


_SENSITIVE_KEYS = {
    "password", "passwd", "pwd",
    "api_key", "apikey", "token", "access_token", "refresh_token",
    "secret", "client_secret", "private_key",
    "authorization", "auth", "credential", "credentials",
    "session_key", "student_record",
}

_DEFAULT_PREVIEW_LEN = 200

# Tracks which session_ids already have handlers attached so we don't
# duplicate console/file output when a logger is constructed repeatedly.
_HANDLER_REGISTRY_LOCK = threading.Lock()
_REGISTERED_SESSIONS: Dict[str, bool] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate(value: Any, limit: int = _DEFAULT_PREVIEW_LEN) -> str:
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    return text if len(text) <= limit else text[:limit] + f"...[+{len(text) - limit}c]"


def _sanitize(value: Any, depth: int = 0) -> Any:
    """Recursively redact sensitive keys and truncate long strings."""
    if depth > 6:
        return "<max-depth>"
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for k, v in value.items():
            if isinstance(k, str) and k.lower() in _SENSITIVE_KEYS:
                out[k] = "<redacted>"
            else:
                out[k] = _sanitize(v, depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [_sanitize(v, depth + 1) for v in value]
    if isinstance(value, str):
        return _truncate(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _truncate(str(value))


class AgentLogger:
    """Structured logger for all agent activities.

    Thread-safety: writes are serialised with an internal lock. Each
    instance owns its own event list; no state is shared across sessions.
    """

    def __init__(self, log_dir: str | Path = "logs", session_id: Optional[str] = None) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id or f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.log_file = self.log_dir / f"{self.session_id}.log"

        self._lock = threading.Lock()
        self.events: List[Dict[str, Any]] = []

        self._logger = logging.getLogger(f"agent.{self.session_id}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False  # don't leak to root logger

        with _HANDLER_REGISTRY_LOCK:
            already = _REGISTERED_SESSIONS.get(self.session_id, False)
            if not already:
                fh = logging.FileHandler(self.log_file, encoding="utf-8")
                fh.setFormatter(logging.Formatter("%(message)s"))
                self._logger.addHandler(fh)

                ch = logging.StreamHandler()
                ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
                self._logger.addHandler(ch)

                _REGISTERED_SESSIONS[self.session_id] = True

    # ------------------------------------------------------------------ #
    # Core emit
    # ------------------------------------------------------------------ #
    def _emit(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "timestamp": _utc_now_iso(),
            "session_id": self.session_id,
            "event_type": event_type,
            "data": _sanitize(data),
        }
        try:
            line = json.dumps(event, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as exc:
            # Never lose the event silently; emit a minimal fallback.
            line = json.dumps({
                "timestamp": event["timestamp"],
                "session_id": self.session_id,
                "event_type": "log_serialization_error",
                "data": {"original_event_type": event_type, "error": str(exc)},
            })

        with self._lock:
            self.events.append(event)
            try:
                self._logger.info(line)
            except Exception as exc:  # pragma: no cover - defensive
                # Logging failure should not silently pass.
                print(f"[AgentLogger] write failed: {exc}")
        return event

    # ------------------------------------------------------------------ #
    # Layer 1 — Model calls
    # ------------------------------------------------------------------ #
    def log_model_call(
        self,
        model: str,
        prompt_preview: str,
        response_preview: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        latency_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._emit("model_call", {
            "model": model,
            "prompt_preview": _truncate(prompt_preview),
            "response_preview": _truncate(response_preview),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "success": success,
            "error": error,
        })

    # ------------------------------------------------------------------ #
    # Layer 2 — RAG retrievals
    # ------------------------------------------------------------------ #
    def log_rag_retrieval(
        self,
        query: str,
        num_results: int,
        sources: Iterable[str],
        latency_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._emit("rag_retrieval", {
            "query": _truncate(query),
            "num_results": num_results,
            "sources": list(sources or []),
            "latency_ms": latency_ms,
            "success": success,
            "error": error,
        })

    # ------------------------------------------------------------------ #
    # Layer 3 — Tool calls
    # ------------------------------------------------------------------ #
    def log_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        success: bool,
        result_preview: Any = None,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._emit("tool_call", {
            "tool": tool_name,
            "arguments": arguments,
            "success": success,
            "result_preview": _truncate(result_preview),
            "latency_ms": latency_ms,
            "error": error,
        })

    # ------------------------------------------------------------------ #
    # Layer 4 — Approvals
    # ------------------------------------------------------------------ #
    def log_approval(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        approved: bool,
        mode: str,
        outcome: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._emit("approval", {
            "tool": tool_name,
            "arguments": arguments,
            "approved": approved,
            "mode": mode,
            "outcome": outcome,
        })

    # ------------------------------------------------------------------ #
    # Layer 5 — Agent iterations
    # ------------------------------------------------------------------ #
    def log_agent_iteration(
        self,
        iteration: int,
        action: str,
        data: Any = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._emit("agent_iteration", {
            "iteration": iteration,
            "action": action,
            "data_preview": _truncate(data),
            "status": status,
        })

    def log_agent_stop(
        self,
        reason: str,
        iterations: int,
        tool_calls: int,
        rag_calls: int,
    ) -> Dict[str, Any]:
        return self._emit("agent_stop", {
            "reason": reason,
            "iterations": iterations,
            "tool_calls": tool_calls,
            "rag_calls": rag_calls,
        })

    # ------------------------------------------------------------------ #
    # Layer 6 — Guardrail events
    # ------------------------------------------------------------------ #
    def log_guardrail_trigger(
        self,
        guardrail: str,
        input_data: Any,
        reason: str,
        decision: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._emit("guardrail_trigger", {
            "guardrail": guardrail,
            "input_preview": _truncate(input_data, 100),
            "reason": reason,
            "decision": decision,
        })

    def log_validation_failure(
        self,
        stage: str,
        error: str,
        data_preview: Any = None,
    ) -> Dict[str, Any]:
        return self._emit("validation_failure", {
            "stage": stage,
            "error": error,
            "data_preview": _truncate(data_preview, 100),
        })

    def log_error(
        self,
        error_type: str,
        message: str,
        context: Any = None,
    ) -> Dict[str, Any]:
        return self._emit("error", {
            "error_type": error_type,
            "message": message,
            "context": _truncate(context),
        })

    # ------------------------------------------------------------------ #
    # Introspection / summary
    # ------------------------------------------------------------------ #
    def get_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            snapshot = list(self.events)
        if event_type is None:
            return snapshot
        return [e for e in snapshot if e.get("event_type") == event_type]

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            snapshot = list(self.events)
        by_type: Dict[str, int] = {}
        for event in snapshot:
            et = event.get("event_type", "unknown")
            by_type[et] = by_type.get(et, 0) + 1
        return {
            "session_id": self.session_id,
            "total_events": len(snapshot),
            "by_type": by_type,
        }

    def save_summary(self, path: str | Path | None = None) -> str:
        target = Path(path) if path else self.log_dir / f"{self.session_id}_summary.json"
        payload = self.get_summary()
        payload["events"] = self.get_events()
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return str(target)