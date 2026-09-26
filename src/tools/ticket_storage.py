import sqlite3
import json
import os
from datetime import datetime
 
class TicketStorage:
    """SQLite storage for support tickets."""
    
    def __init__(self, db_path="data/tickets.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()
    
    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    student_id TEXT,
                    issue_summary TEXT NOT NULL,
                    priority TEXT DEFAULT 'medium',
                    category TEXT DEFAULT 'other',
                    status TEXT DEFAULT 'open',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()
    
    def create_ticket(self, student_name, issue_summary, student_id=None,
                      priority="medium", category="other"):
        """Create a new ticket and return it."""
        # Generate ticket ID
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM tickets")
            count = cursor.fetchone()[0]
            ticket_id = f"TICKET-{count + 1:04d}"
            
            now = datetime.now().isoformat()
            conn.execute("""
                INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_id, student_name, student_id, issue_summary,
                priority, category, "open", now, now
            ))
            conn.commit()
        
        return self.get_ticket(ticket_id)
    
    def get_ticket(self, ticket_id):
        """Retrieve a ticket by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM tickets WHERE ticket_id = ?",
                (ticket_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def list_tickets(self, status=None):
        """List all tickets, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                cursor = conn.execute(
                    "SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM tickets ORDER BY created_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]
