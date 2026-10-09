"""Week 6 memory tests (Mus's modules). Run from the repo root:

    python -m unittest tests.test_week6_memory -v      (or: python tests/test_week6_memory.py)

All tests use temporary databases/files; the team's data/memory.db is never touched.
No live model or network is used.
"""
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from agent.agent import StudentSupportAgent  # noqa: E402
from agent.planner import Planner  # noqa: E402
from agent.state import AgentState  # noqa: E402
from memory.memory_manager import MemoryManager  # noqa: E402
from memory.persistent_memory import PersistentMemory  # noqa: E402
from memory.session_state import SessionState  # noqa: E402
from tools.approval_controller import ApprovalController  # noqa: E402
from tools.ticket_tool import TicketTool  # noqa: E402
from tools.tool_executor import ToolExecutor  # noqa: E402


def ticket(tid="TICKET-0001", sid="stu1", summary="Cannot access online registration portal", **kw):
    t = {"ticket_id": tid, "student_name": "Demo Student", "student_id": sid,
         "issue_summary": summary, "priority": "high", "category": "registration", "status": "open"}
    t.update(kw)
    return t


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "m.db")

    def tearDown(self):
        self.tmp.cleanup()

    def mm(self, user=None):
        m = MemoryManager(self.db)
        m.start_session(user_id=user)
        return m


class TestSessionState(unittest.TestCase):
    def test_id_prefix_and_uniqueness(self):  # 1
        a, b = SessionState(), SessionState()
        self.assertTrue(a.session_id.startswith("SES-"))
        self.assertNotEqual(a.session_id, b.session_id)

    def test_touch_and_case(self):  # 2
        s = SessionState(user_id="u")
        before = s.last_active
        s.touch(); s.touch()
        self.assertEqual(s.conversation_turns, 2)
        self.assertGreaterEqual(s.last_active, before)
        s.set_current_case("TICKET-1")
        self.assertEqual(s.get_context()["current_case"], "TICKET-1")

    def test_roundtrip(self):  # 3
        s = SessionState(user_id="u"); s.touch(); s.preferences["lang"] = "en"; s.set_current_case("T-1")
        r = SessionState.from_dict(s.to_dict())
        self.assertEqual(r.to_dict(), s.to_dict())

    def test_from_dict_invalid_fields(self):  # 20
        r = SessionState.from_dict({"session_id": 5, "user_id": [], "started_at": "junk",
                                    "preferences": "x", "conversation_turns": "3", "current_case": 9})
        self.assertTrue(r.session_id.startswith("SES-"))
        self.assertIsNone(r.user_id); self.assertEqual(r.preferences, {})
        self.assertEqual(r.conversation_turns, 0); self.assertIsNone(r.current_case)
        self.assertIsInstance(SessionState.from_dict(None), SessionState)

    def test_expiry(self):
        s = SessionState()
        self.assertFalse(s.is_expired())
        self.assertTrue(s.is_expired(now=datetime.now(timezone.utc) + timedelta(days=31)))


class TestPersistence(Base):
    def test_save_get_and_restart(self):  # 4, 5
        m1 = self.mm("stu1"); m1.save_ticket(ticket()); m1.end_session()
        m2 = self.mm("stu1")
        t = m2.get_ticket("TICKET-0001")
        self.assertEqual((t["status"], t["issue_summary"]), ("open", "Cannot access online registration portal"))
        self.assertTrue(t["session_id"].startswith("SES-"))

    def test_repeat_save_no_duplicate(self):
        m = self.mm("stu1"); m.save_ticket(ticket()); m.save_ticket(ticket(status="in_progress"))
        rows = m.persistent.get_tickets_by_student("stu1")
        self.assertEqual(len(rows), 1); self.assertEqual(rows[0]["status"], "in_progress")

    def test_multiple_tickets_per_student(self):  # 6
        m = self.mm("stu1")
        m.save_ticket(ticket("T-1")); m.save_ticket(ticket("T-2", summary="Exam timetable clash"))
        self.assertEqual({t["ticket_id"] for t in m.persistent.get_tickets_by_student("stu1")}, {"T-1", "T-2"})

    def test_ticket_id_cannot_overwrite_other_student(self):
        PersistentMemory(self.db).save_ticket(ticket("T-1", "stu1"))
        with self.assertRaises(ValueError):
            PersistentMemory(self.db).save_ticket(ticket("T-1", "stu2"))
        self.assertEqual(PersistentMemory(self.db).get_ticket("T-1")["student_id"], "stu1")

    def test_db_path_without_directory(self):
        cwd = os.getcwd(); os.chdir(self.tmp.name)
        try:
            PersistentMemory("plain.db").save_ticket(ticket())
            self.assertTrue(os.path.exists("plain.db"))
        finally:
            os.chdir(cwd)

    def test_missing_records_safe(self):  # 20
        p = PersistentMemory(self.db)
        self.assertIsNone(p.get_ticket("nope")); self.assertIsNone(p.load_session("SES-none"))
        self.assertFalse(p.delete_ticket("nope")); self.assertEqual(p.get_tickets_by_student(""), [])
        with self.assertRaises(ValueError):
            p.save_ticket({"ticket_id": "x"})
        with self.assertRaises(ValueError):
            MemoryManager(self.db).save_ticket(ticket())  # no active session

    def test_sql_injection_is_inert(self):  # parameterised SQL
        p = PersistentMemory(self.db); p.save_ticket(ticket())
        self.assertEqual(p.get_tickets_by_student("x' OR '1'='1"), [])
        self.assertIsNone(p.get_ticket("TICKET-0001' OR '1'='1"))
        self.assertIsNotNone(p.get_ticket("TICKET-0001"))


