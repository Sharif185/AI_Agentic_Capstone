"""
Memory Integration Test — Week 6

Proves that memory persists across sessions — the core Week 6 requirement.

Two completely separate MemoryManager instances (simulating separate runs)
share only the database file. A ticket created in 'Session 1' must be
fully retrievable in 'Session 2' via a fresh MemoryManager.

Author: Imaan Duga (Quality/Security Lead)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory.memory_manager import MemoryManager


def test_multi_session_memory():
    """Cross-session memory persistence test."""
    db = "data/test_session_memory.db"

    # Clean start
    if os.path.exists(db):
        os.remove(db)

    print("=" * 60)
    print("Memory Integration Test: Cross-Session Persistence")
    print("=" * 60)
    print()

    # ===================================================================
    # SESSION 1: Create a ticket
    # ===================================================================
    print("--- Session 1: Creating ticket ---")
    mm1 = MemoryManager(db_path=db)
    mm1.start_session(user_id="student_001")

    ticket = {
        "ticket_id": "TICKET-0001",
        "student_name": "Integration Test Student",
        "student_id": "student_001",
        "issue_summary": "Cannot access the registration portal",
        "priority": "high",
        "category": "registration",
        "status": "open",
        "created_at": "2026-10-08T10:00:00Z",
        "updated_at": "2026-10-08T10:00:00Z",
    }
    mm1.save_ticket(ticket)
    mm1.end_session()
    print(f"✅ Session 1: Ticket TICKET-0001 saved and session ended")
    print()

    # ===================================================================
    # SESSION 2: Verify ticket is retrievable with a NEW MemoryManager
    # ===================================================================
    print("--- Session 2: Verifying ticket retrieval ---")
    mm2 = MemoryManager(db_path=db)   # brand-new instance, same DB
    mm2.start_session(user_id="student_001")

    # Retrieve the ticket from the new session
    retrieved = mm2.get_ticket("TICKET-0001")

    # Build memory context as the agent would
    context = mm2.get_memory_context(user_id="student_001")

    # ===================================================================
    # Assertions
    # ===================================================================
    assert retrieved is not None, "❌ FAIL: Ticket not found in Session 2"
    assert retrieved["ticket_id"] == "TICKET-0001", f"Wrong ticket ID: {retrieved['ticket_id']}"
    assert retrieved["status"] == "open", f"Wrong status: {retrieved['status']}"
    assert retrieved["issue_summary"] == "Cannot access the registration portal", "Wrong issue"
    assert "TICKET-0001" in context, "❌ FAIL: Ticket not in memory context"
    assert "open" in context, "❌ FAIL: Status not in memory context"

    print(f"✅ Ticket retrieved: {retrieved['ticket_id']} ({retrieved['status']})")
    print()
    print("🧠 Memory context in Session 2:")
    print(context)
    print()
    print("✅ Memory persists across sessions!")
    print()

    mm2.end_session()

    # ===================================================================
    # SESSION 3: Verify memory context improves task
    # ===================================================================
    print("--- Session 3: Demonstrating memory improves task ---")
    mm3 = MemoryManager(db_path=db)
    mm3.start_session(user_id="student_001")

    context3 = mm3.get_memory_context("student_001")
    assert "TICKET-0001" in context3, "❌ FAIL: Ticket not available in Session 3"

    print("Student: What's the status of my ticket?")
    print()
    retrieved3 = mm3.get_ticket("TICKET-0001")
    print(f"🤖 Agent (from memory): Your ticket {retrieved3['ticket_id']} about")
    print(f"   '{retrieved3['issue_summary']}' is currently {retrieved3['status']}.")
    print()
    print("✅ Student did NOT need to re-explain their issue")
    mm3.end_session()

    # Cleanup
    try:
        if os.path.exists(db):
            os.remove(db)
            print(f"Test database cleaned up: {db}")
    except OSError:
        print(f"Note: Could not remove {db} (file still locked — safe to ignore on Windows)")
    print()

    print("=" * 60)
    print("Integration Test: PASS")
    print("=" * 60)


if __name__ == "__main__":
    test_multi_session_memory()
    print()
    print("✅ All integration tests passed!")
