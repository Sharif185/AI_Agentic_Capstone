# Memory Design and Data Handling Note

**Project:** University Student-Support Case Agent  
**Version:** 1.0  
**Date:** 5th October 2026  
**Author:** Sharif Ssentaayi (Project/Requirements Lead)

---

## 1. Purpose

This document defines what the agent remembers, why, who can access it, how long it's kept, and how it's deleted.

The agent implements **justified, bounded persistent memory** for a single, well-defined use case: **case history memory**. This improves legitimate support tasks without expanding into areas where memory should not be applied (grades, admissions, financial decisions).

---

## 2. Memory Use Case: Case History

### What is stored?

| Data | Example | Justification |
|------|---------|---------------|
| Ticket ID | TICKET-0001 | For status lookup |
| Student name | John Doe | For follow-up context |
| Student ID | 2024/BCS/001 | For identification |
| Issue summary | 'Cannot access portal' | To recall the issue |
| Priority | high | For triage context |
| Category | registration | For routing |
| Status | open | For status queries |
| Created timestamp | 2026-10-05T10:30 | For chronology |
| Updated timestamp | 2026-10-05T14:20 | For tracking changes |
| Session ID | SES-a1b2c3d4 | To link session to case |

### What is NOT stored?

- **Passwords or credentials** — Never stored
- **Financial information** — No tuition balances, payment details, or account numbers
- **Grades or academic records** — No exam scores, GPAs, or transcript data
- **Medical or health information** — No medical records or health-related data
- **Any data the student didn't explicitly provide** — No inferred or assumed information
- **Conversation transcripts** — Only structured summaries (ticket data), not full conversations

---

## 3. Why Store It?

### Legitimate Task Improvement

**The Problem Without Memory:**  
When a student creates a support ticket in Session 1 and returns in Session 2 to ask "What's the status of my ticket?", the agent has no context. The student must:
1. Re-explain their issue
2. Remember their ticket ID (if they even know it)
3. Re-state their name and details

This creates friction and wastes the student's time.

**The Solution With Memory:**  
The agent remembers the ticket from Session 1. In Session 2, when the student asks about status, the agent:
1. Retrieves the ticket by student ID
2. Answers immediately: "Your ticket TICKET-0001 about 'Cannot access portal' is currently open"
3. No re-explanation needed

### Follow-Up Continuity

Students often return days later to check on issues. Memory enables smooth follow-up without starting from scratch each time.

### Audit Trail

Stored tickets provide a record of what issues were raised, when, and by whom — useful for support staff reviewing case history.

---

## 4. Who Can Access It?

| Actor | Access Level | What They See | Authorization Method |
|-------|-------------|---------------|----------------------|
| **Student (owner)** | Read own tickets | Only tickets they created (matched by student_id or session_id) | Session-based (user_id matching) |
| **Support Staff** | Read all tickets | All open tickets, for triage and follow-up | Role-based (future: staff authentication) |
| **Developer (test/debug)** | Read all data | Full database access for debugging | Direct database access (dev environment only) |
| **External Systems** | No access | None | Not implemented |

**Note:** In the current implementation (Week 6), access control is session-based: the agent retrieves tickets for the current `user_id`. Future work (Week 7+) may add role-based access control for support staff.

---

## 5. Retention Policy

| Data Type | Active Retention | Closed Retention | Total Maximum |
|-----------|------------------|------------------|---------------|
| **Open Tickets** | 90 days from creation | N/A (not closed) | 90 days |
| **Closed Tickets** | N/A (already closed) | 1 year from closure | 1 year + active time |
| **Session State** | 30 days from last activity | N/A (expires) | 30 days |
| **Preferences** | Indefinite (while account active) | Deleted on account closure | No hard limit |

### Rationale

- **90 days for open tickets:** Most student issues are resolved within weeks. 90 days provides sufficient time for follow-up without indefinite retention.
- **1 year for closed tickets:** Allows students to reference historical issues (e.g., "I had a similar problem last semester").
- **30 days for sessions:** Balances usefulness (students can resume recent conversations) with privacy (stale sessions are purged).

### Automatic Purging

The system implements `purge_old_sessions(days=30)` and `purge_old_tickets(status='closed', days=365)` methods. These are called:
- Daily via a scheduled job (future implementation)
- On-demand during maintenance
- Before archival/backup operations

---

## 6. Deletion Policy

### User Request (Right to be Forgotten)

Students can request deletion of their data at any time. When invoked:
- `delete_all_data(user_id)` removes:
  - All tickets created by that student
  - All session history for that student
  - All preferences for that student
- Deletion is **immediate and irreversible**
- Confirmation message: "Your data has been permanently deleted."

### Automatic Deletion Triggers

1. **Session expiry:** Sessions inactive for 30+ days are purged automatically
2. **Ticket closure + retention:** Closed tickets older than 1 year are purged automatically
3. **Account closure:** If a student graduates or leaves, all their data is purged (future: tied to university account lifecycle)

### What Cannot Be Deleted

- **Aggregated statistics** — Anonymized counts (e.g., "50 tickets created in October") are retained for reporting
- **Audit logs** — Minimal audit trail (timestamp, action type, no PII) retained for 2 years for security compliance

---

## 7. What Memory Does NOT Control

Memory is **assistive only** — it informs the agent's responses but **never makes decisions** on its own.

| Decision Type | Memory Role | Who Decides |
|---------------|-------------|-------------|
| **Grades** | None — grades are never stored | Academic staff only |
| **Admissions** | None — admissions data is never stored | Admissions office only |
| **Fees** | None — financial data is never stored | Finance office only |
| **Ticket Routing** | Memory provides context (category, priority) | Support staff triages manually |
| **Issue Resolution** | Memory recalls the issue; agent doesn't "solve" it autonomously | Student + support staff |

