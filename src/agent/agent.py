from agent.state import AgentState
from agent.stop_conditions import StopConditions
from agent.tracer import Tracer

# Week 5's approved tool list (Section 8 of the brief). The agent refuses
# to call anything outside this set, even if the planner asks for it.
APPROVED_TOOLS = {"get_course_info", "create_support_ticket"}
AVAILABLE_ACTIONS = {"rag_retrieve", "call_tool", "answer", "stop"}

_GENERIC_STOP_MESSAGES = {
    "max_iterations_reached": "I've looked into this as far as I safely can right now. Let me connect you with a human who can help further.",
    "max_tool_calls_reached": "I've tried the available actions for this request. Let me connect you with a human who can help further.",
    "max_rag_calls_reached": "I wasn't able to find a clear answer in the documents I have access to. Let me connect you with a human who can help further.",
    "no_progress_detected": "I'm not finding new information to help with this. Could you give me a bit more detail, or I can connect you with a human?",
    "human_handoff": "This needs a human to review — I've noted the details for follow-up.",
}
_DEFAULT_STOP_MESSAGE = "I'm not able to resolve this safely right now. Let me connect you with a human who can help."


class StudentSupportAgent:
    """
    Bounded, goal-directed orchestrator implementing
    Sense -> Plan -> Act -> Observe -> Evaluate.

    Integrates ModelClient, RAGPipeline, ToolExecutor (which itself owns
    ApprovalController), Planner, StopConditions, Tracer, and AgentState.
    This class never bypasses ToolExecutor/ApprovalController, never calls
    a tool outside APPROVED_TOOLS, and never continues past the configured
    limits — those guarantees hold regardless of what the planner returns.
    """

    def __init__(self, model_client, rag_pipeline, tool_executor, planner,
                 max_iterations=5, max_tool_calls=3, max_rag_calls=2,
                 trace_dir="evidence/traces", memory_manager=None):
        # memory_manager is OPTIONAL (Week 6). With None the agent behaves exactly as in Week 5.
        self.memory = memory_manager
        self.model = model_client
        self.rag = rag_pipeline
        self.tool_executor = tool_executor
        self.planner = planner
        self.max_iterations = max_iterations
        self.trace_dir = trace_dir
        self.stop_conditions = StopConditions(
            max_iterations=max_iterations,
            max_tool_calls=max_tool_calls,
            max_rag_calls=max_rag_calls,
        )

    def run(self, goal, student_name="Student", user_id=None):
        """
        Run the bounded agent loop for one student goal.

        Returns {"response", "state", "trace_file", "iterations", "stop_reason"}.
        """
        state = AgentState(goal, max_iterations=self.max_iterations, student_name=student_name)
        state.memory_context = self._load_memory_context(user_id)
        tracer = Tracer(goal, trace_dir=self.trace_dir)

        while True:
            # 1. Check stop conditions — authoritative, overrides the planner
            should_stop, reason = self.stop_conditions.check(state)
            if should_stop:
                if not state.completed:
                    state.mark_complete(_GENERIC_STOP_MESSAGES.get(reason, _DEFAULT_STOP_MESSAGE), reason)
                break

            # 2. Increment iteration
            state.next_iteration()

            # 3. SENSE — the accumulated state itself is the sensed context;
            #    the planner is given the goal + history on every call.

            # 4. PLAN
            try:
                plan = self.planner.plan(state, AVAILABLE_ACTIONS)
            except Exception as e:
                plan = {"action": "stop", "action_input": {"response": _DEFAULT_STOP_MESSAGE}, "reasoning": f"planner_exception: {e}"}
            state.current_plan = plan
            state.add_step("plan", plan)

            # 5. ACT (+ 6. OBSERVE is recorded inside each _act_* helper)
            action = plan.get("action")
            action_input = plan.get("action_input", {}) or {}
            observation = self._act(action, action_input, state, tracer)

            # 7. EVALUATE
            if action == "answer":
                state.mark_complete(action_input.get("response", ""), "goal_achieved")
            elif action == "stop":
                reason = "human_handoff" if state.human_needed else "stop_requested"
                state.mark_complete(action_input.get("response", _DEFAULT_STOP_MESSAGE), reason)

            tracer.record_iteration(state.iteration, plan, {"action": action, "observation": observation})

            # 8. loop repeats; the top-of-loop check handles exit next pass

        tracer.finalize(state.final_response, state.stop_reason)
        trace_file = tracer.save()

        return {
            "response": state.final_response,
            "state": state.to_dict(),
            "trace_file": trace_file,
            "iterations": state.iteration,
            "stop_reason": state.stop_reason,
        }

    def _load_memory_context(self, user_id):
        """Remembered context for this student, or "" (no memory, no user_id, nothing stored,
        or any memory error). Memory is assistive: a failure here never stops the run."""
        if self.memory is None:
            return ""
        try:
            self.memory.record_turn()
            if not user_id:
                return ""
            return self.memory.get_memory_context(user_id) or ""
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # ACT helpers
    # ------------------------------------------------------------------

    def _act(self, action, action_input, state, tracer):
        if action == "rag_retrieve":
            return self._act_rag_retrieve(action_input, state, tracer)
        if action == "call_tool":
            return self._act_call_tool(action_input, state, tracer)
        if action in ("answer", "stop"):
            state.add_step(action, action_input)
            return action_input

        # Unknown/invalid action from the planner -> safe stop, never a crash
        state.add_step("stop", {"response": "unknown_action", "unknown_action": action})
        state.human_needed = True
        return {"error": f"Unknown action '{action}'"}

    def _act_rag_retrieve(self, action_input, state, tracer):
        query = action_input.get("query") or state.goal
        try:
            result = self.rag.query(query)
            state.record_rag_call(result)
            step_data = {
                "query": query,
                "num_results": len(result.get("retrieved_chunks", [])),
                "sources": result.get("sources", []),
                "context": result.get("context", ""),
                "success": True,
            }
        except Exception as e:
            step_data = {"query": query, "success": False, "error": str(e)}
            state.record_rag_call({"question": query, "error": str(e)})

        state.add_step("rag_retrieve", step_data)
        tracer.record_rag_call(query, step_data.get("num_results", 0), step_data.get("sources", []))
        return step_data

    def _act_call_tool(self, action_input, state, tracer):
        tool_name = action_input.get("tool_name")
        arguments = action_input.get("arguments", {}) or {}

        if tool_name not in APPROVED_TOOLS:
            result = {"success": False, "error": f"Tool '{tool_name}' is not in the approved tool list."}
        else:
            try:
                # ToolExecutor is the sole authority for execution + approval;
                # never bypassed or duplicated here.
                result = self.tool_executor.execute(tool_name, arguments)
            except Exception as e:
                result = {"success": False, "error": f"Tool execution failed unexpectedly: {e}"}

        state.record_tool_call(tool_name, arguments, result)
        state.add_step("call_tool", {"tool_name": tool_name, "arguments": arguments, "result": result})
        tracer.record_tool_call(tool_name, arguments, result)

        if "approved" in result:
            tracer.record_approval(tool_name, arguments, result["approved"])

        return result
