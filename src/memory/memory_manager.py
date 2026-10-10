"""MemoryManager: coordinates SessionState (one conversation) with
PersistentMemory (SQLite). Memory is assistive only: it never decides
grades, admissions or fees, and current instructions always win.

Identity note: the app has no real authentication. `user_id` is whatever the
caller supplies (self-declared). Access control here keys on that value and on
the active session; it is NOT a substitute for real authentication.
"""
from typing import Any, Dict, Optional

from memory.persistent_memory import PersistentMemory, SESSION_RETENTION_DAYS
from memory.session_state import SessionState

MAX_CONTEXT_TICKETS = 5
MAX_SUMMARY_CHARS = 120


class MemoryManager:
    """Session lifecycle, ticket persistence, memory context and deletion."""

    def __init__(self, db_path: str = "data/memory.db"):
        self.persistent = PersistentMemory(db_path)
        self.current_session: Optional[SessionState] = None

    # -------------------------------------------------------------- sessions
    def start_session(self, user_id: Optional[str] = None) -> str:
        """Enforce retention, create + persist a new session, return its ID."""
        self.purge_expired()
        self.current_session = SessionState(user_id=user_id)
        self.persistent.save_session(self.current_session)
        return self.current_session.session_id

    def resume_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """Restore a stored session if it exists and is within the 30-day window.

        If user_id is given it must match the stored owner. Returns False
        (and leaves the current session untouched) otherwise.
        """
        stored = self.persistent.load_session(session_id)
        if stored is None or stored.is_expired(SESSION_RETENTION_DAYS):
            return False
        if user_id is not None and stored.user_id != user_id:
            return False
        stored.touch()
        self.current_session = stored
        self.persistent.save_session(stored)
        return True

    def end_session(self) -> bool:
        """Persist and clear the active session. False if there was none."""
        if self.current_session is None:
            return False
        self.persistent.save_session(self.current_session)
        self.current_session = None
        return True

    def record_turn(self) -> None:
        """Count one conversation turn and persist session metadata."""
        if self.current_session is not None:
            self.current_session.touch()
            self.persistent.save_session(self.current_session)

    # --------------------------------------------------------------- tickets
    def save_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a ticket and link it to the current session.

        Requires an active session. If the session has a user_id, the ticket's
        student_id defaults to it, and a different student_id is rejected
        (ValueError) so one student cannot file memory under another's name.
        """
        sess = self.current_session
        if sess is None:
            raise ValueError("no active session")
        ticket = dict(ticket)
        sid = ticket.get("student_id")
        if sess.user_id:
            if not sid:
                ticket["student_id"] = sess.user_id
            elif sid != sess.user_id:
                raise ValueError("ticket student_id does not match the session user")
        self.persistent.save_session(sess)  # FK target must exist first
        saved = self.persistent.save_ticket(ticket, session_id=sess.session_id)
        sess.set_current_case(saved["ticket_id"])
        self.persistent.save_session(sess)
        return saved

    def _can_access(self, ticket: Dict[str, Any]) -> bool:
        sess = self.current_session
        if sess is None:
            return False
        if ticket.get("student_id"):
            return sess.user_id is not None and ticket["student_id"] == sess.user_id
        return ticket.get("session_id") == sess.session_id  # unowned: same session only

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Return a ticket only if it belongs to the current student/session, else None.

        Knowing a ticket ID alone is not enough.
        """
        ticket = self.persistent.get_ticket(ticket_id)
        return ticket if ticket and self._can_access(ticket) else None

    # ---------------------------------------------------------- preferences
    def set_preference(self, key: str, value: Any, approved: bool = False) -> bool:
        """Set a preference for this session; persist only if approved and the
        session has a user_id. Returns True if it was persisted."""
        sess = self.current_session
        if sess is None:
            return False
        sess.preferences[key] = value
        if approved and sess.user_id:
            return self.persistent.save_preference(sess.user_id, key, value, approved=True)
        return False

    # -------------------------------------------------------------- context
    def get_memory_context(self, user_id: Optional[str]) -> str:
        """Concise text for the planner prompt. Empty unless the active session
        belongs to exactly this user_id. Only that student's records are used."""
        sess = self.current_session
        if not user_id or sess is None or sess.user_id != user_id:
            return ""
        tickets = self.persistent.get_tickets_by_student(user_id)
        prefs = self.persistent.get_preferences(user_id)
        if not tickets and not prefs and not sess.current_case:
            return ""
        lines = []
        if tickets:
            lines.append(f"Prior tickets for this student: {len(tickets)}")
            for t in tickets[:MAX_CONTEXT_TICKETS]:
                summary = t["issue_summary"]
                if len(summary) > MAX_SUMMARY_CHARS:
                    summary = summary[:MAX_SUMMARY_CHARS - 3] + "..."
                lines.append(
                    f"- {t['ticket_id']}: {summary} (status: {t['status']}, "
                    f"category: {t['category']}, created: {t['created_at'][:10]})"
                )
        if sess.current_case:
            lines.append(f"Active case this session: {sess.current_case}")
        if prefs:
            lines.append("Approved preferences: " + ", ".join(f"{k}={v}" for k, v in prefs.items()))
        lines.append("Note: remembered context only. Confirm with the student before treating a new issue as the same as a prior one.")
        return "\n".join(lines)

    # ------------------------------------------------------------- retention
    def purge_expired(self) -> Dict[str, int]:
        """Apply retention: sessions > 30d, open tickets > 90d, closed > 1y."""
        return {
            "sessions": self.persistent.purge_old_sessions(),
            "tickets": self.persistent.purge_expired_tickets(),
        }

    # -------------------------------------------------------------- deletion
    def delete_session_data(self) -> bool:
        """Delete ONLY the active session record (tickets and preferences remain)."""
        sess = self.current_session
        if sess is None:
            return False
        ok = self.persistent.delete_session(sess.session_id)
        self.current_session = None
        return ok

    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete ONE ticket, only if the current student/session may access it."""
        return self.get_ticket(ticket_id) is not None and self.persistent.delete_ticket(ticket_id)

    def delete_all_data(self, user_id: str) -> Dict[str, int]:
        """Right to be forgotten: delete this student's tickets, sessions and
        preferences from memory. Allowed only for the active session's own user.

        Does NOT touch data/support_tickets.json (the ticket tool's own store).
        """
        sess = self.current_session
        if not user_id or sess is None or sess.user_id != user_id:
            return {"tickets": 0, "sessions": 0, "preferences": 0, "denied": 1}
        counts = self.persistent.delete_user_data(user_id)
        self.current_session = None
        return counts