### Memory Boundary Rules

1. **Current session always wins:** If a student says "Actually, my issue is X" in the current conversation, memory is ignored — the agent uses what the student is saying NOW.
2. **No assumptions:** If memory shows a prior ticket about "registration", and the student asks a new question, the agent does NOT assume the new question is about registration unless stated.
3. **Stale memory flagged:** If a ticket is >90 days old and still open, the agent flags it: "This ticket is quite old — would you like to create a new one instead?"

---

## 8. Data Security

### Storage

- **Technology:** SQLite (local file-based database)
- **Location:** `data/memory.db` (inside the project directory)
- **Encryption:** File system-level (OS-dependent; future: encrypted SQLite extension)
- **Backups:** Daily backups to `data/backups/` (retained for 7 days)

### Access Control

- **Session-based:** Agent only retrieves data for the current `user_id`
- **No shared sessions:** Each session is isolated; students cannot access each other's data
- **Access logging:** Every memory read/write is logged with timestamp and action type (not content)

### Network Exposure

- **Current state (Week 6):** Local only — no network access
- **Future state (Week 7+):** If deployed as a service, API authentication required (JWT tokens, API keys)

---

## 9. Consent

### Student Informed Consent

When a ticket is created, the agent informs the student:

> "I'm creating a support ticket for you. Your name, student ID, and issue summary will be stored so support staff can follow up. This information will be kept for 90 days (for open tickets) or 1 year (for closed tickets). You can request deletion at any time by asking me to 'delete my data'."

### Opt-Out

Students can opt out of memory:
- **Per-session opt-out:** "Don't remember this session" — session is not saved to persistent memory
- **Full opt-out:** "Delete all my data" — all stored data is purged immediately

Opting out disables cross-session memory but does NOT prevent ticket creation (tickets are the core support mechanism).

---

## 10. Example Flow

### Session 1: Student Creates Ticket

**Student:** "I can't access the online registration portal."

**Agent Actions:**
1. Uses RAG to check if there's a known solution
2. RAG returns no direct answer
3. Calls `create_support_ticket`:
   - `student_name`: "Demo Student"
   - `student_id`: "demo_student"
   - `issue_summary`: "Cannot access online registration portal"
   - `priority`: "high"
   - `category`: "registration"
4. Ticket saved to persistent memory: `TICKET-0001`
5. Session state saved: `SES-abc123` linked to `demo_student`

**Agent Response:**
> "I've created a support ticket (TICKET-0001) for your issue. A staff member will follow up within 24 hours. Your ticket details have been saved."

### Session 2: Student Returns Next Day

**Student:** "What's the status of my ticket?"

**Agent Actions:**
1. Agent loads memory context for `user_id='demo_student'`
2. Memory returns: "Prior tickets: 1 — TICKET-0001: Cannot access online registration portal (open)"
3. Calls `check_ticket_status('TICKET-0001')`
4. Returns ticket details

**Agent Response:**
> "Your ticket TICKET-0001 about 'Cannot access online registration portal' is currently open. It was created yesterday at 10:00 AM. A staff member will follow up within 24 hours."

**Key Improvement:**  
Student did NOT need to:
- Re-explain the issue
- Remember the ticket ID
- Re-state their name

The agent knew who they were and what they needed.

---

## 11. Compliance Notes

### Privacy

- **No PII beyond what students explicitly provide:** Agent does not infer, assume, or collect data beyond what's in the conversation
- **No conversation recording:** Full conversations are NOT stored — only structured ticket data
- **Minimal data principle:** Only ticket-relevant fields are stored (name, ID, issue, priority, category, timestamps)

### Third-Party Sharing

- **Current:** No data is shared with third parties
- **Future:** If integrated with external ticket systems (e.g., Jira, ServiceNow), data sharing must be explicitly consented to

### Regulatory Compliance

- **GDPR-aligned (right to be forgotten):** Students can request deletion at any time
- **Data minimization:** Only necessary fields are stored
- **Purpose limitation:** Data is used only for support ticket management, not for marketing, analytics, or unrelated purposes
- **Retention limits:** Data is not kept indefinitely; automatic purging enforced

---

## 12. Future Enhancements (Post-Week 6)

1. **Encrypted database:** Use SQLCipher for encrypted SQLite storage
2. **Role-based access control:** Support staff can view all tickets; students see only their own
3. **Audit trail UI:** Students can view a log of what was stored and when
4. **Fine-grained consent:** Students can consent to ticket storage but opt out of session history
5. **Integration with university identity system:** Tie `user_id` to university SSO for authentication

---

## Summary

**Week 6 Memory Design:**
- ✅ Justified use case: Case history memory (ticket status lookups)
- ✅ Bounded storage: Only ticket data, no grades/finances/medical
- ✅ Retention policy: 90 days (open), 1 year (closed), 30 days (sessions)
- ✅ Deletion on request: `delete_all_data(user_id)` available immediately
- ✅ Assistive only: Memory never controls decisions
- ✅ Privacy-first: Minimal data, no PII beyond user input, no third-party sharing
- ✅ Consent: Students informed when data is stored, can opt out anytime

**What This Enables:**  
Students return to ask "What's my ticket status?" and get an instant answer — no re-explanation needed.

**What This Does NOT Do:**  
Store grades, make admissions decisions, or retain data indefinitely.

---

**Document Version:** 1.0  
**Next Review:** Week 7 (after evaluation and guardrails)  
**Owner:** Sharif Ssentaayi (Project/Requirements Lead)
