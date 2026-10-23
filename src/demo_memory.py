"""
Memory Demonstration — Week 6

Two-session demonstration proving that memory persists across sessions
and improves the task (student doesn't need to re-explain).

Author: Aloysious Mutagubya (Application/Integration Lead)

Week 8 changes (Mus):

1. Windows portability: the demo prints emoji characters (✅ ❌ ⚠️ 🧠 🤖),
   which the Windows console's default cp1252 codec cannot encode. The
   stdout/stderr streams are reconfigured to UTF-8 at import time so the
   demo runs identically on Windows, Linux, and macOS.

2. API alignment: the original demo called three MemoryManager methods
   that did not exist or did not behave as assumed:
     * get_stats()        — never implemented in MemoryManager
     * delete_all_data()  — returns {"tickets", "sessions", "preferences"}
                            (plus "denied" if access is rejected), not
                            {"deleted_tickets", ...}
     * get_ticket()       — session-scoped: returns None unless the
                            current session owns the ticket
   The demo has been realigned to use these methods as actually
   implemented. The "before deletion" check now runs inside Session 2
   (before end_session), and a fresh Session 3 verifies the ticket is
   gone.

3. Machine-readable result marker: test_demo_passes
   (tests/test_week6_memory.py) asserts that the demo prints
   "RESULT: SUCCESS". The demo now tracks five verifiable claims and
   prints RESULT: SUCCESS only when all pass, RESULT: FAILURE otherwise.
"""

import sys

# Windows console defaults to cp1252, which cannot encode emoji. Reconfigure
# both streams before any output is produced. On non-Windows platforms this
# block is a no-op (streams are already UTF-8).
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

from datetime import datetime, timezone

from memory.memory_manager import MemoryManager


def main():
    print("=" * 70)
    print("Week 6 Memory Demonstration: Cross-Session Ticket Persistence")
    print("=" * 70)
    print()

    # Use a dedicated demo database so we don't pollute production data
    demo_db = "data/demo_memory.db"

    # Each verifiable claim about MemoryManager's behaviour is tracked here.
    # The summary at the end prints "RESULT: SUCCESS" only if all pass.
    # test_demo_passes (tests/test_week6_memory.py) asserts on that marker.
    checks = {}

    # ===================================================================
    # SESSION 1: Student creates a ticket
    # ===================================================================

    print("--- SESSION 1: Student creates a ticket ---")
    mm1 = MemoryManager(db_path=demo_db)
    session_id_1 = mm1.start_session(user_id="demo_student")
    print(f"Session: {session_id_1}")

    # Simulate a ticket being created by the agent (normally done by TicketTool)
    ticket = {
        "ticket_id": "TICKET-0001",
        "student_name": "Demo Student",
        "student_id": "demo_student",
        "issue_summary": "Cannot access online registration portal",
        "priority": "high",
        "category": "registration",
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    mm1.save_ticket(ticket)
    print(f"✅ Ticket created: {ticket['ticket_id']}")
    print(f"   Issue: {ticket['issue_summary']}")
    print(f"   Status: {ticket['status']}")

    mm1.end_session()
    print("[Session 1 ended]")
    print()

    # ===================================================================
    # SESSION 2: Student returns next day
    # ===================================================================

    print("--- SESSION 2: Student returns next day ---")
    mm2 = MemoryManager(db_path=demo_db)
    session_id_2 = mm2.start_session(user_id="demo_student")
    print(f"Session: {session_id_2}")
    print()

    # Agent loads memory context
    context = mm2.get_memory_context(user_id="demo_student")
    if context:
        print("🧠 Agent's memory context:")
        print(context)
        print()
    else:
        print("⚠️  No prior memory found (unexpected!)")
        print()

    # Student asks about ticket status
    print("Student: What's the status of my ticket?")
    print()

    # Agent uses memory to extract ticket ID and call check_ticket_status
    retrieved = mm2.get_ticket("TICKET-0001")
    if retrieved:
        print("🤖 Agent (using memory):")
        print(f"   Your ticket {retrieved['ticket_id']} about '{retrieved['issue_summary']}'")
        print(f"   is currently {retrieved['status']}. Created: {retrieved['created_at'][:10]}")
    else:
        print("❌ Ticket retrieval failed (this shouldn't happen!)")
    checks["memory_persisted"] = retrieved is not None

    print()
    print("✅ Memory improved the task: Student didn't need to re-explain")
    print()

    # ===================================================================
    # Memory State (before deletion) — inside the active session
    # ===================================================================
    # get_ticket() is session-scoped, so this check must run while the
    # owning session is still active.

    ticket_before = mm2.get_ticket("TICKET-0001")
    print("--- Memory State (before deletion) ---")
    print(f"Ticket TICKET-0001 in memory: {'yes' if ticket_before else 'no'}")
    if ticket_before:
        print(f"  status: {ticket_before.get('status', 'unknown')}")
    print(f"Database: {demo_db}")
    print()
    checks["ticket_present_before_deletion"] = ticket_before is not None

    # ===================================================================
    # Right to be Forgotten — same session, student requests deletion
    # ===================================================================

    print("--- Testing Right to be Forgotten ---")
    print("Student requests: 'Delete my data'")
    result = mm2.delete_all_data("demo_student")
    if result.get("denied"):
        print(f"❌ Deletion denied (session did not own the data): {result}")
        checks["deletion_accepted"] = False
        checks["deletion_removed_data"] = False
    else:
        print(f"✅ Deleted: {result.get('tickets', 0)} ticket(s), "
              f"{result.get('sessions', 0)} session(s), "
              f"{result.get('preferences', 0)} preference(s)")
        checks["deletion_accepted"] = True
        checks["deletion_removed_data"] = result.get("tickets", 0) > 0
    print()

    # delete_all_data() clears the active session as part of deletion, so
    # there is nothing left to end_session() on mm2.
    print("[Session 2 ended]")
    print()

    # ===================================================================
    # Verify deletion in a fresh session
    # ===================================================================
    # A new session started by the same user should not see the deleted
    # ticket. This is the reliable "gone" proof.

    print("--- Verifying deletion in a fresh session ---")
    mm3 = MemoryManager(db_path=demo_db)
    session_id_3 = mm3.start_session(user_id="demo_student")
    print(f"Session: {session_id_3}")
    ticket_after = mm3.get_ticket("TICKET-0001")
    print(f"Ticket TICKET-0001 visible: {'yes' if ticket_after else 'no'}")
    mm3.end_session()
    checks["ticket_gone_after_deletion"] = ticket_after is None
    print()

    # ===================================================================
    # Summary — the machine-readable marker test_demo_passes asserts on
    # ===================================================================

    print("=" * 70)
    if all(checks.values()):
        print("RESULT: SUCCESS")
        print(f"All {len(checks)} checks passed:")
        for name, ok in checks.items():
            print(f"  [PASS] {name}")
    else:
        print("RESULT: FAILURE")
        print("Checks that failed:")
        for name, ok in checks.items():
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print("=" * 70)
    print("Demonstration complete!")


if __name__ == "__main__":
    main()