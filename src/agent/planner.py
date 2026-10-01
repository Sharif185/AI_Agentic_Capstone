import json
from ..models.model_client import ModelClient
 
class Planner:
    """Decides the agent's next action using the model."""
    
    def __init__(self, model_client, tool_schemas, rag_available=True):
        self.model = model_client
        self.tool_schemas = tool_schemas
        self.rag_available = rag_available
    
    def plan_next_action(self, state):
        """
        Decide the next action based on current state.
        
        Returns:
            dict with 'action' and 'parameters'
        """
        plan_prompt = self._build_plan_prompt(state)
        
        response = self.model.generate(
            system_prompt=plan_prompt,
            user_message="What is the next action?",
            temperature=0.1
        )
        
        try:
            decision = json.loads(response["response"])
            return decision
        except json.JSONDecodeError:
            # Fallback: return a stop action
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
            return "(no actions taken yet)"
        
        lines = []
        for step in state.history[-6:]:  # Last 6 steps
            action = step["action"]
            data = step["data"]
            if isinstance(data, dict):
                data_str = json.dumps(data)[:100]
            else:
                data_str = str(data)[:100]
            lines.append(f"  [{action}] {data_str}")
        
        return "\n".join(lines)