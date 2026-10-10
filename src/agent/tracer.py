import json
import os
import uuid
from datetime import datetime, timezone


class Tracer:
    """
    Builds a structured, JSON-serializable execution trace for one agent
    run and saves it under evidence/traces/TRACE-<timestamp>-<suffix>.json.

    The brief's suggested filename format is TRACE-YYYYMMDDHHMMSS.json, but
    that has only one-second resolution — two agent runs in the same second
    (easy to hit, e.g. in a test loop) would silently overwrite each other's
    trace. A short random suffix is appended to guarantee uniqueness while
    keeping the readable timestamp prefix.
    """

    def __init__(self, goal, trace_dir="evidence/traces"):
        self.trace_dir = trace_dir
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        suffix = uuid.uuid4().hex[:6]
        self.trace_id = f"TRACE-{ts}-{suffix}"
        self._trace = {
            "trace_id": self.trace_id,
            "goal": goal,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "iterations": [],
            "tool_calls": [],
            "rag_calls": [],
            "human_approvals": [],
            "final_response": None,
            "stop_reason": None,
            "completed_at": None,
        }

    def record_iteration(self, iteration, plan, action_taken):
        """Record enough information about one iteration to reconstruct what happened."""
        self._trace["iterations"].append({
            "iteration": iteration,
            "plan": plan,
            "action_taken": action_taken,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_tool_call(self, tool, arguments, result):
        self._trace["tool_calls"].append({
            "tool": tool,
            "arguments": arguments,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_rag_call(self, query, number_of_results, sources):
        self._trace["rag_calls"].append({
            "query": query,
            "number_of_results": number_of_results,
            "sources": sources,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_approval(self, tool, arguments, approved):
        self._trace["human_approvals"].append({
            "tool": tool,
            "arguments": arguments,
            "approved": approved,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def finalize(self, final_response, stop_reason):
        self._trace["final_response"] = final_response
        self._trace["stop_reason"] = stop_reason
        self._trace["completed_at"] = datetime.now(timezone.utc).isoformat()

    def get_trace(self):
        """Return the current trace dict — callable mid-run or after finalize()."""
        return self._trace

    def save(self):
        """Write the trace to evidence/traces/<trace_id>.json and return the path."""
        os.makedirs(self.trace_dir, exist_ok=True)
        path = os.path.join(self.trace_dir, f"{self.trace_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._trace, f, indent=2, default=str)
        return path
