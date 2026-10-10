# Memory Design and Data Handling Note

## Project: University Student-Support Case Agent
## Version: 1.0
## Date: 5th October 2026
## Author: Sharif (Project/Requirements Lead)
## Status: Draft

---

## 1. Purpose

This document defines what the agent remembers, why, who can access it, how long it is kept, and how it is deleted. It ensures the agent handles student data responsibly, minimally, and transparently.

---

## 2. Memory Use Case: Case History

### What is stored?

| Data | Example | Justification |
|------|---------|---------------|
| Ticket ID | TICKET-0001 | For status lookup |
| Student name | John Doe | For follow-up context |
| Student ID | 2024/BCS/001 | For identification |
| Issue summary | "Cannot access portal" | To recall the issue |
| Priority | high | For triage context |
| Category | registration | For routing |
| Status | open | For status queries |
| Created timestamp | 2026-10-05T10:30 | For chronology |
| Session ID | SES-a1b2c3d4 | To link session to case |

### What is NOT stored?

- Passwords or credentials
- Financial information
- Grades or academic records
- Medical or health information
- Any data the student did not explicitly provide
- Full conversation transcripts (only summaries are stored)

---

## 3. Why Store It?

| Reason | Explanation |
|--------|-------------|
| Legitimate task | The agent needs case data to look up ticket status across sessions |
| Follow-up | Support staff need context to resolve the issue after hand-off |
| Continuity | A returning student should not have to repeat their issue |
| Audit | A record of actions taken allows review if something goes wrong |

Storage is limited strictly to what is necessary for these four purposes. No data is stored speculatively or for future use beyond the stated scope.

---

## 4. Who Can Access It?

| Role | Access Level | Scope |
|------|-------------|-------|
| Student | Read own tickets only | Can query status of their own cases by ticket ID or session |
| Support staff | Read and write all tickets | Can view, update, and close tickets assigned to their department |
| Developer | Read (anonymised) | Can access logs and summaries for debugging — no raw PII |
| External parties | ❌ No access | No data is shared with third parties under any circumstances |

---

## 5. Retention Policy

| Data Type | Retention Period | Reason |
|-----------|-----------------|--------|
| Active tickets | 90 days from creation | Sufficient time for resolution and follow-up |
| Closed tickets | 1 year from closure | Audit trail and potential re-opening |
| Session records | 30 days from session end | Short-term continuity only |
| Anonymised logs | 2 years | System monitoring and quality review |

After the retention period expires, data is automatically scheduled for deletion per Section 6.

---

## 6. Deletion Policy

| Trigger | Action |
|---------|--------|
| User request | Student may request deletion of their data at any time; all associated tickets and session records are deleted within 7 days |
| Automatic expiry | Data past its retention period is deleted on the next scheduled cleanup run |
| Right to be forgotten | Honoured in full — all identifiable data removed; anonymised aggregates may be retained |
| Account closure | All associated data deleted within 30 days |

> The agent itself cannot delete data. Deletion requests are handled by the support system and reviewed by a staff member before execution.

---

## 7. What Memory Does NOT Control

The agent's memory is strictly limited to case history. It does NOT:

- Influence or store grades or academic standing
- Make or record admissions or enrollment decisions
- Retain stale information past the retention period
- Override or supplement official university records
- Store inferred data (e.g., assumptions about a student's situation not stated explicitly)

If stored information conflicts with official university records, the official records take precedence.

---

## 8. Data Security

| Measure | Detail |
|---------|--------|
| Storage | Local SQLite database (`data/tickets.db`) — not cloud-hosted |
| Access control | Session-based access only; no anonymous reads |
| Access logging | All read and write operations on tickets are logged with timestamp and role |
| Encryption | Database file should be encrypted at rest in production deployments |
| No external transmission | Data is never sent to third-party APIs or services |

> In the current development environment, the database is unencrypted. Encryption must be applied before any production deployment.

---

## 9. Consent

| Principle | Implementation |
|-----------|---------------|
| Informed | Students are told at the start of a session that their issue summary and name may be stored if a support ticket is created |
| Opt-out | Students can decline ticket creation; no data is stored if they do |
| Transparency | Students can ask what data is held about them at any time |
| Minimal collection | Only data explicitly provided by the student during the session is stored |

The agent must not create a ticket — and must not store any data — without the student's knowledge and explicit agreement.

---

## 10. Example Flow

### Session 1 — Ticket Created

1. Student: *"I cannot access the online registration portal."*
2. Agent retrieves relevant documents via RAG — no data stored yet.
3. RAG does not resolve the issue.
4. Agent requests approval to create a support ticket.
5. Student confirms: *"Yes, please create a ticket."*
6. Ticket `TICKET-0042` is created and stored with session ID `SES-a1b2c3d4`.
7. Agent confirms: *"Ticket TICKET-0042 has been created. A support staff member will follow up."*

### Session 2 — Status Query

1. Student (new session): *"What is the status of my ticket?"*
2. Agent asks for the ticket ID or student name to look up the record.
3. Student provides: *"TICKET-0042"*
4. Agent queries `data/tickets.db` and returns: *"Ticket TICKET-0042 is currently open and assigned to the ICT support team."*
5. No new data is stored.

---

## 11. Compliance Notes

| Principle | Status |
|-----------|--------|
| No PII beyond student input | ✅ Only data the student provides is stored |
| No third-party sharing | ✅ All data remains local |
| No sensitive categories | ✅ Health, financial, and academic records are explicitly excluded |
| Minimal retention | ✅ Retention periods defined and enforced (Section 5) |
| Right to deletion | ✅ Deletion policy defined (Section 6) |
| Student informed | ✅ Consent obtained before any data is stored (Section 9) |

> This document should be reviewed whenever the agent's data model, tools, or storage infrastructure changes. All revisions require sign-off from the project lead.
