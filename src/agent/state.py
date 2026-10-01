from datetime import datetime

class AgentState:
    """Tracks the agent's state across iterations."""
    
    def __init__(self, goal, max_iterations=5):
        self.goal = goal
        self.iteration = 0
        self.max_iterations = max_iterations
        self.history = []
        self.retrieved_documents = []
        self.tool_results = []
        self.current_plan = None
        self.completed = False
        self.human_needed = False
        self.final_response = None
        self.stop_reason = None
        self.started_at = datetime.now().isoformat()
        self.tool_call_count = 0
        self.rag_call_count = 0
    
    def add_step(self, action, data):
        self.history.append({
            "iteration": self.iteration,
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def next_iteration(self):
        self.iteration += 1
    
    def mark_complete(self, response, reason):
        self.completed = True
        self.final_response = response
        self.stop_reason = reason
    
    def to_dict(self):
        return {
            "goal": self.goal,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "history": self.history,
            "retrieved_documents": self.retrieved_documents,
            "tool_results": self.tool_results,
            "completed": self.completed,
            "human_needed": self.human_needed,
            "final_response": self.final_response,
            "stop_reason": self.stop_reason,
            "tool_call_count": self.tool_call_count,
            "rag_call_count": self.rag_call_count,
            "started_at": self.started_at
        }
