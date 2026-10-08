from dotenv import load_dotenv

from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from tools.ticket_status_tool import TicketStatusTool
from tools.approval_controller import ApprovalController
from tools.tool_executor import ToolExecutor
from agent.planner import Planner
from agent.agent import StudentSupportAgent
from memory.memory_manager import MemoryManager

load_dotenv()


def main():
    print("=" * 60)
    print("Student Support Agent - Bounded Multi-Step Agent (Week 6)")
    print("With Memory: Cross-session ticket persistence")
    print("=" * 60)

    # 1. Model client
    model = ModelClient()

    # 2. RAG pipeline
    rag_pipeline = RAGPipeline()

    # 3. Week 6: Memory manager (starts without an active session)
    memory = MemoryManager()

    # 4. Approved tools (Week 6: pass memory to ticket tools)
    course_tool = CourseTool()
    ticket_tool = TicketTool(memory=memory)
    ticket_status_tool = TicketStatusTool(memory=memory)

    # 5. Approval controller
    approval_controller = ApprovalController()

    # 6. Tool executor
    tool_executor = ToolExecutor(approval_controller)
    tool_executor.register(course_tool)
    tool_executor.register(ticket_tool)
    tool_executor.register(ticket_status_tool)

    # 7. Agent with its own Planner and MemoryManager
    planner = Planner(model)
    agent = StudentSupportAgent(
        model_client=model,
        rag_pipeline=rag_pipeline,
        tool_executor=tool_executor,
        planner=planner,
        memory_manager=memory,
        max_iterations=5,
        max_tool_calls=3,
        max_rag_calls=2,
    )

    print("\nDescribe what you need help with. Type 'exit' to quit.")
    print("For cross-session memory, provide a student ID (e.g., 'student_001').\n")

    # Start a session (can resume with a session_id, or start fresh)
    user_id = input("Your student ID (press Enter for anonymous): ").strip() or None
    session_id = memory.start_session(user_id=user_id)
    print(f"Session started: {session_id}\n")

    while True:
        goal = input("Student: ").strip()

        if goal.lower() == "exit":
            memory.end_session()
            print("Session saved. Goodbye!")
            break

        if not goal:
            print("Assistant: Please tell me what you need help with.")
            continue

        # Run agent with user_id for memory context
        result = agent.run(goal, user_id=user_id)

        print(f"\nAssistant: {result['response']}")
        print(f"\n[Iterations: {result['iterations']}]")
        print(f"[Stop reason: {result['stop_reason']}]")
        print(f"[Trace saved to: {result['trace_file']}]\n")


if __name__ == "__main__":
    main()
