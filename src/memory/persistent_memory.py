"""SQLite-backed persistent memory (Week 6).

Justified use case: CASE HISTORY. Stores sessions (metadata only), tickets
and approved preferences. Never stores conversation transcripts, credentials,
financial data, grades or medical data. All SQL uses bound parameters.
"""
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from memory.session_state import SessionState, parse_ts

SESSION_RETENTION_DAYS = 30
ACTIVE_TICKET_RETENTION_DAYS = 90
CLOSED_TICKET_RETENTION_DAYS = 365
CLOSED_STATUSES = ("closed", "resolved")

TICKET_FIELDS = (
    "ticket_id", "student_name", "student_id", "issue_summary",
    "priority", "category", "status", "created_at", "updated_at",
)

# Preference keys that must never be persisted (best-effort blocklist).
_PROHIBITED_KEY = re.compile(
    r"pass(word|code)?|pwd|secret|token|credential|pin\b|card|iban|account|bank|"
    r"salary|fee|payment|grade|gpa|mark|transcript|medical|health|diagnos|disab",
    re.IGNORECASE,
)
# Redacted from ticket summaries before storage (best-effort, not a guarantee).
_CRED_PHRASE = re.compile(r"(?i)\b(password|passcode|pin|pwd)\b\s*(is|:|=)\s*\S+")
_LONG_DIGITS = re.compile(r"\b(?:\d[ -]?){13,19}\b")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    started_at TEXT NOT NULL,
    last_active TEXT NOT NULL,
    current_case TEXT,
    conversation_turns INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions(last_active);

CREATE TABLE IF NOT EXISTS case_history (
    ticket_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id) ON DELETE SET NULL,
    student_name TEXT NOT NULL,
    student_id TEXT,
    issue_summary TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium',
    category TEXT NOT NULL DEFAULT 'other',
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_case_student ON case_history(student_id);

CREATE TABLE IF NOT EXISTS preferences (
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    approved INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, key)
);
"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def sanitize_text(text: str) -> str:
    """Redact credential-like phrases and long digit runs (card/account numbers)."""
    text = _CRED_PHRASE.sub(lambda m: f"{m.group(1)} [redacted]", text)
    return _LONG_DIGITS.sub("[redacted-number]", text)


