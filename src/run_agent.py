from dotenv import load_dotenv

from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from tools.approval_controller import ApprovalController
from tools.tool_executor import ToolExecutor
from agent.planner import Planner
from agent.agent import StudentSupportAgent

load_dotenv()


def main():
    print("=" * 60)
    print("Student Support Agent - Bounded Multi-Step Agent (Week 5)")
    print("=" * 60)

    # 1. Model client
    model = ModelClient()

    # 2. RAG pipeline
    rag_pipeline = RAGPipeline()

    # 3. Approved tools
    course_tool = CourseTool()
    ticket_tool = TicketTool()

    # 4. Approval controller
    approval_controller = ApprovalController()

    # 5. Tool executor (existing Week 4 component — not bypassed or duplicated)
    tool_executor = ToolExecutor(approval_controller)
    tool_executor.register(course_tool)
    tool_executor.register(ticket_tool)

    # 6. Agent, with its own Planner
    planner = Planner(model)
    agent = StudentSupportAgent(
        model_client=model,
        rag_pipeline=rag_pipeline,
        tool_executor=tool_executor,
        planner=planner,
        max_iterations=5,
        max_tool_calls=3,
        max_rag_calls=2,
    )

    print("\nDescribe what you need help with. Type 'exit' to quit.\n")

    while True:
        goal = input("Student: ").strip()

        if goal.lower() == "exit":
            print("Goodbye!")
            break

        if not goal:
            print("Assistant: Please tell me what you need help with.")
            continue

        result = agent.run(goal)

        print(f"\nAssistant: {result['response']}")
        print(f"\n[Iterations: {result['iterations']}]")
        print(f"[Stop reason: {result['stop_reason']}]")
        print(f"[Trace saved to: {result['trace_file']}]\n")


if __name__ == "__main__":
    main()
