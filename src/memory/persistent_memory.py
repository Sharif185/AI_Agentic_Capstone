"""
Persistent Memory — Week 6 Memory Layer

SQLite-backed storage for cross-session data: tickets (case history),
session metadata, and student preferences.

Three tables:
  - sessions      : saved session metadata (30-day retention)
  - case_history  : support tickets (90 days open, 1 year closed)
  - preferences   : approved student preferences

Author: Aloysious Mutagubya (Application/Integration Lead)
"""

import json
import os
import sqlite3
from datetime import datetime, timezone, timedelta

from memory.session_state import SessionState


class PersistentMemory:
    """
    SQLite-backed persistent memory store.

    Owns the database schema, all CRUD operations, and retention
    enforcement. Does NOT hold any in-memory session state — that
    lives in SessionState. This class is purely a storage layer.

    Usage:
        pm = PersistentMemory('data/memory.db')
        pm.save_ticket({'ticket_id': 'TICKET-0001', ...})
        ticket = pm.get_ticket('TICKET-0001')
    """

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        # Ensure the data directory exists before SQLite tries to create the file
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema setup
    # ------------------------------------------------------------------

    def _create_tables(self):
        """Create all three tables if they don't already exist."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id          TEXT PRIMARY KEY,
                    user_id             TEXT,
                    started_at          TEXT NOT NULL,
                    last_active         TEXT NOT NULL,
                    current_case        TEXT,
                    preferences         TEXT DEFAULT '{}',
                    conversation_turns  INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS case_history (
                    ticket_id       TEXT PRIMARY KEY,
                    student_name    TEXT NOT NULL,
                    student_id      TEXT,
                    issue_summary   TEXT NOT NULL,
                    priority        TEXT DEFAULT 'medium',
                    category        TEXT DEFAULT 'other',
                    status          TEXT DEFAULT 'open',
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    session_id      TEXT
                );

                CREATE TABLE IF NOT EXISTS preferences (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     TEXT NOT NULL,
                    key         TEXT NOT NULL,
                    value       TEXT NOT NULL,
                    approved    INTEGER DEFAULT 1,
                    created_at  TEXT NOT NULL,
                    UNIQUE(user_id, key)
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        """Return a new SQLite connection with row_factory set."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row   # rows accessible as dicts
        return conn

    # ------------------------------------------------------------------
    # Session operations
    # ------------------------------------------------------------------

    def save_session(self, session_state: SessionState):
        """
        Insert or replace a session record in the sessions table.
        Called by MemoryManager.end_session().
        """
        data = session_state.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions
                    (session_id, user_id, started_at, last_active,
                     current_case, preferences, conversation_turns)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["session_id"],
                    data.get("user_id"),
                    data["started_at"],
                    data["last_active"],
                    data.get("current_case"),
                    json.dumps(data.get("preferences", {})),
                    data.get("conversation_turns", 0),
                ),
            )

    def load_session(self, session_id: str):
        """
        Load a session by ID. Returns a SessionState if found, else None.
        Called by MemoryManager.resume_session().
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()

        if row is None:
            return None

        data = dict(row)
        data["preferences"] = json.loads(data.get("preferences") or "{}")
        return SessionState.from_dict(data)

    def purge_old_sessions(self, days: int = 30):
        """
        Delete session records whose last_active is older than `days`.
        Retention policy: 30 days from last activity.
        Returns the number of rows deleted.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE last_active < ?", (cutoff,)
            )
            return cursor.rowcount

    # ------------------------------------------------------------------
    # Ticket (case history) operations
    # ------------------------------------------------------------------

    def save_ticket(self, ticket: dict, session_id: str = None):
        """
        Insert or replace a ticket in the case_history table.

        ticket must have at minimum:
            ticket_id, student_name, issue_summary, created_at, updated_at

        Optional fields default to sensible values.
        session_id links the ticket to the session that created it.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO case_history
                    (ticket_id, student_name, student_id, issue_summary,
                     priority, category, status, created_at, updated_at, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket["ticket_id"],
                    ticket.get("student_name", "Unknown"),
                    ticket.get("student_id"),
                    ticket.get("issue_summary", ""),
                    ticket.get("priority", "medium"),
                    ticket.get("category", "other"),
                    ticket.get("status", "open"),
                    ticket.get("created_at", now),
                    ticket.get("updated_at", now),
                    session_id or ticket.get("session_id"),
                ),
            )

    def get_ticket(self, ticket_id: str) -> dict | None:
        """
        Retrieve a single ticket by ticket_id.
        Returns a dict if found, None if not.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM case_history WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_tickets_by_student(self, student_id: str) -> list[dict]:
        """
        Retrieve all tickets for a student, ordered most-recent first.
        Matches on student_id column.
        Returns a list of dicts (empty if no tickets found).
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM case_history
                WHERE student_id = ?
                ORDER BY created_at DESC
                """,
                (student_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """
        Update a ticket's status (e.g., open → closed).
        Returns True if a row was updated, False if not found.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE case_history SET status = ?, updated_at = ? WHERE ticket_id = ?",
                (status, now, ticket_id),
            )
            return cursor.rowcount > 0

    def delete_ticket(self, ticket_id: str) -> bool:
        """
        Permanently delete a ticket. Used by delete_all_data() and
        right-to-be-forgotten requests.
        Returns True if a row was deleted, False if not found.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM case_history WHERE ticket_id = ?", (ticket_id,)
            )
            return cursor.rowcount > 0

    def purge_old_tickets(self, status: str = "closed", days: int = 365) -> int:
        """
        Delete tickets of a given status older than `days`.
        Retention policy:
          - open tickets:   90 days from created_at  (call with status='open',   days=90)
          - closed tickets: 1 year from updated_at   (call with status='closed', days=365)
        Returns number of rows deleted.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        date_col = "updated_at" if status == "closed" else "created_at"
        with self._connect() as conn:
            cursor = conn.execute(
                f"DELETE FROM case_history WHERE status = ? AND {date_col} < ?",
                (status, cutoff),
            )
            return cursor.rowcount

    # ------------------------------------------------------------------
    # Preference operations
    # ------------------------------------------------------------------

    def save_preference(self, user_id: str, key: str, value, approved: bool = True):
        """
        Upsert a user preference.
        Only approved preferences are stored (approved=True by default).
        Ignores unapproved preferences to enforce consent.
        """
        if not approved:
            return  # Never store preferences the student hasn't approved

        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO preferences (user_id, key, value, approved, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value, approved = excluded.approved
                """,
                (user_id, key, str(value), int(approved), now),
            )

    def get_preferences(self, user_id: str) -> dict:
        """
        Retrieve all approved preferences for a user as a flat dict.
        Returns empty dict if no preferences found.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value FROM preferences WHERE user_id = ? AND approved = 1",
                (user_id,),
            ).fetchall()
        return {row["key"]: row["value"] for row in rows}

    def delete_preferences(self, user_id: str) -> int:
        """Delete all preferences for a user (right to be forgotten)."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM preferences WHERE user_id = ?", (user_id,)
            )
            return cursor.rowcount

    def delete_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user (right to be forgotten)."""
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE user_id = ?", (user_id,)
            )
            return cursor.rowcount

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return basic DB stats (useful for debugging and monitoring)."""
        with self._connect() as conn:
            n_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            n_tickets = conn.execute("SELECT COUNT(*) FROM case_history").fetchone()[0]
            n_open = conn.execute(
                "SELECT COUNT(*) FROM case_history WHERE status='open'"
            ).fetchone()[0]
            n_prefs = conn.execute("SELECT COUNT(*) FROM preferences").fetchone()[0]
        return {
            "sessions": n_sessions,
            "tickets_total": n_tickets,
            "tickets_open": n_open,
            "preferences": n_prefs,
            "db_path": self.db_path,
        }
