import json
import os
from .state import AgentState
from .planner import Planner
from .stop_conditions import StopConditions
from .tracer import Tracer

class StudentSupportAgent:
    """Bounded, goal-directed agent for student support."""
    
    def __init__(self, model_client, rag_pipeline, tool_executor,
                 max_iterations=5, max_tool_calls=3, max_rag_calls=2,
                 trace_output_dir=None):
        self.model = model_client
        self.rag = rag_pipeline
        self.executor = tool_executor
        self.planner = Planner(model_client, tool_executor.get_tool_schemas())
        self.stop_conditions = StopConditions(max_iterations, max_tool_calls, max_rag_calls)
        
        # Allow caller to override trace output dir (useful for tests)
        if trace_output_dir is None:
            # Default: evidence/traces relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            trace_output_dir = os.path.join(project_root, "evidence", "traces")
        self.tracer = Tracer(output_dir=trace_output_dir)
    
    def run(self, goal, student_name="Student", trace_id=None):
        """
        Run the bounded agent loop.
        
        Returns:
            dict with 'response', 'state', 'trace_file', 'iterations', 'stop_reason'
        """
        state = AgentState(goal)
        assigned_trace_id = self.tracer.start_trace(goal, trace_id=trace_id)
        
        print(f"\n[Agent] Starting trace {assigned_trace_id}")
        print(f"[Agent] Goal: {goal}\n")
        
        while True:
            # EVALUATE — check stop conditions before each iteration
            should_stop, reason = self.stop_conditions.should_stop(state)
            if should_stop:
                state.stop_reason = reason
                print(f"[Agent] STOP — {reason}")
                break
            
            state.next_iteration()
            print(f"\n[Agent] ── Iteration {state.iteration} ──")
            
            # 1. SENSE
            sense_data = self._sense(state)
            state.add_step("sense", sense_data)
            print(f"[Agent] SENSE: iter={state.iteration}, rag_results={sense_data['has_rag_results']}, tool_results={sense_data['has_tool_results']}")
            
            # 2. PLAN
            plan = self.planner.plan_next_action(state)
            state.current_plan = plan
            state.add_step("plan", plan)
            print(f"[Agent] PLAN: {plan}")
            
            # 3. ACT
            action = plan.get("action")
            
            if action == "answer":
                final_text = plan.get("text", "")
                state.mark_complete(final_text, "goal_achieved")
                state.add_step("act", {"action": "answer", "text": final_text})
                print(f"[Agent] ACT: answer → {final_text[:100]}...")
                break
            
            elif action == "stop":
                stop_reason = plan.get("reason", "agent_stopped")
                final_text = self._generate_stop_response(state, stop_reason)
                state.mark_complete(final_text, stop_reason)
                state.add_step("act", {"action": "stop", "reason": stop_reason})
                print(f"[Agent] ACT: stop → {stop_reason}")
                break
            
            elif action == "rag_retrieve":
                query = plan.get("query", goal)
                result = self._execute_rag(state, query)
                state.add_step("act", {"action": "rag_retrieve", "query": query, "result": result})
                print(f"[Agent] ACT: rag_retrieve({query!r}) → success={result.get('success')}")
            
            elif action == "call_tool":
                result = self._execute_tool(state, plan, student_name)
                state.add_step("act", {"action": "call_tool", "tool": plan.get("tool"), "result": result})
                print(f"[Agent] ACT: call_tool({plan.get('tool')}) → success={result.get('success')}")
            
            else:
                state.mark_complete(
                    "I'm not sure how to help with that. Would you like me to create a support ticket?",
                    "unknown_action"
                )
                break
            
            # 4. OBSERVE
            observation = self._observe(state)
            state.add_step("observe", observation)
            print(f"[Agent] OBSERVE: tool_calls={observation['tool_call_count']}, rag_calls={observation['rag_call_count']}")
            
            # Record this iteration in tracer
            self.tracer.record_iteration({
                "iteration": state.iteration,
                "action": action,
                "plan": plan,
                "observation": observation
            })
        
        # Generate final response if not set by loop
        if not state.final_response:
            state.final_response = self._generate_final_response(state)
        
        self.tracer.end_trace(state.final_response, state.stop_reason)
        trace_file = self.tracer.save()
        
        print(f"\n[Agent] Final response: {state.final_response}")
        print(f"[Agent] Trace saved: {trace_file}")
        
        return {
            "response": state.final_response,
            "state": state.to_dict(),
            "trace_file": trace_file,
            "iterations": state.iteration,
            "stop_reason": state.stop_reason
        }
    
    def _sense(self, state):
        return {
            "goal": state.goal,
            "iteration": state.iteration,
            "has_rag_results": len(state.retrieved_documents) > 0,
            "has_tool_results": len(state.tool_results) > 0,
            "history_length": len(state.history)
        }
    
    def _execute_rag(self, state, query):
        try:
            result = self.rag.query(query)
            state.retrieved_documents.append(result)
            state.rag_call_count += 1
            self.tracer.record_rag_call(
                query=query,
                num_results=len(result.get("retrieved_chunks", [])),
                sources=result.get("sources", [])
            )
            return {
                "success": True,
                "num_results": len(result.get("retrieved_chunks", [])),
                "sources": result.get("sources", []),
                "context_preview": result.get("context", "")[:200]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_tool(self, state, plan, student_name="Student"):
        tool_name = plan.get("tool")
        arguments = plan.get("arguments", {})
        
        # For ticket creation, inject student_name if not provided
        if tool_name == "create_support_ticket" and "student_name" not in arguments:
            arguments["student_name"] = student_name
        
        try:
            result = self.executor.execute(tool_name, arguments)
            state.tool_results.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result
            })
            state.tool_call_count += 1
            
            self.tracer.record_tool_call(tool_name, arguments, result.get("result"))
            
            # Check approval outcome for ticket creation
            if tool_name == "create_support_ticket":
                approval_log = self.executor.approval.get_log()
                if approval_log:
                    last = approval_log[-1]
                    self.tracer.record_approval(tool_name, arguments, last.get("approved", False))
                    if not last.get("approved", False):
                        state.human_needed = True
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _observe(self, state):
        return {
            "iteration": state.iteration,
            "tool_call_count": state.tool_call_count,
            "rag_call_count": state.rag_call_count,
            "has_new_info": len(state.history) > 0,
            "last_action_success": self._last_action_succeeded(state)
        }
    
    def _last_action_succeeded(self, state):
        act_steps = [h for h in state.history if h["action"] == "act"]
        if not act_steps:
            return True
        last = act_steps[-1]["data"]
        result = last.get("result", {})
        if isinstance(result, dict):
            return result.get("success", True)
        return True
    
    def _generate_stop_response(self, state, reason):
        if reason == "max_iterations_reached":
            return (
                "I've been working on your issue but need more information to help fully. "
                "Would you like me to create a support ticket for direct assistance?"
            )
        elif reason == "no_progress_detected":
            return (
                "I need more details to help you. Could you tell me:\n"
                "- What course or service is this about?\n"
                "- What specifically is the issue?\n\n"
                "Or I can create a support ticket for direct assistance."
            )
        else:
            return (
                "I wasn't able to fully resolve your issue. "
                "Would you like me to create a support ticket?"
            )
    
    def _generate_final_response(self, state):
        if state.tool_results:
            last_result = state.tool_results[-1]
            if last_result["tool"] == "create_support_ticket":
                result_data = last_result["result"].get("result", {})
                if result_data.get("success"):
                    ticket_id = result_data.get("ticket_id", "unknown")
                    return (
                        f"I've created ticket {ticket_id} for your issue. "
                        "Support staff will follow up within 24 hours."
                    )
        if state.retrieved_documents:
            return "Based on the information I found, please see the details above."
        return "I need more information to help you. Could you clarify your issue?"
