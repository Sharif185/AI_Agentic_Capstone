class StopConditions:
    """Evaluates whether the agent should stop."""
    
    def __init__(self, max_iterations=5, max_tool_calls=3, max_rag_calls=2):
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls
        self.max_rag_calls = max_rag_calls
    
    def should_stop(self, state):
        """
        Returns: tuple (should_stop: bool, reason: str)
        """
        if state.completed:
            return True, "goal_achieved"
        if state.iteration >= self.max_iterations:
            return True, "max_iterations_reached"
        if state.tool_call_count >= self.max_tool_calls:
            return True, "max_tool_calls_reached"
        if state.rag_call_count >= self.max_rag_calls:
            return True, "max_rag_calls_reached"
        if self._no_progress(state):
            return True, "no_progress_detected"
        if state.human_needed:
            return True, "human_handoff"
        return False, None
    
    def _no_progress(self, state):
        if len(state.history) < 4:
            return False
        # Get last 2 observe steps
        observe_steps = [h for h in state.history if h["action"] == "observe"]
        if len(observe_steps) < 2:
            return False
        last_two = observe_steps[-2:]
        return last_two[0]["data"] == last_two[1]["data"]