class TestIsolationAndContext(Base):
    def test_isolation(self):  # 7, 15
        a = self.mm("stu1"); a.save_ticket(ticket("T-A", "stu1", "Portal login problem")); a.end_session()
        b = self.mm("stu2"); b.save_ticket(ticket("T-B", "stu2", "Fee statement query"))
        ctx = b.get_memory_context("stu2")
        self.assertIn("T-B", ctx); self.assertNotIn("T-A", ctx); self.assertNotIn("Portal login", ctx)
        self.assertEqual(b.get_memory_context("stu1"), "")      # cannot ask for someone else's
        self.assertIsNone(b.get_ticket("T-A"))                  # ticket ID alone is not enough

    def test_context_requires_matching_active_session(self):
        m = MemoryManager(self.db)
        self.assertEqual(m.get_memory_context("stu1"), "")
        m.start_session(None); m.save_ticket(ticket("T-1", None))
        self.assertEqual(m.get_memory_context("stu1"), "")

    def test_mismatched_student_id_rejected(self):
        m = self.mm("stu1")
        with self.assertRaises(ValueError):
            m.save_ticket(ticket("T-9", "someone_else"))

    def test_unowned_ticket_same_session_only(self):
        m = MemoryManager(self.db); m.start_session(None); m.save_ticket(ticket("T-1", None))
        self.assertIsNotNone(m.get_ticket("T-1"))
        m.end_session(); m.start_session(None)
        self.assertIsNone(m.get_ticket("T-1"))

    def test_empty_memory_context(self):
        self.assertEqual(self.mm("fresh").get_memory_context("fresh"), "")


class TestDeletion(Base):
    def test_delete_ticket_only(self):  # 8
        m = self.mm("stu1"); m.save_ticket(ticket("T-1")); m.save_ticket(ticket("T-2"))
        self.assertTrue(m.delete_ticket("T-1"))
        self.assertIsNone(m.get_ticket("T-1")); self.assertIsNotNone(m.get_ticket("T-2"))

    def test_delete_session_only(self):
        m = self.mm("stu1"); m.save_ticket(ticket()); sid = m.current_session.session_id
        self.assertTrue(m.delete_session_data())
        self.assertIsNone(m.persistent.load_session(sid))
        self.assertIsNotNone(m.persistent.get_ticket("TICKET-0001"))  # ticket remains

    def test_delete_all_data(self):  # 13
        a = self.mm("stu1"); a.save_ticket(ticket("T-1")); a.set_preference("lang", "en", approved=True)
        b = MemoryManager(self.db); b.start_session("stu2"); b.save_ticket(ticket("T-2", "stu2")); b.end_session()
        counts = a.delete_all_data("stu1")
        self.assertEqual(counts["tickets"], 1); self.assertEqual(counts["preferences"], 1)
        self.assertGreaterEqual(counts["sessions"], 1)
        p = PersistentMemory(self.db)
        self.assertEqual(p.get_tickets_by_student("stu1"), []); self.assertEqual(p.get_preferences("stu1"), {})
        self.assertIsNotNone(p.get_ticket("T-2"))  # other student untouched

    def test_delete_all_denied_for_other_user(self):
        a = self.mm("stu1"); a.save_ticket(ticket())
        b = self.mm("stu2")
        self.assertEqual(b.delete_all_data("stu1").get("denied"), 1)
        self.assertIsNotNone(PersistentMemory(self.db).get_ticket("TICKET-0001"))


