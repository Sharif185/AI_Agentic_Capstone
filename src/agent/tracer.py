import json
from datetime import datetime
from pathlib import Path

class Tracer:
    """Records execution traces for the agent."""
    
    def __init__(self, output_dir="evidence/traces"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_trace = None
    
    def start_trace(self, goal, trace_id=None):
        self.current_trace = {
            "trace_id": trace_id or f"TRACE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "goal": goal,
            "started_at": datetime.now().isoformat(),
            "iterations": [],
            "tool_calls": [],
            "rag_calls": [],
            "human_approvals": [],
            "final_response": None,
            "stop_reason": None,
            "completed_at": None
        }
        return self.current_trace["trace_id"]
    
    def record_iteration(self, iteration_data):
        if self.current_trace:
            self.current_trace["iterations"].append(iteration_data)
    
    def record_tool_call(self, tool_name, arguments, result):
        if self.current_trace:
            self.current_trace["tool_calls"].append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
    
    def record_rag_call(self, query, num_results, sources):
        if self.current_trace:
            self.current_trace["rag_calls"].append({
                "query": query,
                "num_results": num_results,
                "sources": sources,
                "timestamp": datetime.now().isoformat()
            })
    
    def record_approval(self, tool, arguments, approved):
        if self.current_trace:
            self.current_trace["human_approvals"].append({
                "tool": tool,
                "arguments": arguments,
                "approved": approved,
                "timestamp": datetime.now().isoformat()
            })
    
    def end_trace(self, final_response, stop_reason):
        if self.current_trace:
            self.current_trace["final_response"] = final_response
            self.current_trace["stop_reason"] = stop_reason
            self.current_trace["completed_at"] = datetime.now().isoformat()
    
    def save(self, filename=None):
        if not self.current_trace:
            return None
        if filename is None:
            filename = f"{self.current_trace['trace_id']}.json"
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.current_trace, f, indent=2)
        return str(filepath)
    
    def get_trace(self):
        return self.current_trace
