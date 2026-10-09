import json

PLANNING_PROMPT_TEMPLATE = """You are the planning module of a bounded university student-support agent.
Given the student's goal and everything done so far, decide the SINGLE next action.

STUDENT GOAL:
{goal}

AVAILABLE ACTIONS:
- rag_retrieve: search university documents. action_input: {{"query": "<search query>"}}
- call_tool: call one approved tool. action_input: {{"tool_name": "get_course_info"|"create_support_ticket", "arguments": {{...}}}}
- answer: give the final answer now, if you have enough information. action_input: {{"response": "<final answer text>"}}
- stop: stop and hand off to a human, or ask the student to clarify, if the request is too vague or cannot be resolved. action_input: {{"response": "<message to the student>"}}

HISTORY SO FAR (most recent last):
{history}

RULES:
- Only call_tool with: get_course_info, create_support_ticket.
- Do NOT repeat a rag_retrieve query or a call_tool (tool_name + arguments) that already appears in the history above.
- If a tool lookup failed (course not found) and a RAG retrieval also found nothing relevant, the next step is usually call_tool with create_support_ticket, summarizing the issue.
- If the goal is vague (e.g. "I have a problem") and the history gives you nothing to act on, choose stop and ask a clarifying question rather than guessing.
- Respond with ONLY a single JSON object, no other text, no markdown fences, in exactly this shape:
{{"action": "rag_retrieve|call_tool|answer|stop", "action_input": {{...}}, "reasoning": "<one short sentence>"}}
"""

_FALLBACK_MESSAGE = "I'm not able to make progress on this request safely. Let me connect you with a human who can help."


class Planner:
    """
    MINIMAL STAND-IN PLANNER.

    No src/agent/planner.py existed anywhere in the repository before this
    Week 5 integration, even though the brief assumes the AI Engineering
    Lead already owns one. This implementation exists purely so the
    Sense -> Plan -> Act -> Observe -> Evaluate loop is testable end-to-end;
    it is intentionally simple (one LLM call per planning step, strict JSON
    output, safe fallback on any parse/model failure).

    agent.py only depends on the plan(state, available_actions) interface
    below -- whoever owns prompt/planning design can replace this file's
    internals (a smarter prompt, few-shot examples, a different model call
    shape, etc.) without touching agent.py, as long as plan() keeps
    returning {"action", "action_input", "reasoning"}.
    """

    def __init__(self, model_client):
        self.model = model_client

    def plan(self, state, available_actions):
        """
        Returns {"action": str, "action_input": dict, "reasoning": str}.
        Never raises — on any failure (model error, bad/unparseable JSON,
        invalid action name), falls back to a safe "stop" decision rather
        than crashing the agent loop.
        """
        prompt = PLANNING_PROMPT_TEMPLATE.format(
            goal=state.goal,
            history=self._format_history(state),
        )

        try:
            result = self.model.generate(
                system_prompt="You respond with valid JSON only, nothing else — no markdown, no commentary.",
                user_message=prompt,
                temperature=0.0,
                disable_thinking=True,
            )
            raw = (result.get("response") or "").strip()
            decision = self._parse_json(raw)
        except Exception as e:
            return {"action": "stop", "action_input": {"response": _FALLBACK_MESSAGE}, "reasoning": f"planner_error: {e}"}

        if not decision or decision.get("action") not in available_actions:
            # Keep a truncated snippet of what the model actually returned,
            # so a parse failure is diagnosable from the trace alone instead
            # of needing to reproduce it live.
            snippet = raw[:300].replace("\n", " ") if raw else "(empty response)"
            return {
                "action": "stop",
                "reason": "Planner could not parse decision",
                "raw_response": response["response"]
            }
    
    def _build_plan_prompt(self, state):
        """Build the planning prompt."""
        history_summary = self._summarize_history(state)
        
        return f"""You are planning the next action for a student support agent.
 
GOAL: {state.goal}
 
CURRENT STATE:
- Iteration: {state.iteration}/{state.max_iterations}
- Tool calls made: {state.tool_call_count}
- RAG calls made: {state.rag_call_count}
- Human needed: {state.human_needed}
 
HISTORY:
{history_summary}
 
AVAILABLE ACTIONS:
1. {{"action": "rag_retrieve", "query": "..."}}
   - Search the knowledge base for relevant documents
   - Use when you need information from university documents
 
2. {{"action": "call_tool", "tool": "get_course_info", "arguments": {{"course_code": "...", "info_type": "..."}}}}
   - Look up structured course information
   - Use when you need prerequisites, credits, schedule, or description
 
3. {{"action": "call_tool", "tool": "create_support_ticket", "arguments": {{"student_name": "...", "issue_summary": "...", "priority": "..."}}}}
   - Create a support ticket (requires human approval)
   - Use when the issue cannot be resolved with available information
 
4. {{"action": "answer", "text": "..."}}
   - Provide the final answer to the student
   - Use when you have enough information to resolve the issue
 
5. {{"action": "stop", "reason": "..."}}
   - Stop the loop without a final answer
   - Use when you cannot make progress
 
RULES:
- Do NOT repeat an action you've already taken with the same arguments
- Do NOT exceed {{state.max_iterations}} total iterations
- If 2+ actions have failed, consider answering or stopping
- If the issue needs human help, create a ticket
- If you have enough information, provide the answer
 
Respond with ONLY a JSON object, no other text.
 
DECISION:"""
    
    def _summarize_history(self, state):
        """Create a readable summary of the history."""
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
