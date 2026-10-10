from datetime import datetime, timezone


class AgentState:
    """
    Tracks the complete state of one agent execution (one student goal)
    across iterations of the Sense -> Plan -> Act -> Observe -> Evaluate
    loop.

    Deliberately stores only what's needed to reason about and trace the
    run: the goal text, counters, and a structured history. It does not
    store real student records, grades, or any sensitive personal data —
    `student_name` is the only identifying field, and it's whatever the
    caller passes in (a demo name in testing).
    """

    def __init__(self, goal, max_iterations=5, student_name="Student"):
        self.goal = goal
        self.student_name = student_name
        self.iteration = 0
        self.max_iterations = max_iterations
        self.history = []               # every recorded step (plan, rag_retrieve, call_tool, answer, stop)
        self.retrieved_documents = []   # accumulated RAG results across iterations
        self.tool_results = []          # accumulated tool call results
        self.current_plan = None        # most recent planner decision
        self.completed = False
        self.human_needed = False
        self.final_response = None
        self.stop_reason = None
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.tool_call_count = 0
        self.rag_call_count = 0
        self.memory_context = ""        # remembered case history (read-only context; set by the agent when memory is enabled)

    def add_step(self, action, data):
        """
        Record a significant agent action: current iteration, action type,
        action data/result, and a timestamp. Returns the recorded step.
        """
        step = {
            "iteration": self.iteration,
            "action": action,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.history.append(step)
        return step

    def next_iteration(self):
        """Increment the iteration counter safely and return the new value."""
        self.iteration += 1
        return self.iteration

    def record_rag_call(self, rag_result):
        """Increment the RAG counter and store the retrieval result."""
        self.rag_call_count += 1
        self.retrieved_documents.append(rag_result)

    def record_tool_call(self, tool_name, arguments, result):
        """
        Increment the tool-call counter, store the result, and flag
        human_needed if the result represents a denied approval.
        """
        self.tool_call_count += 1
        self.tool_results.append({"tool": tool_name, "arguments": arguments, "result": result})
        if result.get("approved") is False:
            self.human_needed = True

    def mark_complete(self, response, reason):
        """Mark the agent as completed and store the final response + stop reason."""
        self.completed = True
        self.final_response = response
        self.stop_reason = reason

    def to_dict(self):
        """Return a JSON-serializable representation of the state."""
        return {
            "goal": self.goal,
            "student_name": self.student_name,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "history": self.history,
            "retrieved_documents": self.retrieved_documents,
            "tool_results": self.tool_results,
            "current_plan": self.current_plan,
            "completed": self.completed,
            "human_needed": self.human_needed,
            "final_response": self.final_response,
            "stop_reason": self.stop_reason,
            "started_at": self.started_at,
            "tool_call_count": self.tool_call_count,
            "rag_call_count": self.rag_call_count,
            "memory_context": self.memory_context,
        }
