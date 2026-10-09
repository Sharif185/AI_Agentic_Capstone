# State Model

**Project:** University Student-Support Case Agent (BSE4104)
**Owner:** Mus (Application / Integration Lead) | **Week 6** | **Status:** implemented in `src/memory/` and `src/agent/`

The agent keeps three kinds of state. They have different lifetimes and are deliberately kept in separate classes so that a per-run scratchpad is never mistaken for permanent student memory.

| Layer | Class | Where it lives | Lifetime |
|---|---|---|---|
| Session state | `SessionState` (`src/memory/session_state.py`) | In memory; session *metadata* mirrored to SQLite | One conversation; stored sessions purged after **30 days** of inactivity |
| Agent / workflow state | `AgentState` (`src/agent/state.py`) | In memory only | One agent run (one student goal) |
| Persistent memory | `PersistentMemory` (`src/memory/persistent_memory.py`), coordinated by `MemoryManager` | SQLite, `data/memory.db` | Per retention policy below |

## 1. Session state

Purpose: tracks who the conversation is with and which case is active.

| Field | Type | Notes |
|---|---|---|
| `session_id` | str | `SES-` + 8 hex chars from `uuid4` |
| `user_id` | str \| None | Self-declared student ID (the app has no authentication); None = anonymous |
| `started_at` | str (ISO-8601 UTC) | |
| `last_active` | str (ISO-8601 UTC) | Updated by `touch()` and `set_current_case()` |
| `current_case` | str \| None | Active ticket ID |
| `preferences` | dict | **In-session only. Never written to the database.** |
| `conversation_turns` | int | Incremented by `touch()` (once per `agent.run`) |

Methods: `touch()`, `set_current_case()`, `get_context()`, `is_expired()`, `to_dict()`, `from_dict()` (invalid or missing fields fall back to safe defaults).

## 2. Agent / workflow state

Purpose: everything needed for one Sense → Plan → Act → Observe → Evaluate run. Discarded when the run ends (a JSON trace is written separately to `evidence/traces/`).

| Field | Type |
|---|---|
| `goal` | str |
| `iteration` / `max_iterations` | int |
| `history` | list of step dicts |
| `retrieved_documents` | list |
| `tool_results` | list |
| `completed` | bool |
| `stop_reason` | str \| None |
| `memory_context` (**new in Week 6**) | str: read-only remembered context for the planner, `""` when none |

Also present from Week 5: `student_name`, `human_needed`, `final_response`, `current_plan`, `tool_call_count`, `rag_call_count`, `started_at`.
`memory_context` is *copied in* at the start of a run. Nothing in `AgentState` is ever saved as student memory.

## 3. Persistent memory (SQLite)

Justified use case: **case history**. When a student returns, the agent can answer "what's the status of my ticket?" without re-asking.

### Tables

`sessions` (metadata only; no transcripts, no preferences)

| Column | Type | Constraint |
|---|---|---|
| `session_id` | TEXT | PRIMARY KEY |
| `user_id` | TEXT | indexed |
| `started_at`, `last_active` | TEXT | NOT NULL; `last_active` indexed |
| `current_case` | TEXT | |
| `conversation_turns` | INTEGER | NOT NULL, default 0 |

`case_history`

| Column | Type | Constraint |
|---|---|---|
| `ticket_id` | TEXT | PRIMARY KEY (re-saving updates, never duplicates) |
| `session_id` | TEXT | FOREIGN KEY → `sessions` ON DELETE SET NULL |
| `student_name` | TEXT | NOT NULL |
| `student_id` | TEXT | indexed; the ownership key |
| `issue_summary` | TEXT | NOT NULL, ≤ 500 chars, credential-like text redacted |
| `priority`, `category`, `status` | TEXT | defaults `medium`, `other`, `open` |
| `created_at`, `updated_at` | TEXT | NOT NULL |

`preferences` (approved only)

| Column | Type | Constraint |
|---|---|---|
| `user_id`, `key` | TEXT | composite PRIMARY KEY |
| `value` | TEXT (JSON) | |
| `approved` | INTEGER | always 1 for stored rows |
| `updated_at` | TEXT | |

### Relationships

```
student (user_id / student_id) 1 ──< many  sessions      (sessions.user_id)
student (student_id)           1 ──< many  case_history  (case_history.student_id)
session                        1 ──< many  case_history  (case_history.session_id, nullable)
student (user_id)              1 ──< many  preferences   (composite key user_id + key)
```

