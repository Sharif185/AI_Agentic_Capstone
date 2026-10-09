"""Session state: in-memory state for ONE conversation (Week 6).

Kept separate from AgentState (one agent run) and PersistentMemory (SQLite).
Timestamps are timezone-aware UTC ISO-8601 strings so they sort and compare
consistently.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

SESSION_RETENTION_DAYS = 30


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ts(value: Any) -> Optional[datetime]:
    """Parse an ISO timestamp (naive values are treated as UTC). None if invalid."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class SessionState:
    """State for a single conversation."""

    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None):
        self.session_id: str = session_id or self._generate_id()
        self.user_id: Optional[str] = user_id
        self.started_at: str = _now_iso()
        self.last_active: str = self.started_at
        self.current_case: Optional[str] = None
        # In-session ONLY. Never written to the database: only approved
        # preferences are persisted, via PersistentMemory.save_preference().
        self.preferences: Dict[str, Any] = {}
        self.conversation_turns: int = 0

    @staticmethod
    def _generate_id() -> str:
        return f"SES-{uuid.uuid4().hex[:8]}"

    def touch(self) -> None:
        """Record activity: update last_active and count one conversation turn."""
        self.last_active = _now_iso()
        self.conversation_turns += 1

    def set_current_case(self, ticket_id: Optional[str]) -> None:
        """Associate this session with a ticket (the active case)."""
        self.current_case = ticket_id
        self.last_active = _now_iso()

    def get_context(self) -> Dict[str, Any]:
        """Small dict suitable for injecting into the agent (no timestamps)."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "current_case": self.current_case,
            "preferences": dict(self.preferences),
            "conversation_turns": self.conversation_turns,
        }

    def is_expired(self, days: int = SESSION_RETENTION_DAYS, now: Optional[datetime] = None) -> bool:
        """True when last_active is older than the retention window (or unreadable)."""
        last = parse_ts(self.last_active)
        if last is None:
            return True
        now = now or datetime.now(timezone.utc)
        return now - last > timedelta(days=days)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "started_at": self.started_at,
            "last_active": self.last_active,
            "current_case": self.current_case,
            "preferences": dict(self.preferences),
            "conversation_turns": self.conversation_turns,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "SessionState":
        """Rebuild a session; missing or invalid fields fall back to safe defaults."""
        data = data if isinstance(data, dict) else {}
        sid = data.get("session_id")
        uid = data.get("user_id")
        obj = cls(
            session_id=sid if isinstance(sid, str) and sid.strip() else None,
            user_id=uid if isinstance(uid, str) and uid.strip() else None,
        )
        started = data.get("started_at")
        if parse_ts(started):
            obj.started_at = started
        last = data.get("last_active")
        obj.last_active = last if parse_ts(last) else obj.started_at
        case = data.get("current_case")
        obj.current_case = case if isinstance(case, str) and case.strip() else None
        prefs = data.get("preferences")
        obj.preferences = dict(prefs) if isinstance(prefs, dict) else {}
        turns = data.get("conversation_turns")
        obj.conversation_turns = turns if isinstance(turns, int) and not isinstance(turns, bool) and turns >= 0 else 0
        return obj
