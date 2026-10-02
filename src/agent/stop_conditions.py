import json

# Actions whose repetition counts toward no-progress detection. Planning
# and terminal steps (plan/answer/stop) are excluded -- only repeated
# *information-gathering* actions (same query, same tool+args) indicate
# the agent is stuck.
_PROGRESS_TRACKED_ACTIONS = ("rag_retrieve", "call_tool")


class StopConditions:
    """
    Centralized, deterministic guardrails for the agent loop.

    The agent loop MUST call check(state) at the top of every iteration;
    if should_stop is True, the loop stops immediately regardless of what
    the planner wants. This is what prevents the agent from running
    indefinitely, bypassing approval, or exceeding Week 5's bounds.
    """

    def __init__(self, max_iterations=5, max_tool_calls=3, max_rag_calls=2):
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls
        self.max_rag_calls = max_rag_calls

    def check(self, state):
        """
        Returns (should_stop: bool, reason: str or None).
        reason is one of: goal_achieved, max_iterations_reached,
        max_tool_calls_reached, max_rag_calls_reached, no_progress_detected,
        human_handoff. reason is None only when should_stop is False.
        """
        if state.completed:
            return True, "goal_achieved" if not state.human_needed else state.stop_reason or "goal_achieved"

        if state.human_needed:
            return True, "human_handoff"

        if state.iteration >= self.max_iterations:
            return True, "max_iterations_reached"

        if state.tool_call_count >= self.max_tool_calls:
            return True, "max_tool_calls_reached"

        if state.rag_call_count >= self.max_rag_calls:
            return True, "max_rag_calls_reached"

        if self._no_progress(state):
            return True, "no_progress_detected"

        return False, None

    def _no_progress(self, state, window=2):
        """
        Detect repeated identical actions with identical arguments.
        Deterministic: looks only at the last `window` information-
        gathering steps (rag_retrieve / call_tool) in history and checks
        whether they are all the exact same action+arguments.
        """
        tracked = [s for s in state.history if s["action"] in _PROGRESS_TRACKED_ACTIONS]
        if len(tracked) < window:
            return False

        recent = tracked[-window:]
        signatures = {self._signature(step) for step in recent}
        return len(signatures) == 1

    @staticmethod
    def _signature(step):
        """A stable, hashable signature of a step's defining input (not its
        result/output), so re-running the SAME query/tool+args is detected
        even if the result happens to differ slightly."""
        action = step["action"]
        data = step["data"] or {}
        if action == "rag_retrieve":
            key = data.get("query")
        elif action == "call_tool":
            key = (data.get("tool_name"), json.dumps(data.get("arguments", {}), sort_keys=True, default=str))
        else:
            key = json.dumps(data, sort_keys=True, default=str)
        return (action, key)
