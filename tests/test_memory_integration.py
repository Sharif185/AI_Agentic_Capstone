"""
Memory Integration Test — Week 6

Proves that memory persists across sessions.
Two completely separate MemoryManager instances share only the database file.
A ticket created in Session 1 must be retrievable in Session 2.

Written against Mus's actual MemoryManager API.

Author: Imaan Duga (Quality/Security Lead)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory.memory_manager import MemoryManager


def test_multi_session_memory():
    db = "data/test_session_memory.db"

    if os.path.exists(db):
        try:
            os.remove(db)
        except OSError:
            pass

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
    print("✅ Session 1: Ticket TICKET-0001 saved and session ended")
    print()

    # ===================================================================
    # SESSION 2: Verify ticket retrievable with a BRAND NEW MemoryManager
    # ===================================================================
    print("--- Session 2: Verifying ticket retrieval ---")
    mm2 = MemoryManager(db_path=db)   # new instance, same DB file
    mm2.start_session(user_id="student_001")

    retrieved = mm2.get_ticket("TICKET-0001")
    context   = mm2.get_memory_context(user_id="student_001")

    # Assertions
    assert retrieved is not None,                            "❌ Ticket not found in Session 2"
    assert retrieved["ticket_id"] == "TICKET-0001",          f"Wrong ticket ID: {retrieved['ticket_id']}"
    assert retrieved["status"] == "open",                    f"Wrong status: {retrieved['status']}"
    assert "Cannot access the registration portal" in retrieved["issue_summary"], "Wrong issue"
    assert "TICKET-0001" in context,                         f"Ticket not in context. Got: {context!r}"

    print(f"✅ Ticket retrieved: {retrieved['ticket_id']} ({retrieved['status']})")
    print()
    print("🧠 Memory context in Session 2:")
    print(context)
    print()
    print("✅ Memory persists across sessions!")
    print()
    mm2.end_session()

    # ===================================================================
    # SESSION 3: Demonstrate memory improves task
    # ===================================================================
    print("--- Session 3: Memory improves task ---")
    mm3 = MemoryManager(db_path=db)
    mm3.start_session(user_id="student_001")
    context3 = mm3.get_memory_context("student_001")
    assert "TICKET-0001" in context3, f"Ticket not available in Session 3. Got: {context3!r}"

    t = mm3.get_ticket("TICKET-0001")
    print("Student: What's the status of my ticket?")
    print(f"🤖 Agent: Your ticket {t['ticket_id']} about '{t['issue_summary']}' is {t['status']}.")
    print()
    print("✅ Student did NOT need to re-explain their issue")
    mm3.end_session()

    # Cleanup
    try:
        if os.path.exists(db):
            os.remove(db)
            print(f"Test database cleaned up: {db}")
    except OSError:
        print(f"Note: Could not remove {db} (Windows file lock — safe to ignore)")

    print()
    print("=" * 60)
    print("Integration Test: PASS")
    print("=" * 60)


if __name__ == "__main__":
    test_multi_session_memory()
    print()
    print("✅ All integration tests passed!")