class TestPreferencesAndPrivacy(Base):
    def test_approved_preference_persists(self):  # 9
        m = self.mm("stu1"); self.assertTrue(m.set_preference("reply_style", "short", approved=True))
        self.assertEqual(self.mm("stu1").persistent.get_preferences("stu1"), {"reply_style": "short"})
        self.assertIn("reply_style=short", self.mm("stu1").get_memory_context("stu1"))

    def test_unapproved_preference_not_persisted(self):  # 10
        m = self.mm("stu1")
        self.assertFalse(m.set_preference("reply_style", "short", approved=False))
        self.assertEqual(m.current_session.preferences["reply_style"], "short")  # in-session only
        self.assertEqual(m.persistent.get_preferences("stu1"), {})
        m.end_session()
        with sqlite3.connect(self.db) as c:
            self.assertNotIn("short", json.dumps(c.execute("SELECT * FROM sessions").fetchall()))

    def test_store_level_rejects_unapproved(self):  # 10 (store layer, independent of the manager)
        p = PersistentMemory(self.db)
        self.assertFalse(p.save_preference("stu1", "reply_style", "short", approved=False))
        self.assertEqual(p.get_preferences("stu1"), {})

    def test_prohibited_preferences_rejected(self):  # 14
        p = PersistentMemory(self.db)
        for k, v in [("password", "x"), ("grade", "A"), ("medical_condition", "y"), ("note", "card 4111 1111 1111 1111"),
                     ("note", "my password is hunter2")]:
            self.assertFalse(p.save_preference("stu1", k, v), (k, v))
        self.assertEqual(p.get_preferences("stu1"), {})

    def test_ticket_text_redacted_and_extras_dropped(self):  # 14
        p = PersistentMemory(self.db)
        t = p.save_ticket(ticket(summary="Login fails, password is hunter2, card 4111 1111 1111 1111",
                                 password="hunter2", grades="A"))
        self.assertNotIn("hunter2", t["issue_summary"]); self.assertNotIn("4111", t["issue_summary"])
        with sqlite3.connect(self.db) as c:
            cols = [r[1] for r in c.execute("PRAGMA table_info(case_history)")]
            dump = json.dumps(c.execute("SELECT * FROM case_history").fetchall())
        self.assertNotIn("password", cols); self.assertNotIn("hunter2", dump)

    def test_no_transcript_columns(self):
        with sqlite3.connect(self.db) as c:
            PersistentMemory(self.db)
            cols = {r[1] for t in ("sessions", "case_history", "preferences") for r in c.execute(f"PRAGMA table_info({t})")}
        self.assertFalse({"transcript", "messages", "conversation"} & cols)


class TestRetention(Base):
    def test_sessions_purged_after_30_days(self):  # 11
        p = PersistentMemory(self.db)
        old, new = SessionState(user_id="u"), SessionState(user_id="u")
        old.last_active = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        p.save_session(old); p.save_session(new)
        self.assertEqual(p.purge_old_sessions(30), 1)
        self.assertIsNone(p.load_session(old.session_id)); self.assertIsNotNone(p.load_session(new.session_id))

    def test_ticket_retention_active_90_closed_365(self):  # 12
        p = PersistentMemory(self.db)
        now = datetime.now(timezone.utc)
        ago = lambda d: (now - timedelta(days=d)).isoformat()
        p.save_ticket(ticket("open-old", updated_at=ago(91), created_at=ago(91)))
        p.save_ticket(ticket("open-ok", updated_at=ago(89), created_at=ago(89)))
        p.save_ticket(ticket("closed-100d", status="closed", updated_at=ago(100), created_at=ago(100)))
        p.save_ticket(ticket("closed-old", status="closed", updated_at=ago(366), created_at=ago(366)))
        self.assertEqual(p.purge_expired_tickets(), 2)
        left = {t["ticket_id"] for t in p.get_tickets_by_student("stu1")}
        self.assertEqual(left, {"open-ok", "closed-100d"})

    def test_start_session_enforces_retention(self):
        p = PersistentMemory(self.db); p.save_ticket(ticket("stale", updated_at="2020-01-01T00:00:00", created_at="2020-01-01T00:00:00"))
        self.mm("stu1")
        self.assertIsNone(PersistentMemory(self.db).get_ticket("stale"))

    def test_resume_session(self):
        m = self.mm("stu1"); sid = m.current_session.session_id; m.end_session()
        m2 = MemoryManager(self.db)
        self.assertFalse(m2.resume_session("SES-nonexistent"))
        self.assertFalse(m2.resume_session(sid, user_id="stu2"))
        self.assertTrue(m2.resume_session(sid, user_id="stu1"))
        old = SessionState(user_id="stu1"); old.last_active = "2020-01-01T00:00:00+00:00"
        m2.persistent.save_session(old)
        self.assertFalse(m2.resume_session(old.session_id))


class _CaptureModel:
    def __init__(self):
        self.prompts = []

    def generate(self, system_prompt, user_message, temperature=None, tools=None, disable_thinking=False):
        self.prompts.append(user_message)
        return {"response": json.dumps({"action": "answer", "action_input": {"response": "ok"}, "reasoning": "t"})}