class PersistentMemory:
    """CRUD + retention for sessions, tickets and approved preferences."""

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        directory = os.path.dirname(db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._create_tables()

    # ------------------------------------------------------------------ infra
    @contextmanager
    def _connect(self):
        """Open a connection, commit on success, roll back on error, always close."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _create_tables(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    # --------------------------------------------------------------- sessions
    def save_session(self, session_state: SessionState) -> None:
        """Insert or update session METADATA. In-session preferences are not stored."""
        s = session_state
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO sessions (session_id, user_id, started_at, last_active,
                                         current_case, conversation_turns)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(session_id) DO UPDATE SET
                       user_id=excluded.user_id, last_active=excluded.last_active,
                       current_case=excluded.current_case,
                       conversation_turns=excluded.conversation_turns""",
                (s.session_id, s.user_id, s.started_at, s.last_active,
                 s.current_case, s.conversation_turns),
            )

    def load_session(self, session_id: str) -> Optional[SessionState]:
        """Return the stored session or None if it does not exist."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        return SessionState.from_dict(dict(row)) if row else None

    def delete_session(self, session_id: str) -> bool:
        """Delete one session record (its tickets are kept, unlinked)."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            return cur.rowcount > 0

    def purge_old_sessions(self, days: int = SESSION_RETENTION_DAYS, now: Optional[datetime] = None) -> int:
        """Delete sessions not active for more than `days`. Returns rows removed."""
        cutoff = ((now or _now()) - timedelta(days=days)).isoformat()
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE last_active < ?", (cutoff,))
            return cur.rowcount

    # ---------------------------------------------------------------- tickets
    def save_ticket(self, ticket: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """Insert or update a ticket (keyed by ticket_id, so repeats never duplicate).

        Only whitelisted fields are stored; extra keys are dropped. Raises
        ValueError for missing required fields, or if the ticket_id already
        belongs to a different student (never overwrite someone else's record).
        """
        if not isinstance(ticket, dict):
            raise ValueError("ticket must be a dict")
        ticket_id = ticket.get("ticket_id")
        name = ticket.get("student_name")
        summary = ticket.get("issue_summary")
        if not (isinstance(ticket_id, str) and ticket_id.strip()):
            raise ValueError("ticket_id is required")
        if not (isinstance(name, str) and name.strip()):
            raise ValueError("student_name is required")
        if not (isinstance(summary, str) and summary.strip()):
            raise ValueError("issue_summary is required")

        now = _now().isoformat()
        created = ticket.get("created_at") if parse_ts(ticket.get("created_at")) else now
        updated = ticket.get("updated_at") if parse_ts(ticket.get("updated_at")) else created
        student_id = ticket.get("student_id")
        student_id = student_id.strip() if isinstance(student_id, str) and student_id.strip() else None

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT student_id FROM case_history WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
            if existing and existing["student_id"] and existing["student_id"] != student_id:
                raise ValueError(f"ticket_id {ticket_id} already belongs to a different student")
            conn.execute(
                """INSERT INTO case_history (ticket_id, session_id, student_name, student_id,
                       issue_summary, priority, category, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(ticket_id) DO UPDATE SET
                       session_id=COALESCE(excluded.session_id, case_history.session_id),
                       student_name=excluded.student_name, student_id=excluded.student_id,
                       issue_summary=excluded.issue_summary, priority=excluded.priority,
                       category=excluded.category, status=excluded.status,
                       updated_at=excluded.updated_at""",
                (ticket_id.strip(), session_id, name.strip(), student_id,
                 sanitize_text(summary.strip())[:500],
                 ticket.get("priority") or "medium", ticket.get("category") or "other",
                 ticket.get("status") or "open", created, updated),
            )
        return self.get_ticket(ticket_id.strip())

    @staticmethod
    def _row_to_ticket(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        return {k: d[k] for k in TICKET_FIELDS} | {"session_id": d["session_id"]}

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Return the ticket dict or None. (No access check: see MemoryManager.)"""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM case_history WHERE ticket_id = ?", (ticket_id,)).fetchone()
        return self._row_to_ticket(row) if row else None

    def get_tickets_by_student(self, student_id: str) -> List[Dict[str, Any]]:
        """All tickets for exactly this student_id, newest first."""
        if not student_id:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM case_history WHERE student_id = ? ORDER BY created_at DESC, ticket_id DESC",
                (student_id,),
            ).fetchall()
        return [self._row_to_ticket(r) for r in rows]

    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete exactly one ticket. Returns True if a row was removed."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM case_history WHERE ticket_id = ?", (ticket_id,))
            return cur.rowcount > 0

    def purge_expired_tickets(
        self,
        active_days: int = ACTIVE_TICKET_RETENTION_DAYS,
        closed_days: int = CLOSED_TICKET_RETENTION_DAYS,
        now: Optional[datetime] = None,
    ) -> int:
        """Delete open tickets idle > active_days and closed ones idle > closed_days
        (measured from updated_at). Returns rows removed."""
        now = now or _now()
        active_cut = (now - timedelta(days=active_days)).isoformat()
        closed_cut = (now - timedelta(days=closed_days)).isoformat()
        marks = ",".join("?" for _ in CLOSED_STATUSES)
        with self._connect() as conn:
            c1 = conn.execute(
                f"DELETE FROM case_history WHERE status NOT IN ({marks}) AND updated_at < ?",
                (*CLOSED_STATUSES, active_cut),
            )
            c2 = conn.execute(
                f"DELETE FROM case_history WHERE status IN ({marks}) AND updated_at < ?",
                (*CLOSED_STATUSES, closed_cut),
            )
            return c1.rowcount + c2.rowcount

    # ------------------------------------------------------------ preferences
    def save_preference(self, user_id: str, key: str, value: Any, approved: bool = True) -> bool:
        """Persist a preference ONLY if approved and not prohibited. Returns True if stored."""
        if not approved or not user_id or not isinstance(key, str) or not key.strip():
            return False
        text = value if isinstance(value, str) else json.dumps(value)
        if _PROHIBITED_KEY.search(key) or _LONG_DIGITS.search(text) or _CRED_PHRASE.search(text):
            return False
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO preferences (user_id, key, value, approved, updated_at)
                   VALUES (?, ?, ?, 1, ?)
                   ON CONFLICT(user_id, key) DO UPDATE SET
                       value=excluded.value, updated_at=excluded.updated_at""",
                (user_id, key.strip(), json.dumps(value), _now().isoformat()),
            )
        return True

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Approved preferences for this user as {key: value}."""
        if not user_id:
            return {}
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value FROM preferences WHERE user_id = ? AND approved = 1 ORDER BY key",
                (user_id,),
            ).fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    # --------------------------------------------------------------- deletion
    def delete_user_data(self, user_id: str) -> Dict[str, int]:
        """Delete every row tied to user_id, in one transaction."""
        if not user_id:
            return {"tickets": 0, "sessions": 0, "preferences": 0}
        with self._connect() as conn:
            t = conn.execute("DELETE FROM case_history WHERE student_id = ?", (user_id,)).rowcount
            s = conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,)).rowcount
            p = conn.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,)).rowcount
        return {"tickets": t, "sessions": s, "preferences": p}
