import json
import re

class Planner:
    """Decides the agent's next action using the model."""
    
    def __init__(self, model_client, tool_schemas, rag_available=True):
        self.model = model_client
        self.tool_schemas = tool_schemas
        self.rag_available = rag_available
    
    def plan_next_action(self, state):
        """
        Decide the next action based on current state.
        Returns: dict with 'action' and parameters
        """
        plan_prompt = self._build_plan_prompt(state)
        
        try:
            # Use model.generate() which supports both OpenAI and Gemini backends
            result = self.model.generate(
                system_prompt=plan_prompt,
                user_message="What is the next action? Respond with ONLY a JSON object.",
                temperature=0.1
            )
            raw = result["response"].strip()
            
            # Strip markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            
            decision = json.loads(raw)
            return decision
        except json.JSONDecodeError as e:
            print(f"[Planner] JSON parse error: {e} | raw={raw!r}")
            return {
                "action": "stop",
                "reason": "Planner could not parse decision"
            }
        except Exception as e:
            print(f"[Planner] Exception: {type(e).__name__}: {e}")
            return {
                "action": "stop",
                "reason": "Planner could not parse decision"
            }
    
    def _build_plan_prompt(self, state):
        history_summary = self._summarize_history(state)
        
        # Build context from retrieved documents
        rag_context = ""
        if state.retrieved_documents:
            last_rag = state.retrieved_documents[-1]
            rag_context = f"\nRETRIEVED CONTEXT (last RAG call):\n{last_rag.get('context', '')[:500]}"
        
        # Build tool results summary
        tool_context = ""
        if state.tool_results:
            last_tool = state.tool_results[-1]
            tool_context = f"\nLAST TOOL RESULT:\n{json.dumps(last_tool.get('result', {}))[:300]}"
        
        return f"""You are planning the next action for a bounded student support agent.

GOAL: {state.goal}

CURRENT STATE:
- Iteration: {state.iteration}/{state.max_iterations}
- Tool calls made: {state.tool_call_count}/3
- RAG calls made: {state.rag_call_count}/2
- Human needed: {state.human_needed}
{rag_context}
{tool_context}

HISTORY:
{history_summary}

AVAILABLE ACTIONS (respond with ONLY one of these JSON formats):

1. Search knowledge base:
{{"action": "rag_retrieve", "query": "your search query here"}}

2. Look up course info:
{{"action": "call_tool", "tool": "get_course_info", "arguments": {{"course_code": "BSE4104", "info_type": "prerequisites"}}}}

3. Create support ticket (requires human approval):
{{"action": "call_tool", "tool": "create_support_ticket", "arguments": {{"student_name": "Student", "issue_summary": "brief description", "priority": "medium", "category": "other"}}}}

4. Provide final answer:
{{"action": "answer", "text": "your complete answer to the student here"}}

5. Stop without answer:
{{"action": "stop", "reason": "explain why you cannot proceed"}}

DECISION RULES:
- If you need info from documents → rag_retrieve (max 2 times)
- If you need course prerequisites/credits/schedule → call_tool get_course_info
- If issue cannot be resolved with available info → call_tool create_support_ticket
- If you have enough information to answer → answer
- If goal is vague and 2+ iterations done → stop and ask for clarification
- NEVER repeat the same action with the same arguments
- If last tool call failed → try a different approach

Respond with ONLY a valid JSON object, no explanation, no markdown."""
    
    def _summarize_history(self, state):
        if not state.history:
            return "(no actions taken yet)"
        lines = []
        for step in state.history[-8:]:
            action = step["action"]
            data = step["data"]
            if isinstance(data, dict):
                data_str = json.dumps(data)[:120]
            else:
                data_str = str(data)[:120]
            lines.append(f"  [{action}] {data_str}")
        return "\n".join(lines)