class TestAgentIntegration(Base):
    def agent(self, memory):
        model = _CaptureModel()
        a = StudentSupportAgent(model, None, ToolExecutor(ApprovalController()), Planner(model),
                                memory_manager=memory, trace_dir=self.tmp.name)
        return a, model

    def test_agent_works_without_memory(self):  # 16
        a, model = self.agent(None)
        r = a.run("hello")
        self.assertEqual((r["response"], r["stop_reason"]), ("ok", "goal_achieved"))
        self.assertNotIn("MEMORY CONTEXT", model.prompts[0])
        self.assertEqual(r["state"]["memory_context"], "")

    def test_agent_receives_memory(self):  # 17, 19-ish
        m = self.mm("stu1"); m.save_ticket(ticket())
        a, model = self.agent(m)
        r = a.run("status of my ticket?", user_id="stu1")
        self.assertIn("MEMORY CONTEXT", model.prompts[0]); self.assertIn("TICKET-0001", model.prompts[0])
        self.assertIn("TICKET-0001", r["state"]["memory_context"])
        self.assertEqual(m.current_session.conversation_turns, 1)

    def test_agent_without_user_id_or_empty_memory(self):  # 17
        m = self.mm("stu1"); m.save_ticket(ticket())
        a, model = self.agent(m)
        a.run("hi"); a.run("hi", user_id="stu_new")
        self.assertTrue(all("MEMORY CONTEXT" not in p for p in model.prompts))

    def test_memory_failure_does_not_break_agent(self):
        class Broken:
            def record_turn(self): raise RuntimeError("db down")
        a, _ = self.agent(Broken())
        self.assertEqual(a.run("hi", user_id="stu1")["stop_reason"], "goal_achieved")

    def test_planner_prompt_empty_and_populated(self):  # 17
        s = AgentState("goal")
        self.assertEqual(s.memory_context, "")
        self.assertNotIn("MEMORY CONTEXT", Planner(None)._format_memory(s))
        s.memory_context = "Prior tickets for this student: 1"
        out = Planner(None)._format_memory(s)
        self.assertIn("MEMORY CONTEXT", out); self.assertIn("takes precedence", out)


class TestTicketToolMemory(Base):
    def run_tool(self, memory, decision=True):
        tool = TicketTool(storage_path=os.path.join(self.tmp.name, "tickets.json"), memory=memory)
        ex = ToolExecutor(ApprovalController(decision_fn=lambda n, a: decision)); ex.register(tool)
        return ex.execute("create_support_ticket", {"student_name": "Demo Student", "student_id": "stu1",
                                                    "issue_summary": "Cannot access registration portal", "category": "registration"})

    def test_ticket_saved_to_memory_once(self):
        m = self.mm("stu1")
        r = self.run_tool(m)
        self.assertTrue(r["success"] and r["memory_saved"] and r["approved"])
        rows = m.persistent.get_tickets_by_student("stu1")
        self.assertEqual(len(rows), 1); self.assertEqual(rows[0]["ticket_id"], r["ticket"]["ticket_id"])
        self.assertEqual(m.current_session.current_case, r["ticket"]["ticket_id"])

    def test_denied_approval_saves_nothing(self):
        m = self.mm("stu1")
        r = self.run_tool(m, decision=False)
        self.assertFalse(r["success"]); self.assertEqual(r["error"], "Human approval denied")
        self.assertEqual(m.persistent.get_tickets_by_student("stu1"), [])

    def test_memory_failure_keeps_ticket(self):
        m = MemoryManager(self.db)  # no active session -> memory save fails
        r = self.run_tool(m)
        self.assertTrue(r["success"]); self.assertFalse(r["memory_saved"])

    def test_without_memory_unchanged(self):
        r = self.run_tool(None)
        self.assertTrue(r["success"]); self.assertNotIn("memory_saved", r)

    def test_status_lookup_contract(self):
        """Interface Louis's TicketStatusTool expects: memory.get_ticket(id) -> dict with these keys.
        (Contract check only - his tool is not implemented here.)"""
        m = self.mm("stu1"); r = self.run_tool(m)
        t = m.get_ticket(r["ticket"]["ticket_id"])
        for k in ("ticket_id", "status", "issue_summary", "created_at", "updated_at"):
            self.assertIn(k, t)
        self.assertIsNone(m.get_ticket("TICKET-9999"))
        self.assertIsNone(self.mm("stu2").get_ticket(r["ticket"]["ticket_id"]))


class TestDemoScript(unittest.TestCase):
    def test_demo_passes(self):  # 19
        import subprocess
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        p = subprocess.run([sys.executable, os.path.join(root, "src", "demo_memory.py")],
                           capture_output=True, text=True, cwd=root)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("RESULT: SUCCESS", p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
