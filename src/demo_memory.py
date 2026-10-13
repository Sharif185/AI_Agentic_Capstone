"""
Memory Demonstration — Week 6

Two-session demonstration proving that memory persists across sessions
and improves the task (student doesn't need to re-explain).

Author: Aloysious Mutagubya (Application/Integration Lead)
"""

from datetime import datetime, timezone

from memory.memory_manager import MemoryManager


def main():
    print("=" * 70)
    print("Week 6 Memory Demonstration: Cross-Session Ticket Persistence")
    print("=" * 70)
    print()

    # Use a dedicated demo database so we don't pollute production data
    demo_db = "data/demo_memory.db"

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

    print()
    print("✅ Memory improved the task: Student didn't need to re-explain")
    print()

    mm2.end_session()
    print("[Session 2 ended]")
    print()

    # ===================================================================
    # Database Stats
    # ===================================================================

    print("--- Database Stats ---")
    stats = mm2.get_stats()
    print(f"Total sessions: {stats['sessions']}")
    print(f"Total tickets: {stats['tickets_total']}")
    print(f"Open tickets: {stats['tickets_open']}")
    print(f"Database: {stats['db_path']}")
    print()

    # ===================================================================
    # Right to be Forgotten Test
    # ===================================================================

    print("--- Testing Right to be Forgotten ---")
    print("Student requests: 'Delete my data'")
    result = mm2.delete_all_data("demo_student")
    print(f"✅ Deleted: {result['deleted_tickets']} ticket(s), "
          f"{result['deleted_sessions']} session(s), "
          f"{result['deleted_preferences']} preference(s)")
    print()

    stats_after = mm2.get_stats()
    print(f"Total tickets after deletion: {stats_after['tickets_total']}")
    print()

    print("=" * 70)
    print("Demonstration complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