A ticket belongs to a *student*. The `session_id` link only records which conversation created it.

## 4. Data flow

```
 Student message
        │
        ▼
┌─────────────────────────┐  user_id, session_id
│ SESSION STATE           │──────────────────────────┐
│ (one conversation)      │                          │
└────────────┬────────────┘                          │
             │ agent.run(goal, user_id)              │ save / load session metadata
             ▼                                       ▼
┌─────────────────────────┐  get_memory_context   ┌───────────────────────────┐
│ AGENT / WORKFLOW STATE  │◄──────────────────────│ PERSISTENT MEMORY (SQLite)│
│ (one run)               │   (read-only text)    │ sessions | case_history | │
│ goal, history, tools,   │                       │ preferences               │
│ memory_context          │  ticket created       │                           │
│                         │──────────────────────►│                           │
└────────────┬────────────┘ (TicketTool → save)   └───────────────────────────┘
             ▼
        Final response
```

Planner prompt order: current goal, then a clearly separated `MEMORY CONTEXT` block (background only), then history and rules. The current goal always wins over memory.

## 5. State transitions

| From | To | Trigger | What happens | Code |
|---|---|---|---|---|
| Session | Workflow | Student sends a message | `agent.run(goal, user_id)` counts the turn and loads `memory_context` into `AgentState` | `StudentSupportAgent.run` |
| Workflow | Persistent | Ticket created (after human approval) | `TicketTool` writes its JSON store, then `MemoryManager.save_ticket` upserts into `case_history`, links the session, sets `current_case` | `TicketTool.execute` |
| Workflow / Session | Persistent | Preference stated **and approved** | `set_preference(..., approved=True)` → `preferences` row; unapproved stays in `SessionState.preferences` only | `MemoryManager.set_preference` |
| Persistent | Workflow | New session starts and a student ID is given | `get_memory_context(user_id)` returns that student's recent tickets and approved preferences | `MemoryManager.get_memory_context` |
| Persistent | Deleted | Retention expiry | `start_session` runs `purge_expired()` | `MemoryManager.purge_expired` |
| Persistent | Deleted | Student asks to be forgotten | `delete_all_data(user_id)` | `MemoryManager.delete_all_data` |

## 6. Retention and deletion (what the code actually does)

| Data | Rule | Enforced by |
|---|---|---|
| Sessions | Purged when `last_active` is older than 30 days | `purge_old_sessions`, called on every `start_session` |
| Open tickets | Purged 90 days after `updated_at` | `purge_expired_tickets`, same trigger |
| Closed/resolved tickets | Purged 365 days after `updated_at` | same |
| Preferences | Kept until deleted | `delete_all_data` |

Retention only runs when a session starts. A database nobody opens is not cleaned.

Three different deletions:

| Operation | Removes | Leaves |
|---|---|---|
| `delete_session_data()` | The active session record | Tickets, preferences |
| `delete_ticket(id)` | One ticket (only if the caller may access it) | Everything else |
| `delete_all_data(user_id)` | That student's tickets, sessions and preferences | Other students; `data/support_tickets.json` |

## 7. Never stored, and access rules

- Never stored by design: credentials, financial data, grades, medical data, conversation transcripts. The schema has no columns for them; ticket text is whitelisted by field and credential-like phrases or 13–19 digit numbers are redacted; preference keys such as `password`, `grade`, `medical`, `card` are refused. This is a **best-effort pattern filter, not a guarantee**: a free-text summary can still hold sensitive wording the patterns do not catch.
- Context and ticket reads require an active session whose `user_id` equals the owner. Knowing a ticket ID is not enough. Anonymous sessions can only read unowned tickets created in the same session.
- `MemoryManager.get_ticket` is the read path for `TicketStatusTool` (Louis): it returns `ticket_id, status, issue_summary, created_at, updated_at` or `None`.

## 8. Known limitations

1. **No authentication.** `user_id` is typed in by the student. Isolation is only as strong as that identity; it must be replaced by a verified identity before real use.
2. **Two ticket stores.** `data/support_tickets.json` (ticket tool) is still the primary store; memory holds a copy. `delete_all_data` clears memory only.
3. **Retention runs at session start only**, and SQLite files are not encrypted.
4. **Timestamps** are timezone-aware UTC (the guide's example used naive local time); naive values are read as UTC.
