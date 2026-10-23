import time

from agent.state import AgentState
from agent.stop_conditions import StopConditions
from agent.tracer import Tracer

# Week 5's approved tool list. Kept for backwards compatibility; the
# authoritative check is now GuardrailManager.check_tool() (which includes
# check_ticket_status per the Week 7 spec).
APPROVED_TOOLS = {"get_course_info", "create_support_ticket", "check_ticket_status"}

AVAILABLE_ACTIONS = {"rag_retrieve", "call_tool", "answer", "stop"}

_GENERIC_STOP_MESSAGES = {
    "max_iterations_reached": "I've looked into this as far as I safely can right now. Let me connect you with a human who can help further.",
    "max_iterations": "I've looked into this as far as I safely can right now. Let me connect you with a human who can help further.",
    "max_tool_calls_reached": "I've tried the available actions for this request. Let me connect you with a human who can help further.",
    "max_tool_calls": "I've tried the available actions for this request. Let me connect you with a human who can help further.",
    "max_rag_calls_reached": "I wasn't able to find a clear answer in the documents I have access to. Let me connect you with a human who can help further.",
    "max_rag_calls": "I wasn't able to find a clear answer in the documents I have access to. Let me connect you with a human who can help further.",
    "rate_limit": "I've reached the limit on that action for this request. Let me connect you with a human who can help further.",
    "not_in_allowlist": "I'm not able to perform that action. Let me connect you with a human who can help further.",
    "no_progress_detected": "I'm not finding new information to help with this. Could you give me a bit more detail, or I can connect you with a human?",
    "human_handoff": "This needs a human to review — I've noted the details for follow-up.",
}
_DEFAULT_STOP_MESSAGE = "I'm not able to resolve this safely right now. Let me connect you with a human who can help."

_REFUSAL_MESSAGES = {
    "refuse_injection": (
        "I'm here to help with university-related questions. "
        "How can I assist you with your studies?"
    ),
    "refuse_prohibited": (
        "I'm not able to help with that. Please contact the relevant office directly."
    ),
    "reject_empty": "I didn't receive a question. Could you please rephrase?",
    "reject_too_long": "Your message is too long — please shorten it and try again.",
    "reject_error": "Something went wrong processing your request. Please try again.",
}
_DEFAULT_REFUSAL = "I'm sorry, I can't process that request."


