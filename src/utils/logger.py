"""
src/utils/logger.py
-------------------
Structured logging for the University Student-Support Case Agent.

Author : Imaan (Quality/Security Lead)
Version: 1.0
Date   : 11 September 2026

Design goals
------------
1. Every agent turn writes one structured JSON record to the rotating log
   file (logs/agent.log) AND a human-readable line to the console.
2. Fields capture everything the Quality/Security Lead needs to evaluate
   the agent against docs/quality-metrics.md:
       - user query
       - intent / selected action
       - tool name + inputs + outputs
       - RAG retrieval results and sources cited
       - agent response text
       - latency_ms  (Metric 8 — response time)
       - safety_flag (Metric 7 — boundary compliance)
       - error details
       - session / turn identifiers for traceability
3. Uses only the Python standard library (logging + json) — no extra
   dependencies required in Week 1.
4. The logger is imported and used by the agent once it is built in
   Weeks 2–6; no changes to this file should be needed.

Usage
-----
    from src.utils.logger import AgentLogger

    logger = AgentLogger()

    # At the start of a turn:
    logger.log_query(session_id="s-001", turn=1, query="What are the exam dates?")

    # After RAG retrieval:
    logger.log_retrieval(
        session_id="s-001", turn=1,
        query="What are the exam dates?",
        retrieved_chunks=[{"source": "Academic Regulations §5.1", "text": "..."}],
        sources_cited=["Academic Regulations §5.1"]
    )

    # After a tool call:
    logger.log_tool_call(
        session_id="s-001", turn=1,
        tool_name="rag_retrieval",
        tool_inputs={"query": "exam dates"},
        tool_output={"chunks": [...]},
        latency_ms=340
    )

    # After composing the final response:
    logger.log_response(
        session_id="s-001", turn=1,
        query="What are the exam dates?",
        response="Examinations are held in ...",
        sources_cited=["Academic Regulations §5.1"],
        tool_name="rag_retrieval",
        latency_ms=610,
        safety_flag=False
    )

    # If an error occurs:
    logger.log_error(
        session_id="s-001", turn=1,
        error_type="ToolTimeoutError",
        detail="rag_retrieval exceeded 5 s limit",
        query="What are the exam dates?"
    )

    # Safety / escalation event:
    logger.log_safety_event(
        session_id="s-001", turn=1,
        query="Can you change my grade?",
        boundary_rule="No grading decisions",
        action_taken="refused_and_escalated"
    )
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Resolve the logs/ directory relative to this file's location so the logger
# works regardless of where the process is started from.
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_LOGS_DIR = os.path.join(_REPO_ROOT, "logs")
_LOG_FILE = os.path.join(_LOGS_DIR, "agent.log")

# Rotate at 5 MB, keep 5 backup files — keeps the logs/ directory tidy.
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 5


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """Formats every log record as a single-line JSON string."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        # Merge any extra structured fields the caller attached.
        if hasattr(record, "structured"):
            payload.update(record.structured)
        return json.dumps(payload, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Human-readable console formatter
# ---------------------------------------------------------------------------

class _ConsoleFormatter(logging.Formatter):
    """Concise, human-readable format for the console."""

    _FMT = "%(asctime)s [%(levelname)s] %(message)s"
    _DATE = "%H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self._FMT, datefmt=self._DATE)


# ---------------------------------------------------------------------------
# AgentLogger
# ---------------------------------------------------------------------------

class AgentLogger:
    """
    Structured logger for the Student-Support Case Agent.

    One instance is sufficient for the whole application:

        from src.utils.logger import AgentLogger
        logger = AgentLogger()

    All methods are safe to call before the agent features they record
    are implemented — they simply write a structured record and return.
    """

    def __init__(
        self,
        log_level: int = logging.DEBUG,
        log_file: str = _LOG_FILE,
    ) -> None:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        self._logger = logging.getLogger("agent")
        self._logger.setLevel(log_level)

        # Avoid adding duplicate handlers if the module is imported twice.
        if not self._logger.handlers:
            # --- File handler (JSON, rotating) ---
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=_MAX_BYTES,
                backupCount=_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setFormatter(_JsonFormatter())
            file_handler.setLevel(log_level)

            # --- Console handler (human-readable) ---
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(_ConsoleFormatter())
            console_handler.setLevel(logging.INFO)

            self._logger.addHandler(file_handler)
            self._logger.addHandler(console_handler)

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _emit(
        self,
        level: int,
        event: str,
        structured: dict[str, Any],
    ) -> None:
        """Attach structured fields to the log record and emit."""
        record = self._logger.makeRecord(
            name=self._logger.name,
            level=level,
            fn="",
            lno=0,
            msg=event,
            args=(),
            exc_info=None,
        )
        record.structured = structured  # type: ignore[attr-defined]
        self._logger.handle(record)

    # ------------------------------------------------------------------
    # Public logging methods
    # ------------------------------------------------------------------

    def log_query(
        self,
        session_id: str,
        turn: int,
        query: str,
    ) -> None:
        """
        Log the raw student query at the start of a turn.

        Metrics coverage: provides the input record for every metric.
        """
        self._emit(
            logging.INFO,
            "user_query",
            {
                "session_id": session_id,
                "turn": turn,
                "query": query,
            },
        )

    def log_retrieval(
        self,
        session_id: str,
        turn: int,
        query: str,
        retrieved_chunks: list[dict[str, Any]],
        sources_cited: list[str],
    ) -> None:
        """
        Log RAG retrieval results.

        Parameters
        ----------
        retrieved_chunks : list of dicts, each with at minimum
            {"source": "<doc name / section>", "text": "<passage>"}
        sources_cited : list of source strings that will appear in the
            final response (subset of retrieved_chunks sources).

        Metrics coverage: Metric 3 (source grounding rate).
        """
        self._emit(
            logging.DEBUG,
            "rag_retrieval",
            {
                "session_id": session_id,
                "turn": turn,
                "query": query,
                "chunks_retrieved": len(retrieved_chunks),
                "retrieved_chunks": retrieved_chunks,
                "sources_cited": sources_cited,
            },
        )

    def log_tool_call(
        self,
        session_id: str,
        turn: int,
        tool_name: str,
        tool_inputs: dict[str, Any],
        tool_output: Any,
        latency_ms: float,
    ) -> None:
        """
        Log a single tool invocation (RAG retrieval, case lookup,
        ticket creation, escalation, etc.).

        Metrics coverage: Metric 6 (tool selection accuracy),
                          Metric 5 (ticket creation),
                          Metric 4 (case retrieval).
        """
        self._emit(
            logging.DEBUG,
            "tool_call",
            {
                "session_id": session_id,
                "turn": turn,
                "tool_name": tool_name,
                "tool_inputs": tool_inputs,
                "tool_output": tool_output,
                "latency_ms": round(latency_ms, 2),
            },
        )

    def log_response(
        self,
        session_id: str,
        turn: int,
        query: str,
        response: str,
        sources_cited: list[str],
        tool_name: str | None,
        latency_ms: float,
        safety_flag: bool = False,
    ) -> None:
        """
        Log the final agent response for a turn.

        Parameters
        ----------
        tool_name    : the primary tool used this turn, or None if
                       the agent answered without a tool call.
        latency_ms   : end-to-end latency from query receipt to
                       response delivery.
        safety_flag  : True if this response involved a safety
                       boundary check (even if it passed).

        Metrics coverage: Metric 1 (accuracy), Metric 3 (grounding),
                          Metric 7 (safety), Metric 8 (latency).
        """
        level = logging.WARNING if safety_flag else logging.INFO
        self._emit(
            level,
            "agent_response",
            {
                "session_id": session_id,
                "turn": turn,
                "query": query,
                "response": response,
                "sources_cited": sources_cited,
                "tool_used": tool_name,
                "latency_ms": round(latency_ms, 2),
                "safety_flag": safety_flag,
            },
        )

    def log_error(
        self,
        session_id: str,
        turn: int,
        error_type: str,
        detail: str,
        query: str | None = None,
    ) -> None:
        """
        Log an agent-level error (tool timeout, retrieval failure,
        unexpected exception, iteration cap exceeded, etc.).

        Metrics coverage: Metric 11 (loop safety — iteration cap),
                          general failure/recovery evidence.
        """
        self._emit(
            logging.ERROR,
            "agent_error",
            {
                "session_id": session_id,
                "turn": turn,
                "error_type": error_type,
                "detail": detail,
                "query": query,
            },
        )

    def log_safety_event(
        self,
        session_id: str,
        turn: int,
        query: str,
        boundary_rule: str,
        action_taken: str,
    ) -> None:
        """
        Log a safety / boundary event.

        Parameters
        ----------
        boundary_rule : the specific rule triggered, e.g.
                        "No grading decisions" or "No admissions decisions".
        action_taken  : what the agent did, e.g.
                        "refused_and_escalated" or "refused_no_ticket".

        Metrics coverage: Metric 7 (safety boundary compliance — 100 % target).
        """
        self._emit(
            logging.WARNING,
            "safety_event",
            {
                "session_id": session_id,
                "turn": turn,
                "query": query,
                "boundary_rule": boundary_rule,
                "action_taken": action_taken,
            },
        )

    def log_session_start(self, session_id: str) -> None:
        """Log the beginning of a new student session."""
        self._emit(
            logging.INFO,
            "session_start",
            {
                "session_id": session_id,
                "started_at": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    def log_session_end(
        self,
        session_id: str,
        total_turns: int,
        total_latency_ms: float,
    ) -> None:
        """
        Log the end of a student session with summary statistics.

        Metrics coverage: Metric 8 (latency — session-level total).
        """
        self._emit(
            logging.INFO,
            "session_end",
            {
                "session_id": session_id,
                "total_turns": total_turns,
                "total_latency_ms": round(total_latency_ms, 2),
                "ended_at": datetime.now(tz=timezone.utc).isoformat(),
            },
        )


# ---------------------------------------------------------------------------
# Module-level default instance
# ---------------------------------------------------------------------------

# Import and use this directly for convenience:
#   from src.utils.logger import logger
#   logger.log_query(...)
logger = AgentLogger()


# ---------------------------------------------------------------------------
# Quick smoke-test — run this file directly to verify the logger works
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Running logger smoke test …\n")

    _log = AgentLogger()
    _sid = "smoke-test-001"

    _log.log_session_start(session_id=_sid)

    _t0 = time.perf_counter()
    _log.log_query(session_id=_sid, turn=1, query="What are the exam dates?")

    _log.log_retrieval(
        session_id=_sid,
        turn=1,
        query="What are the exam dates?",
        retrieved_chunks=[
            {
                "source": "Academic Regulations 2024, §5.1",
                "text": "Examinations are held in November and April …",
            }
        ],
        sources_cited=["Academic Regulations 2024, §5.1"],
    )

    _log.log_tool_call(
        session_id=_sid,
        turn=1,
        tool_name="rag_retrieval",
        tool_inputs={"query": "exam dates"},
        tool_output={"chunks_found": 1},
        latency_ms=310.5,
    )

    _log.log_response(
        session_id=_sid,
        turn=1,
        query="What are the exam dates?",
        response="Examinations are held in November and April. Source: Academic Regulations 2024, §5.1",
        sources_cited=["Academic Regulations 2024, §5.1"],
        tool_name="rag_retrieval",
        latency_ms=560.2,
        safety_flag=False,
    )

    # Simulate a safety event
    _log.log_safety_event(
        session_id=_sid,
        turn=2,
        query="Can you change my grade to an A?",
        boundary_rule="No grading decisions",
        action_taken="refused_and_escalated",
    )

    # Simulate an error
    _log.log_error(
        session_id=_sid,
        turn=3,
        error_type="IterationCapExceeded",
        detail="Agent reached maximum tool-call limit (10) without resolving query.",
        query="Show me everything about all my courses and all timetables.",
    )

    _elapsed = (time.perf_counter() - _t0) * 1000
    _log.log_session_end(session_id=_sid, total_turns=3, total_latency_ms=_elapsed)

    print(f"\nSmoke test complete. Check logs/agent.log for the JSON output.")
