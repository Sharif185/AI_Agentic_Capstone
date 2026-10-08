"""
Session State — Week 6 Memory Layer

Tracks a single conversation session between the student and the agent.
Ephemeral: exists in-memory during the conversation, then optionally
persisted to SQLite via PersistentMemory on session end.

Author: Aloysious Mutagubya (Application/Integration Lead)
"""

import uuid
from datetime import datetime, timezone


class SessionState:
    """
    In-memory state for one conversation session.

    Lifetime: Active conversation (max 30 days, then purged from DB).

    Fields:
        session_id          : Unique session identifier (SES-XXXXXXXX)
        user_id             : Optional student identifier for cross-session memory
        started_at          : ISO timestamp when session began
        last_active         : ISO timestamp of most recent interaction
        current_case        : Active ticket ID if a ticket was created this session
        preferences         : In-session preferences dict (language, tone, etc.)
        conversation_turns  : Count of student messages in this session
    """

    def __init__(self, session_id=None, user_id=None):
        self.session_id = session_id or self._generate_id()
        self.user_id = user_id
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.last_active = self.started_at
        self.current_case = None        # Active ticket ID (set when a ticket is created)
        self.preferences = {}           # In-session preferences only
        self.conversation_turns = 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique session ID with SES- prefix."""
        return f"SES-{uuid.uuid4().hex[:8]}"

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------

    def touch(self):
        """
        Record a new interaction: update last_active timestamp and
        increment the conversation turn counter.
        Called once per student message.
        """
        self.last_active = datetime.now(timezone.utc).isoformat()
        self.conversation_turns += 1

    def set_current_case(self, ticket_id: str):
        """
        Record the active ticket for this session.
        Called when create_support_ticket succeeds so the session
        is linked to the ticket in persistent memory.
        """
        self.current_case = ticket_id

    def set_preference(self, key: str, value):
        """Store an in-session preference (e.g., preferred language)."""
        self.preferences[key] = value

    # ------------------------------------------------------------------
    # Context export
    # ------------------------------------------------------------------

    def get_context(self) -> dict:
        """
        Return a lightweight dict suitable for injecting into the agent.
        Only includes fields the agent needs to reason about — not all
        session metadata.
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "current_case": self.current_case,
            "conversation_turns": self.conversation_turns,
            "preferences": self.preferences,
        }

    # ------------------------------------------------------------------
    # Serialisation / deserialisation (for DB persistence)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Serialise the full session state to a plain dict.
        Used by PersistentMemory.save_session().
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "started_at": self.started_at,
            "last_active": self.last_active,
            "current_case": self.current_case,
            "preferences": self.preferences,
            "conversation_turns": self.conversation_turns,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """
        Reconstruct a SessionState from a persisted dict.
        Used by PersistentMemory.load_session().
        """
        session = cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
        )
        session.started_at = data.get("started_at", session.started_at)
        session.last_active = data.get("last_active", session.last_active)
        session.current_case = data.get("current_case")
        session.preferences = data.get("preferences", {})
        session.conversation_turns = data.get("conversation_turns", 0)
        return session

    def __repr__(self) -> str:
        return (
            f"SessionState(session_id={self.session_id!r}, "
            f"user_id={self.user_id!r}, "
            f"turns={self.conversation_turns}, "
            f"current_case={self.current_case!r})"
        )
