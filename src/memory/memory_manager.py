"""
Memory Manager — Week 6 Memory Layer

High-level interface that coordinates SessionState (ephemeral) and
PersistentMemory (SQLite). This is the single entry-point the agent
and demo scripts use — they never touch PersistentMemory directly.

Author: Aloysious Mutagubya (Application/Integration Lead)
"""

from memory.session_state import SessionState
from memory.persistent_memory import PersistentMemory

# Maximum tickets shown in the memory context injected into the agent prompt.
# Keeps prompts from growing unboundedly when a student has many tickets.
MAX_CONTEXT_TICKETS = 3


class MemoryManager:
    """
    Coordinates session state and persistent memory.

    Usage (new session):
        mm = MemoryManager()
        session_id = mm.start_session(user_id='student_001')
        mm.save_ticket({'ticket_id': 'TICKET-0001', ...})
        context = mm.get_memory_context('student_001')
        mm.end_session()

    Usage (resume existing session):
        mm = MemoryManager()
        found = mm.resume_session('SES-abc12345')
        if not found:
            mm.start_session(user_id='student_001')
    """

    def __init__(self, db_path: str = "data/memory.db"):
        self.persistent = PersistentMemory(db_path)
        self.current_session: SessionState | None = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(self, user_id: str = None) -> str:
        """
        Start a brand-new session. Returns the new session_id.

        Parameters
        ----------
        user_id : str, optional
            Student identifier for cross-session memory lookups.
            If None, memory context will be empty (anonymous session).
        """
        self.current_session = SessionState(user_id=user_id)
        return self.current_session.session_id

    def resume_session(self, session_id: str) -> bool:
        """
        Attempt to resume a previously saved session.

        Returns True if the session was found and loaded, False if not.
        The caller should fall back to start_session() on False.
        """
        session = self.persistent.load_session(session_id)
        if session:
            self.current_session = session
            self.current_session.touch()  # Mark as active again
            return True
        return False

    def end_session(self):
        """
        Persist the current session to the database and clear it from memory.
        Call this when the conversation ends (user says 'exit', timeout, etc.).
        """
        if self.current_session:
            self.persistent.save_session(self.current_session)
            self.current_session = None

    # ------------------------------------------------------------------
    # Ticket operations
    # ------------------------------------------------------------------

    def save_ticket(self, ticket: dict):
        """
        Save a ticket to persistent memory and link it to the current session.

        Also updates the current session's active case to this ticket_id,
        so the session record remembers what ticket was created.

        ticket must contain at minimum:
            ticket_id, student_name, issue_summary, created_at, updated_at
        """
        session_id = (
            self.current_session.session_id if self.current_session else None
        )
        self.persistent.save_ticket(ticket, session_id=session_id)

        # Update the current session's active case
        if self.current_session:
            self.current_session.set_current_case(ticket["ticket_id"])

    def get_ticket(self, ticket_id: str) -> dict | None:
        """Retrieve a ticket by ID. Returns None if not found."""
        return self.persistent.get_ticket(ticket_id)

    # ------------------------------------------------------------------
    # Memory context for prompt injection
    # ------------------------------------------------------------------

    def get_memory_context(self, user_id: str) -> str:
        """
        Build a concise memory context string for injection into the
        agent's planning prompt.

        Format:
            MEMORY CONTEXT:
            Prior tickets: 2
              - TICKET-0001: Cannot access registration portal (open, created 2026-10-05)
              - TICKET-0002: Exam schedule question (closed, created 2026-09-28)

        Returns an empty string if:
          - user_id is None
          - No tickets found for this student
        Limits output to MAX_CONTEXT_TICKETS (default 3) to avoid
        overflowing the prompt with stale context.
        """
        if not user_id:
            return ""

        tickets = self.persistent.get_tickets_by_student(user_id)
        if not tickets:
            return ""

        # Truncate to the most recent MAX_CONTEXT_TICKETS
        recent = tickets[:MAX_CONTEXT_TICKETS]

        lines = ["MEMORY CONTEXT:", f"Prior tickets: {len(tickets)}"]
        for t in recent:
            date_str = t.get("created_at", "")[:10]  # YYYY-MM-DD
            lines.append(
                f"  - {t['ticket_id']}: {t['issue_summary']} ({t['status']}, created {date_str})"
            )

        if len(tickets) > MAX_CONTEXT_TICKETS:
            lines.append(
                f"  ... and {len(tickets) - MAX_CONTEXT_TICKETS} older ticket(s) not shown"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Privacy — Right to be Forgotten
    # ------------------------------------------------------------------

    def delete_all_data(self, user_id: str) -> dict:
        """
        Permanently delete all data for a student (right to be forgotten).

        Removes:
          - All tickets in case_history for this student
          - All sessions for this student
          - All preferences for this student

        Returns a summary dict with counts of deleted records.
        Also clears the current session if it belongs to this user.
        """
        # Gather tickets first so we can delete them individually
        tickets = self.persistent.get_tickets_by_student(user_id)
        deleted_tickets = 0
        for ticket in tickets:
            if self.persistent.delete_ticket(ticket["ticket_id"]):
                deleted_tickets += 1

        deleted_sessions = self.persistent.delete_sessions(user_id)
        deleted_prefs = self.persistent.delete_preferences(user_id)

        # Clear the active session if it belongs to this user
        if self.current_session and self.current_session.user_id == user_id:
            self.current_session = None

        return {
            "deleted_tickets": deleted_tickets,
            "deleted_sessions": deleted_sessions,
            "deleted_preferences": deleted_prefs,
            "user_id": user_id,
        }

    # ------------------------------------------------------------------
    # Preference pass-throughs
    # ------------------------------------------------------------------

    def save_preference(self, user_id: str, key: str, value, approved: bool = True):
        """Save an approved user preference to persistent memory."""
        self.persistent.save_preference(user_id, key, value, approved=approved)

    def get_preferences(self, user_id: str) -> dict:
        """Retrieve all approved preferences for a user."""
        return self.persistent.get_preferences(user_id)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def purge_expired_data(self):
        """
        Run all retention-policy purges:
          - Sessions inactive > 30 days
          - Open tickets > 90 days old
          - Closed tickets > 1 year old

        Returns a summary of what was removed.
        """
        purged_sessions = self.persistent.purge_old_sessions(days=30)
        purged_open = self.persistent.purge_old_tickets(status="open", days=90)
        purged_closed = self.persistent.purge_old_tickets(status="closed", days=365)
        return {
            "purged_sessions": purged_sessions,
            "purged_open_tickets": purged_open,
            "purged_closed_tickets": purged_closed,
        }

    def get_stats(self) -> dict:
        """Return database statistics for monitoring/debugging."""
        stats = self.persistent.get_stats()
        stats["active_session"] = (
            self.current_session.session_id if self.current_session else None
        )
        return stats

    def __repr__(self) -> str:
        session_info = (
            self.current_session.session_id if self.current_session else "None"
        )
        return f"MemoryManager(db={self.persistent.db_path!r}, session={session_info})"
