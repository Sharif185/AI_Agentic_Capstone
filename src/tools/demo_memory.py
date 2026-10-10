"""Week 6 two-session memory demonstration.

Run from the repo root:   python src/demo_memory.py
Writes only to data/demo_memory.db (isolated; deleted before and after the run).
Never touches data/memory.db. Demo data only - no real student information.

Parts:
  A. Session 1 stores a ticket; Session 2 (a NEW MemoryManager on the same DB)
     retrieves it. The reply is built from the retrieved record, not hardcoded.
  B. The REAL StudentSupportAgent + Planner run with a MOCK model (no live AI
     call) that captures the prompt, proving the agent receives the memory
     context, and that another student's agent receives none.
Exit code is non-zero if any check fails.
"""
import json
import os
import sys
import tempfile

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC_DIR)
REPO_ROOT = os.path.dirname(SRC_DIR)

from agent.agent import StudentSupportAgent  # noqa: E402
from agent.planner import Planner  # noqa: E402
from memory.memory_manager import MemoryManager  # noqa: E402
from tools.approval_controller import ApprovalController  # noqa: E402
from tools.tool_executor import ToolExecutor  # noqa: E402

DEMO_DB = os.path.join(REPO_ROOT, "data", "demo_memory.db")
STUDENT = "demo_student"
OTHER_STUDENT = "demo_other_student"
failures = []


def check(label, condition):
    print(f"  [{'PASS' if condition else 'FAIL'}] {label}")
    if not condition:
        failures.append(label)


def cleanup():
    if os.path.basename(DEMO_DB) != "demo_memory.db":  # safety: never remove anything else
        raise RuntimeError("refusing to delete a non-demo database")
    for suffix in ("", "-wal", "-shm", "-journal"):
        try:
            os.remove(DEMO_DB + suffix)
        except FileNotFoundError:
            pass


class MockModel:
    """Stands in for the LLM: records each planner prompt, always answers."""

    def __init__(self):
        self.prompts = []

    def generate(self, system_prompt, user_message, temperature=None, tools=None, disable_thinking=False):
        self.prompts.append(user_message)
        plan = {"action": "answer", "action_input": {"response": "(mock model reply)"}, "reasoning": "mock"}
        return {"response": json.dumps(plan)}


def run_agent_with(memory, user_id, goal):
    model = MockModel()
    agent = StudentSupportAgent(
        model_client=model, rag_pipeline=None,
        tool_executor=ToolExecutor(ApprovalController()),
        planner=Planner(model), memory_manager=memory,
        trace_dir=tempfile.mkdtemp(prefix="demo_traces_"),
    )
    agent.run(goal, user_id=user_id)
    return model.prompts[0]


def main():
    cleanup()
    print("=" * 62)
    print("WEEK 6 MEMORY DEMO (demo data only, isolated DB: data/demo_memory.db)")
    print("=" * 62)

    print("\n--- SESSION 1: Student creates a ticket ---")
    mm1 = MemoryManager(db_path=DEMO_DB)
    s1 = mm1.start_session(user_id=STUDENT)
    print(f"Session: {s1}")
    mm1.save_ticket({
        "ticket_id": "TICKET-0001", "student_name": "Demo Student", "student_id": STUDENT,
        "issue_summary": "Cannot access online registration portal",
        "priority": "high", "category": "registration", "status": "open",
        "created_at": "2026-10-08T10:00:00", "updated_at": "2026-10-08T10:00:00",
    })
    stored = mm1.get_ticket("TICKET-0001")
    print(f"Ticket stored: {stored['ticket_id']} | {stored['issue_summary']} | status={stored['status']}")
    check("Session ID has SES- prefix", s1.startswith("SES-"))
    check("Ticket readable in Session 1", stored is not None)
    mm1.end_session()
    del mm1
    print("[Session 1 ended; MemoryManager 1 discarded]")

    print("\n--- SESSION 2: Student returns (NEW MemoryManager, same DB) ---")
    mm2 = MemoryManager(db_path=DEMO_DB)
    s2 = mm2.start_session(user_id=STUDENT)
    print(f"Session: {s2}")
    check("Session 2 has a different session ID", s2 != s1)
    context = mm2.get_memory_context(user_id=STUDENT)
    print("Memory context retrieved from the database:")
    print("  " + context.replace("\n", "\n  "))
    ticket = mm2.get_ticket("TICKET-0001")
    check("Ticket survived into Session 2", ticket is not None and ticket["issue_summary"] == "Cannot access online registration portal")
    check("Context references TICKET-0001", "TICKET-0001" in context)
    print("\nStudent: What's the status of my ticket?")
    if ticket:
        reply = (f"Your ticket {ticket['ticket_id']} about '{ticket['issue_summary']}' "
                 f"is currently {ticket['status']}. Created: {ticket['created_at'][:10]}")
        print("Reply (built from the stored record, no model call):\n  " + reply)
        check("Reply reflects stored status 'open'", "currently open" in reply)

    print("\n--- Real agent receives the memory context (mock model, no live AI) ---")
    prompt = run_agent_with(mm2, STUDENT, "What's the status of my ticket?")
    check("Planner prompt has a MEMORY CONTEXT section", "MEMORY CONTEXT" in prompt)
    check("Planner prompt contains TICKET-0001 and its summary",
          "TICKET-0001" in prompt and "Cannot access online registration portal" in prompt)

    print("\n--- Isolation: a different student ---")
    mm_other = MemoryManager(db_path=DEMO_DB)
    mm_other.start_session(user_id=OTHER_STUDENT)
    other_prompt = run_agent_with(mm_other, OTHER_STUDENT, "What's the status of my ticket?")
    check("Other student's context is empty", mm_other.get_memory_context(OTHER_STUDENT) == "")
    check("Other student cannot read TICKET-0001 by ID", mm_other.get_ticket("TICKET-0001") is None)
    check("Other student's planner prompt has no MEMORY CONTEXT / TICKET-0001",
          "MEMORY CONTEXT" not in other_prompt and "TICKET-0001" not in other_prompt)
    mm_other.end_session()

    check("Agent still works with memory_manager=None",
          "MEMORY CONTEXT" not in run_agent_with(None, STUDENT, "What's the status of my ticket?"))
    mm2.end_session()

    print("\n" + "=" * 62)
    if failures:
        print(f"RESULT: FAILED ({len(failures)} check(s) failed)")
        for f in failures:
            print(f"  - {f}")
    else:
        print("RESULT: SUCCESS - the ticket persisted across separate sessions and managers;")
        print("        the student did not need to re-explain the issue.")
    print("=" * 62)
    cleanup()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
