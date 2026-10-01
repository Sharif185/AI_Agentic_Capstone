import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from tools.ticket_storage import TicketStorage
from orchestration.tool_executor import ToolExecutor
from orchestration.approval_controller import ApprovalController
from agent.agent import StudentSupportAgent

def main():
    print("=" * 70)
    print("Student Support Agent - Bounded Autonomy (Week 5)")
    print("=" * 70)
    print("\nLimits: 5 iterations, 3 tool calls, 2 RAG calls")
    print("Type 'exit' to quit.\n")
    
    model = ModelClient()
    rag = RAGPipeline()
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    courses_path = os.path.join(project_root, "..", "data", "courses.json")
    db_path = os.path.join(project_root, "..", "data", "tickets.db")
    
    tools = [CourseTool(data_path=courses_path), TicketTool(storage=TicketStorage(db_path=db_path))]
    approval = ApprovalController(auto_approve=False, interactive=True)
    executor = ToolExecutor(tools, approval)
    agent = StudentSupportAgent(model, rag, executor)
    
    while True:
        goal = input("Student: ").strip()
        if goal.lower() == "exit":
            break
        if not goal:
            continue
        
        print("\n" + "─" * 70)
        result = agent.run(goal)
        print(f"\n{'─'*70}")
        print(f"Iterations: {result['iterations']} | Stop: {result['stop_reason']}")
        print(f"\nAssistant: {result['response']}")
        print(f"Trace: {result['trace_file']}\n")

if __name__ == "__main__":
    main()