class StudentSupportAgent:
    """
    Bounded, goal-directed orchestrator implementing
    Sense -> Plan -> Act -> Observe -> Evaluate.

    Integrates ModelClient, RAGPipeline, ToolExecutor (which itself owns
    ApprovalController), Planner, StopConditions, Tracer, AgentState, and
    (Week 7) an AgentLogger + GuardrailManager.

    Week 7 enforcement guarantees, in application code — not just in the
    system prompt:

      * Input validation runs BEFORE any model, RAG, memory or tool call.
      * The iteration limiter is checked at the top of every loop pass.
      * Every tool call is checked against the allow-list and its per-tool
        rate limit BEFORE the executor is invoked.
      * Every RAG call is checked against the per-run RAG cap BEFORE the
        pipeline is invoked.
      * The final response is validated (output validator) before return.

    The class never bypasses ToolExecutor/ApprovalController and never
    calls a tool outside the guardrail allow-list, regardless of what the
    planner returns.
    """

    def __init__(
        self,
        model_client,
        rag_pipeline,
        tool_executor,
        planner,
        max_iterations=5,
        max_tool_calls=3,
        max_rag_calls=2,
        trace_dir="evidence/traces",
        memory_manager=None,
        logger=None,
        guardrails=None,
    ):
        # Lazy import so a project without the Week 7 modules still imports
        # this file (e.g. running Week 5/6 tests standalone).
        try:
            from observability.logger import AgentLogger  # noqa: WPS433
        except ImportError:  # pragma: no cover
            try:
                from src.observability.logger import AgentLogger  # type: ignore
            except ImportError:
                AgentLogger = None  # type: ignore

        try:
            from guardrails.guardrail_manager import GuardrailManager  # noqa: WPS433
        except ImportError:  # pragma: no cover
            try:
                from src.guardrails.guardrail_manager import GuardrailManager  # type: ignore
            except ImportError:
                GuardrailManager = None  # type: ignore

        # memory_manager is OPTIONAL (Week 6). With None the agent behaves
        # exactly as in Week 5.
        self.memory = memory_manager
        self.model = model_client
        self.rag = rag_pipeline
        self.tool_executor = tool_executor
        self.planner = planner
        self.max_iterations = max_iterations
        self.trace_dir = trace_dir

        # ---------- Week 7: logger + guardrails ----------
        if logger is not None:
            self.logger = logger
        elif AgentLogger is not None:
            self.logger = AgentLogger(log_dir="logs")
        else:
            self.logger = None  # tests without the Week 7 logger still run

        if guardrails is not None:
            self.guardrails = guardrails
        elif GuardrailManager is not None and self.logger is not None:
            self.guardrails = GuardrailManager(
                logger=self.logger,
                max_iterations=max_iterations,
                max_tool_calls=max_tool_calls,
                max_rag_calls=max_rag_calls,
            )
        elif GuardrailManager is not None:
            self.guardrails = GuardrailManager(
                max_iterations=max_iterations,
                max_tool_calls=max_tool_calls,
                max_rag_calls=max_rag_calls,
            )
        else:
            self.guardrails = None  # tests without the Week 7 guardrails still run

        # Inject the shared logger into collaborators that support it.
        self._inject_logger(self.planner)
        self._inject_logger(self.rag)
        self._inject_logger(self.tool_executor)

        self.stop_conditions = StopConditions(
            max_iterations=max_iterations,
            max_tool_calls=max_tool_calls,
            max_rag_calls=max_rag_calls,
        )

    # ------------------------------------------------------------------ #
    # small internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _inject_logger(component):
        if component is None:
            return
        if getattr(component, "logger", None) is None:
            try:
                component.logger = StudentSupportAgent._pending_logger  # set below
            except Exception:
                pass

    @staticmethod
    def _safe_get(obj, *names, default=0):
        """Return the first present attribute/counter from obj, else default."""
        for name in names:
            if isinstance(obj, dict):
                if name not in obj:
                    continue
                value = obj[name]
            else:
                if not hasattr(obj, name):
                    continue
                value = getattr(obj, name)
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                return len(value)
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        return default

    def _guardrail_state(self, state):
        """A small dict-view of the real agent state for the IterationLimiter.

        The limiter reads iterations/tool_calls/rag_calls; the agent state
        uses different names and hides counters behind record_* methods, so
        we normalise here rather than coupling the limiter to AgentState.
        """
        return {
            "iterations": self._safe_get(state, "iteration", "iterations", "iteration_count"),
            "tool_calls": self._safe_get(
                state, "tool_call_count", "tool_calls", "tool_call_history"
            ),
            "rag_calls": self._safe_get(
                state, "rag_call_count", "rag_calls", "rag_call_history"
            ),
        }

    @staticmethod
    def _refusal_for(action):
        return _REFUSAL_MESSAGES.get(action, _DEFAULT_REFUSAL)

    def _log_iteration(self, iteration, action, data=None, status=None):
        if self.logger is None:
            return
        try:
            self.logger.log_agent_iteration(iteration, action, data, status=status)
        except Exception:
            pass

    def _log_guardrail(self, guardrail, input_data, reason, decision=None):
        if self.logger is None:
            return
        try:
            self.logger.log_guardrail_trigger(guardrail, input_data, reason, decision=decision)
        except Exception:
            pass

    def _log_error(self, error_type, message, context=None):
        if self.logger is None:
            return
        try:
            self.logger.log_error(error_type, message, context)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # main loop
    # ------------------------------------------------------------------ #
    def run(self, goal, student_name="Student", user_id=None):
        """
        Run the bounded agent loop for one student goal.

        Returns {"response", "state", "trace_file", "iterations", "stop_reason"}.
        """
        # Reset per-run guardrail counters (tool rate limits, trigger counts).
        if self.guardrails is not None:
            try:
                self.guardrails.reset()
            except Exception:
                pass

        self._log_iteration(0, "start", {"goal": goal[:120] if isinstance(goal, str) else goal})

        # ============================================================== #
        # GUARDRAIL 1 — input validation (before any model / RAG / tool) #
        # ============================================================== #
        if self.guardrails is not None:
            try:
                input_check = self.guardrails.validate_input(goal)
            except Exception as exc:
                self._log_error("input_guardrail_error", str(exc), goal)
                input_check = {"valid": True, "action": "allow", "reason": None}

            if not input_check.get("valid"):
                reason = input_check.get("reason", "refused")
                action = input_check.get("action", "refuse_prohibited")
                self._log_guardrail(
                    "input_validator",
                    goal[:100] if isinstance(goal, str) else str(goal)[:100],
                    reason,
                    decision=action,
                )
                self._log_iteration(0, "stop", {"reason": reason}, status="input_refused")
                return {
                    "response": self._refusal_for(action),
                    "state": None,
                    "trace_file": None,
                    "iterations": 0,
                    "stop_reason": "input_refused",
                }

        # -------------------- normal run -------------------- #
        state = AgentState(goal, max_iterations=self.max_iterations, student_name=student_name)
        state.memory_context = self._load_memory_context(user_id)
        tracer = Tracer(goal, trace_dir=self.trace_dir)

        while True:
            # ============================================================== #
            # GUARDRAIL 4 — iteration / tool / rag limits (authoritative)    #
            # ============================================================== #
            if self.guardrails is not None:
                try:
                    limit_check = self.guardrails.check_iteration(self._guardrail_state(state))
                except Exception as exc:
                    self._log_error("iteration_guardrail_error", str(exc))
                    limit_check = {"allowed": True, "reason": None}

                if not limit_check.get("allowed"):
                    reason = limit_check.get("reason", "max_iterations")
                    if not state.completed:
                        state.mark_complete(
                            _GENERIC_STOP_MESSAGES.get(reason, _DEFAULT_STOP_MESSAGE),
                            reason,
                        )
                    break

            # Legacy StopConditions — kept for no-progress detection and
            # any additional checks the Week 5/6 layer already performs.
            should_stop, reason = self.stop_conditions.check(state)
            if should_stop:
                if not state.completed:
                    state.mark_complete(
                        _GENERIC_STOP_MESSAGES.get(reason, _DEFAULT_STOP_MESSAGE),
                        reason,
                    )
                break

            # 2. Increment iteration
            state.next_iteration()
            self._log_iteration(state.iteration, "sense", {"goal": state.goal[:100]})

            # 3. SENSE — the accumulated state itself is the sensed context.

            # 4. PLAN
            plan_start = time.time()
            try:
                plan = self.planner.plan(state, AVAILABLE_ACTIONS)
                plan_latency_ms = (time.time() - plan_start) * 1000.0
                if self.logger is not None and not getattr(self.planner, "logs_model_calls", False):
                    # Fallback model-call log if the planner doesn't log itself.
                    try:
                        self.logger.log_model_call(
                            model=getattr(self.model, "model_name", "unknown"),
                            prompt_preview=f"goal={state.goal!r}; iteration={state.iteration}",
                            response_preview=str(plan),
                            latency_ms=plan_latency_ms,
                            success=True,
                        )
                    except Exception:
                        pass
            except Exception as e:
                plan_latency_ms = (time.time() - plan_start) * 1000.0
                self._log_error("planner_exception", str(e), state.goal)
                if self.logger is not None and not getattr(self.planner, "logs_model_calls", False):
                    try:
                        self.logger.log_model_call(
                            model=getattr(self.model, "model_name", "unknown"),
                            prompt_preview=f"goal={state.goal!r}",
                            response_preview="",
                            latency_ms=plan_latency_ms,
                            success=False,
                            error=str(e),
                        )
                    except Exception:
                        pass
                plan = {
                    "action": "stop",
                    "action_input": {"response": _DEFAULT_STOP_MESSAGE},
                    "reasoning": f"planner_exception: {e}",
                }

            state.current_plan = plan
            state.add_step("plan", plan)
            self._log_iteration(state.iteration, "plan", plan)

            # 5. ACT (+ 6. OBSERVE is recorded inside each _act_* helper)
            action = plan.get("action")
            action_input = plan.get("action_input", {}) or {}
            observation = self._act(action, action_input, state, tracer)
            self._log_iteration(state.iteration, "observe", observation)

            # 7. EVALUATE
            if action == "answer":
                raw_response = action_input.get("response", "") or ""
                # ============================================================== #
                # GUARDRAIL 3 — output validation on the final answer            #
                # ============================================================== #
                if self.guardrails is not None:
                    context_used = bool(
                        getattr(state, "rag_call_count", 0)
                        or getattr(state, "rag_calls", None)
                        or getattr(state, "sources", None)
                    )
                    sources = getattr(state, "sources", None) or []
                    try:
                        out_check = self.guardrails.validate_output(
                            raw_response, context_used=context_used, sources=sources
                        )
                    except Exception as exc:
                        self._log_error("output_guardrail_error", str(exc))
                        out_check = {"valid": True, "warnings": [], "action": "allow"}
                    if not out_check.get("valid"):
                        self._log_guardrail(
                            "output_validator",
                            raw_response[:100],
                            "; ".join(out_check.get("warnings", [])),
                            decision=out_check.get("action", "flag_ungrounded"),
                        )
                state.mark_complete(raw_response, "goal_achieved")
            elif action == "stop":
                reason = "human_handoff" if state.human_needed else "stop_requested"
                state.mark_complete(action_input.get("response", _DEFAULT_STOP_MESSAGE), reason)

            tracer.record_iteration(
                state.iteration, plan, {"action": action, "observation": observation}
            )

            # 8. loop repeats; the top-of-loop checks handle exit next pass

        if self.logger is not None:
            try:
                self.logger.log_agent_stop(
                    state.stop_reason or "unknown",
                    getattr(state, "iteration", 0),
                    self._safe_get(state, "tool_call_count", "tool_calls", "tool_call_history"),
                    self._safe_get(state, "rag_call_count", "rag_calls", "rag_call_history"),
                )
            except Exception:
                pass

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

    # ------------------------------------------------------------------ #
    # ACT helpers
    # ------------------------------------------------------------------ #
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
        self._log_error("unknown_action", f"Planner returned unknown action: {action!r}")
        return {"error": f"Unknown action '{action}'"}

    def _act_rag_retrieve(self, action_input, state, tracer):
        query = action_input.get("query") or state.goal

        # ============================================================== #
        # GUARDRAIL 4b — RAG cap (checked BEFORE invoking the pipeline)  #
        # ============================================================== #
        if self.guardrails is not None:
            try:
                rag_check = self.guardrails.check_rag(self._guardrail_state(state))
            except Exception as exc:
                self._log_error("rag_guardrail_error", str(exc))
                rag_check = {"allowed": True, "reason": None}
            if not rag_check.get("allowed"):
                reason = rag_check.get("reason", "max_rag_calls")
                self._log_guardrail("rag_call_limit", query[:100], reason, decision="block")
                step_data = {"query": query, "success": False, "error": reason}
                state.add_step("rag_retrieve", step_data)
                tracer.record_rag_call(query, 0, [])
                # Force a safe stop: mark complete with a human-handoff message.
                state.human_needed = True
                state.mark_complete(
                    _GENERIC_STOP_MESSAGES.get(reason, _DEFAULT_STOP_MESSAGE), reason
                )
                return step_data

        start = time.time()
        try:
            result = self.rag.query(query)
            latency_ms = (time.time() - start) * 1000.0
            state.record_rag_call(result)
            step_data = {
                "query": query,
                "num_results": len(result.get("retrieved_chunks", [])),
                "sources": result.get("sources", []),
                "context": result.get("context", ""),
                "success": True,
                "latency_ms": latency_ms,
            }
            # Fallback RAG log if the pipeline doesn't log itself.
            if self.logger is not None and not getattr(self.rag, "logs_retrievals", False):
                try:
                    self.logger.log_rag_retrieval(
                        query=query,
                        num_results=step_data["num_results"],
                        sources=step_data["sources"],
                        latency_ms=latency_ms,
                        success=True,
                    )
                except Exception:
                    pass
        except Exception as e:
            latency_ms = (time.time() - start) * 1000.0
            step_data = {"query": query, "success": False, "error": str(e)}
            state.record_rag_call({"question": query, "error": str(e)})
            self._log_error("rag_exception", str(e), query)
            if self.logger is not None and not getattr(self.rag, "logs_retrievals", False):
                try:
                    self.logger.log_rag_retrieval(
                        query=query,
                        num_results=0,
                        sources=[],
                        latency_ms=latency_ms,
                        success=False,
                        error=str(e),
                    )
                except Exception:
                    pass

        state.add_step("rag_retrieve", step_data)
        tracer.record_rag_call(
            query, step_data.get("num_results", 0), step_data.get("sources", [])
        )
        return step_data

    def _act_call_tool(self, action_input, state, tracer):
        tool_name = action_input.get("tool_name")
        arguments = action_input.get("arguments", {}) or {}

        # ============================================================== #
        # GUARDRAIL 4a — tool allow-list + per-tool rate limit           #
        # (checked BEFORE handing off to ToolExecutor)                   #
        # ============================================================== #
        tool_check = {"allowed": True, "requires_approval": False}
        if self.guardrails is not None:
            try:
                tool_check = self.guardrails.check_tool(tool_name)
            except Exception as exc:
                self._log_error("tool_guardrail_error", str(exc), tool_name)
                tool_check = {"allowed": True, "requires_approval": False}

            if not tool_check.get("allowed"):
                reason = tool_check.get("reason", "not_in_allowlist")
                self._log_guardrail("tool_allowlist", tool_name, reason, decision="block")
                result = {
                    "success": False,
                    "error": f"Tool '{tool_name}' blocked by guardrail: {reason}.",
                }
                state.record_tool_call(tool_name, arguments, result)
                state.add_step(
                    "call_tool",
                    {"tool_name": tool_name, "arguments": arguments, "result": result},
                )
                tracer.record_tool_call(tool_name, arguments, result)
                # Rate-limit is a per-tool ceiling; not fatal by itself, but
                # block further attempts of the same tool this run.
                return result
        else:
            # No guardrails configured — fall back to the module-level set.
            if tool_name not in APPROVED_TOOLS:
                result = {
                    "success": False,
                    "error": f"Tool '{tool_name}' is not in the approved tool list.",
                }
                state.record_tool_call(tool_name, arguments, result)
                state.add_step(
                    "call_tool",
                    {"tool_name": tool_name, "arguments": arguments, "result": result},
                )
                tracer.record_tool_call(tool_name, arguments, result)
                return result

        # -------------------- execution -------------------- #
        start = time.time()
        try:
            # ToolExecutor is the sole authority for execution + approval;
            # never bypassed or duplicated here.
            result = self.tool_executor.execute(tool_name, arguments)
        except Exception as e:
            result = {"success": False, "error": f"Tool execution failed unexpectedly: {e}"}
            self._log_error("tool_exception", str(e), tool_name)
        latency_ms = (time.time() - start) * 1000.0

        # Fallback tool-call log if the executor doesn't log itself.
        if self.logger is not None and not getattr(self.tool_executor, "logs_tool_calls", False):
            try:
                self.logger.log_tool_call(
                    tool_name=tool_name,
                    arguments=arguments,
                    success=bool(result.get("success", False)),
                    result_preview=result.get("result") if isinstance(result, dict) else result,
                    latency_ms=latency_ms,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            except Exception:
                pass

        state.record_tool_call(tool_name, arguments, result)
        state.add_step(
            "call_tool",
            {"tool_name": tool_name, "arguments": arguments, "result": result},
        )
        tracer.record_tool_call(tool_name, arguments, result)

        if isinstance(result, dict) and "approved" in result:
            tracer.record_approval(tool_name, arguments, result["approved"])
            if self.logger is not None and not getattr(
                self.tool_executor, "logs_approvals", False
            ):
                try:
                    self.logger.log_approval(
                        tool_name=tool_name,
                        arguments=arguments,
                        approved=bool(result.get("approved")),
                        mode=getattr(self.tool_executor, "approval_mode", "unknown"),
                    )
                except Exception:
                    pass

        return result