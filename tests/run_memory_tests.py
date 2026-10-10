"""
Memory Test Runner — Week 6

Automated unit tests for the memory subsystem.
Tests persistence, privacy, boundaries, and memory context formatting.
Written against Mus's actual MemoryManager API.

Author: Imaan Duga (Quality/Security Lead)
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory.memory_manager import MemoryManager


def _make_ticket(ticket_id, student_id, summary="Test issue"):
    return {
        "ticket_id": ticket_id,
        "student_name": "Test Student",
        "student_id": student_id,
        "issue_summary": summary,
        "priority": "medium",
        "category": "other",
        "status": "open",
        "created_at": "2026-10-08T10:00:00Z",
        "updated_at": "2026-10-08T10:00:00Z",
    }


def run_tests():
    results = []
    test_db = "data/test_memory_unit.db"

    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass

    print("=" * 60)
    print("Week 6 Memory Unit Tests")
    print("=" * 60)
    print()

    # ------------------------------------------------------------------
    # TEST 1: Session Created with SES- Prefix
    # ------------------------------------------------------------------
    print("TEST 1: Session created with SES- prefix")
    try:
        mm = MemoryManager(db_path=test_db)
        session_id = mm.start_session(user_id="test_user_1")
        assert session_id.startswith("SES-"), f"Expected SES- prefix, got {session_id}"
        print(f"✅ PASS: Session ID = {session_id}")
        results.append({"test": "session_created", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "session_created", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 2: Ticket Saved and Retrieved
    # ------------------------------------------------------------------
    print("TEST 2: Ticket saved and retrieved")
    try:
        mm = MemoryManager(db_path=test_db)
        mm.start_session(user_id="test_user_2")
        saved = mm.save_ticket(_make_ticket("TICKET-0002", "test_user_2"))
        retrieved = mm.get_ticket("TICKET-0002")
        assert retrieved is not None, "Ticket not found after save"
        assert retrieved["ticket_id"] == "TICKET-0002", "Wrong ticket ID"
        assert retrieved["issue_summary"] == "Test issue", "Wrong issue summary"
        print(f"✅ PASS: Ticket saved and retrieved correctly")
        results.append({"test": "ticket_saved_retrieved", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "ticket_saved_retrieved", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 3: Memory Context Includes Ticket Reference
    # ------------------------------------------------------------------
    print("TEST 3: Memory context includes ticket reference")
    try:
        mm = MemoryManager(db_path=test_db)
        mm.start_session(user_id="test_user_3")
        mm.save_ticket(_make_ticket("TICKET-0003", "test_user_3", "Context test issue"))
        context = mm.get_memory_context("test_user_3")
        assert "TICKET-0003" in context, f"Ticket ID not in context. Context was: {context!r}"
        assert "Context test issue" in context, "Issue summary not in context"
        print(f"✅ PASS: Memory context formatted correctly")
        results.append({"test": "memory_context_includes_ticket", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "memory_context_includes_ticket", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 4: Ticket Deletion
    # ------------------------------------------------------------------
    print("TEST 4: Ticket deletion")
    try:
        mm = MemoryManager(db_path=test_db)
        mm.start_session(user_id="test_user_4")
        mm.save_ticket(_make_ticket("TICKET-DEL", "test_user_4", "Will be deleted"))

        before = mm.get_ticket("TICKET-DEL")
        assert before is not None, "Ticket not found before deletion"

        deleted = mm.delete_ticket("TICKET-DEL")
        assert deleted is True, "delete_ticket() returned False"

        after = mm.get_ticket("TICKET-DEL")
        assert after is None, "Ticket still exists after deletion"
        print(f"✅ PASS: Ticket deleted successfully")
        results.append({"test": "ticket_deletion", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "ticket_deletion", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 5: Preferences Saved (set_preference API)
    # ------------------------------------------------------------------
    print("TEST 5: Preferences saved and retrieved")
    try:
        mm = MemoryManager(db_path=test_db)
        mm.start_session(user_id="test_user_5")
        # Mus's API: set_preference(key, value, approved=False)
        # approved=True + user_id present → gets persisted
        mm.set_preference("language", "en", approved=True)
        # Retrieve from persistent layer directly
        prefs = mm.persistent.get_preferences("test_user_5")
        assert prefs.get("language") == "en", f"Language preference not saved, got: {prefs}"
        print(f"✅ PASS: Preferences saved and retrieved")
        results.append({"test": "preferences_saved", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "preferences_saved", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 6: No Passwords Stored (Design Verification)
    # ------------------------------------------------------------------
    print("TEST 6: No passwords stored (design verification)")
    try:
        import sqlite3
        with sqlite3.connect(test_db) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            for table in table_names:
                cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                bad = [c for c in cols if any(w in c.lower() for w in ("password", "credential", "secret", "token"))]
                assert not bad, f"Found password-like column(s) in {table}: {bad}"
        print(f"✅ PASS: No password/credential fields in any DB table")
        results.append({"test": "no_passwords_stored", "status": "PASS"})
    except Exception as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "no_passwords_stored", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed  = len(results) - passed
    print(f"Total: {len(results)} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()

    os.makedirs("tests", exist_ok=True)
    with open("tests/week6-memory-results.json", "w") as f:
        json.dump({"tests": results, "summary": {"passed": passed, "failed": failed}}, f, indent=2)
    print("Results saved to: tests/week6-memory-results.json")
    print()

    try:
        if os.path.exists(test_db):
            os.remove(test_db)
            print(f"Test database cleaned up: {test_db}")
    except OSError:
        print(f"Note: Could not remove {test_db} (Windows file lock — safe to ignore)")

    return passed == len(results)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
