import json
import time

try:
    from observability.logger import AgentLogger  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from src.observability.logger import AgentLogger  # type: ignore
    except ImportError:
        AgentLogger = None  # type: ignore


PLANNING_PROMPT_TEMPLATE = """You are the planning module of a bounded university student-support agent.
Given the student's goal and everything done so far, decide the SINGLE next action.

STUDENT GOAL:
{goal}

AVAILABLE ACTIONS:
- rag_retrieve: search university documents. action_input: {{"query": "<search query>"}}
- call_tool: call one approved tool. action_input: {{"tool_name": "get_course_info"|"create_support_ticket"|"check_ticket_status", "arguments": {{...}}}}
- answer: give the final answer now, if you have enough information. action_input: {{"response": "<final answer text>"}}
- stop: stop and hand off to a human, or ask the student to clarify, if the request is too vague or cannot be resolved. action_input: {{"response": "<message to the student>"}}

{memory_section}HISTORY SO FAR (most recent last):
{history}

RULES:
- Only call_tool with: get_course_info, create_support_ticket, check_ticket_status.
- Do NOT repeat a rag_retrieve query or a call_tool (tool_name + arguments) that already appears in the history above.
- If a tool lookup failed (course not found) and a RAG retrieval also found nothing relevant, the next step is usually call_tool with create_support_ticket, summarizing the issue.
- If the goal is vague (e.g. "I have a problem") and the history gives you nothing to act on, choose stop and ask a clarifying question rather than guessing.
- Respond with ONLY a single JSON object, no other text, no markdown fences, in exactly this shape:
{{"action": "rag_retrieve|call_tool|answer|stop", "action_input": {{...}}, "reasoning": "<one short sentence>"}}
"""

_FALLBACK_MESSAGE = "I'm not able to make progress on this request safely. Let me connect you with a human who can help."

_PREVIEW_LEN = 200


class Planner:
    """
    Bounded planner.

    Interface contract with agent.py:
        plan(state, available_actions) ->
            {"action": str, "action_input": dict, "reasoning": str}
    Never raises. On any failure (model error, bad JSON, invalid action
    name) it falls back to a safe "stop" decision.

    Week 7 change: this planner now logs a model_call event for every
    planning step (model id, prompt/response preview, tokens if available,
    latency, success). Setting `logs_model_calls = True` tells agent.py
    not to emit a duplicate fallback log.
    """

    # Signals to AgentLogger-aware callers (agent.py) that this planner
    # already emits its own model_call events — no fallback needed.
    logs_model_calls = True

    def __init__(self, model_client, logger=None):
        self.model = model_client
        if logger is not None:
            self.logger = logger
        elif AgentLogger is not None:
            self.logger = AgentLogger(log_dir="logs")
        else:
            self.logger = None

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def plan(self, state, available_actions):
        prompt = PLANNING_PROMPT_TEMPLATE.format(
            goal=state.goal,
            history=self._format_history(state),
            memory_section=self._format_memory(state),
        )
        user_message = prompt  # kept separate so the log preview stays stable

        start = time.time()
        raw = ""
        try:
            result = self.model.generate(
                system_prompt=(
                    "You respond with valid JSON only, nothing else — "
                    "no markdown, no commentary."
                ),
                user_message=user_message,
                temperature=0.0,
                disable_thinking=True,
            )
            latency_ms = (time.time() - start) * 1000.0

            if isinstance(result, dict):
                raw = (result.get("response") or "").strip()
                usage = result.get("usage") or {}
            else:
                raw = (str(result) or "").strip()
                usage = {}

            self._log_model_call(
                prompt=prompt,
                response=raw,
                latency_ms=latency_ms,
                usage=usage,
                success=True,
                error=None,
            )

            decision = self._parse_json(raw)

        except Exception as e:
            latency_ms = (time.time() - start) * 1000.0
            self._log_model_call(
                prompt=prompt,
                response=raw,
                latency_ms=latency_ms,
                usage={},
                success=False,
                error=str(e),
            )
            return {
                "action": "stop",
                "action_input": {"response": _FALLBACK_MESSAGE},
                "reasoning": f"planner_error: {e}",
            }

        if not decision or decision.get("action") not in available_actions:
            snippet = raw[:300].replace("\n", " ") if raw else "(empty response)"
            return {
                "action": "stop",
                "reason": "Planner could not parse decision",
                "raw_response": response["response"]
            }

        decision.setdefault("action_input", {})
        decision.setdefault("reasoning", "")
        return decision

    # ------------------------------------------------------------------ #
    # logging helpers
    # ------------------------------------------------------------------ #
    def _log_model_call(self, prompt, response, latency_ms, usage, success, error=None):
        if self.logger is None:
            return
        try:
            self.logger.log_model_call(
                model=self._model_name(),
                prompt_preview=prompt[:_PREVIEW_LEN],
                response_preview=(response or "")[:_PREVIEW_LEN],
                input_tokens=usage.get("prompt_tokens") or usage.get("input_tokens"),
                output_tokens=usage.get("completion_tokens") or usage.get("output_tokens"),
                latency_ms=latency_ms,
                success=success,
                error=error,
            )
        except Exception:
            # Logging must never break planning.
            pass

    def _model_name(self):
        for attr in ("model_name", "model_id", "name"):
            value = getattr(self.model, attr, None)
            if isinstance(value, str) and value:
                return value
        return "unknown"

    # ------------------------------------------------------------------ #
    # history / memory formatting (unchanged)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _format_memory(state):
        """MEMORY CONTEXT block, or "" when empty. It is background only: the student's
        current goal and the rules below always take precedence over it."""
        memory = getattr(state, "memory_context", "") or ""
        if not memory.strip():
            return ""
        return (
            "MEMORY CONTEXT (remembered from earlier sessions; background only - the current goal "
            "above takes precedence, and do not assume the current issue is the same as a prior one "
            "without confirming with the student):\n" + memory.strip() + "\n\n"
        )

    @staticmethod
    def _format_history(state, max_entries=10):
        if not state.history:
            return "(nothing yet)"
        lines = []
        for step in state.history[-max_entries:]:
            summary = json.dumps(step["data"], default=str)[:300]
            lines.append(f"- iteration {step['iteration']}: {step['action']} -> {summary}")
        return "\n".join(lines)

    @staticmethod
    def _parse_json(raw):
        """
        Extract and parse the first balanced top-level {...} object in raw.
        Used instead of a greedy regex because a greedy '\\{.*\\}' match can
        span from the FIRST '{' to the LAST '}' in the whole response --
        if the model adds any trailing commentary or a second brace
        anywhere, that silently grabs the wrong (unparseable) span. A
        balanced-brace scan finds the exact matching object regardless of
        what surrounds it.
        """
        if not raw:
            return None

        start = raw.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(raw)):
            ch = raw[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = raw[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        return None
        return None