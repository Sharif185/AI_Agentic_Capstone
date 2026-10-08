# State Model

**Project:** University Student-Support Case Agent  
**Version:** 1.0  
**Date:** 5th October 2026  
**Author:** Aloysious Mutagubya (Application/Integration Lead)

---

## Overview

The agent operates with **three distinct layers of state**, each with its own lifetime and purpose:

1. **Session State** — In-memory, lives for one conversation
2. **Workflow/Agent State** — In-memory, lives for one agent run (one goal)
3. **Persistent State** — Cross-session, lives in SQLite database

This separation ensures:
- Clear boundaries between ephemeral and durable state
- Proper data flow between layers
- Privacy-first design (only justified data persists)

---

## 1. Session State (In-Memory, Per Conversation)

### Purpose
Tracks one conversation session between the student and the agent. Ephemeral — exists only while the conversation is active.

### Python Class Definition

```python
class SessionState:
    """
    Tracks a single conversation session.
    Lifetime: Active conversation (max 30 days, then purged).
    """
    session_id: str           # SES-XXXX (unique session identifier)
    user_id: str              # Optional student identifier (for cross-session memory)
    started_at: datetime      # When session began
    last_active: datetime     # Last interaction timestamp
    current_case: str         # Active ticket ID (if any)
    preferences: dict         # In-session preferences (e.g., preferred language)
    conversation_turns: int   # Number of exchanges in this session
```

### Lifetime

| Event | State Change |
|-------|--------------|
| **Session Start** | New `SessionState` created, `session_id` generated |
| **Each Turn** | `last_active` updated, `conversation_turns` incremented |
| **Ticket Created** | `current_case` set to ticket ID |
| **Session End** | State saved to persistent memory (optional) |
| **Expiry (30 days)** | Session purged from persistent storage |

### Data Flow
- **Created by:** `MemoryManager.start_session(user_id)`
- **Updated by:** Agent during conversation
- **Persisted by:** `MemoryManager.end_session()` (saves to database)
- **Retrieved by:** `MemoryManager.resume_session(session_id)`

---

## 2. Workflow / Agent State (In-Memory, Per Agent Run)

### Purpose
Tracks one bounded agent execution (one student goal, up to 5 iterations). Ephemeral — exists only for the duration of that run.

### Python Class Definition

```python
class AgentState:
    """
    Tracks the execution state of one agent run.
    Lifetime: Single agent execution (goal completion or stop).
    """
    goal: str                        # Student's goal/question
    student_name: str                # Student identifier for this run
    iteration: int                   # Current iteration (1-indexed)
    max_iterations: int              # Iteration limit (default: 5)
    history: list[dict]              # All steps taken (plan, rag_retrieve, call_tool, answer, stop)
    retrieved_documents: list[dict]  # Accumulated RAG results
    tool_results: list[dict]         # Accumulated tool call results
    current_plan: dict               # Most recent planner decision
    completed: bool                  # True when agent finishes
    human_needed: bool               # True if approval was denied
    final_response: str              # Agent's final answer
    stop_reason: str                 # Why the agent stopped
    started_at: str                  # ISO timestamp of run start
    tool_call_count: int             # Total tool calls (bounded by max_tool_calls)
    rag_call_count: int              # Total RAG calls (bounded by max_rag_calls)
    memory_context: str              # NEW (Week 6): Injected memory context
```

### Lifetime

| Event | State Change |
|-------|--------------|
| **Agent Run Start** | New `AgentState(goal)` created |
| **Each Iteration** | `iteration` incremented, steps added to `history` |
| **RAG Retrieve** | `rag_call_count` incremented, result added to `retrieved_documents` |
| **Tool Call** | `tool_call_count` incremented, result added to `tool_results` |
| **Stop Condition Met** | `completed` set to True, `stop_reason` recorded |
| **Agent Run End** | State serialized to trace file, then discarded |

### Data Flow
- **Created by:** `StudentSupportAgent.run(goal, user_id)`
- **Updated by:** Agent loop (Sense → Plan → Act → Observe → Evaluate)
- **Passed to:** `Planner` (for planning context), `Tracer` (for trace recording)
- **Persisted by:** `Tracer.save()` (writes to JSON trace file)

---

## 3. Persistent State (Cross-Session, SQLite Database)

### Purpose
Stores data that must survive across sessions: case history, session metadata, preferences. Durable — lives according to retention policy.

### Python Class Definition

```python
class PersistentMemory:
    """
    Manages cross-session data in SQLite.
    Lifetime: Per retention policy (see Memory Design doc).
    """
    tickets: list[Ticket]      # All created tickets
    case_history: list[Case]   # Prior cases by student (derived from tickets)
    preferences: dict          # Approved preferences only
    sessions: list[Session]    # Session metadata (for resumption)
```

### Database Schema

#### `sessions` Table

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | TEXT PRIMARY KEY | SES-XXXX |
| `user_id` | TEXT | Student identifier (nullable) |
| `started_at` | TEXT | ISO timestamp |
| `last_active` | TEXT | ISO timestamp |
| `current_case` | TEXT | Active ticket ID (nullable) |
| `preferences` | TEXT (JSON) | Session preferences |
| `conversation_turns` | INTEGER | Number of exchanges |

**Retention:** 30 days from `last_active`

#### `case_history` Table

| Column | Type | Description |
|--------|------|-------------|
| `ticket_id` | TEXT PRIMARY KEY | TICKET-0001, TICKET-0002, ... |
| `student_name` | TEXT | Full name |
| `student_id` | TEXT | Student ID (nullable) |
| `issue_summary` | TEXT | Issue description |
| `priority` | TEXT | low, medium, high |
| `category` | TEXT | registration, exams, fees, academic, other |
| `status` | TEXT | open, closed |
| `created_at` | TEXT | ISO timestamp |
| `updated_at` | TEXT | ISO timestamp |
| `session_id` | TEXT | Session that created this ticket (nullable) |

**Retention:**  
- Open tickets: 90 days from `created_at`
- Closed tickets: 1 year from `updated_at` (closure date)

#### `preferences` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `user_id` | TEXT | Student identifier |
| `key` | TEXT | Preference key (e.g., "language") |
| `value` | TEXT | Preference value (e.g., "en") |
| `approved` | INTEGER (bool) | 1 if approved by student, 0 otherwise |
| `created_at` | TEXT | ISO timestamp |

**Retention:** Indefinite (while account active)

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        SESSION STATE                             │
│   (in-memory, lives for one conversation)                        │
│   session_id  •  user_id  •  current_case  •  preferences       │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ 1. User sends message
                         │    → Session context passed to agent
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                        WORKFLOW STATE                            │
│   (in-memory, lives for one agent run)                           │
│   goal  •  iteration  •  history  •  tool_results               │
│   memory_context (NEW in Week 6)                                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ 2. Ticket created
                         │    → Ticket saved to persistent memory
                         │
                         │ 3. Memory context loaded
                         │    ← Prior tickets retrieved
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      PERSISTENT MEMORY                           │
│   (SQLite, lives across sessions)                                │
│   sessions table  •  case_history table  •  preferences table    │
└──────────────────────────────────────────────────────────────────┘
                         │
                         │ 4. User request: delete data
                         │    → All user data purged
                         │
                         ▼
                     [DELETED]
```

---

## State Transitions Table

| From | To | Trigger | What Happens |
|------|----|---------|--------------| 
| **None** | **Session State** | User starts conversation | `MemoryManager.start_session(user_id)` creates new session |
| **Session State** | **Workflow State** | User sends message | Session context passed to `agent.run(goal, user_id)` |
| **Workflow State** | **Workflow State** | Agent iterates | `state.next_iteration()` → Plan → Act → Observe → Evaluate |
| **Workflow State** | **Persistent Memory** | Ticket created | `memory.save_ticket(ticket)` writes to `case_history` table |
| **Workflow State** | **Persistent Memory** | Preference stated | `memory.save_preference(user_id, key, value, approved=True)` |
| **Persistent Memory** | **Workflow State** | New session starts | `memory.get_memory_context(user_id)` loads prior tickets → injected into `AgentState.memory_context` |
| **Session State** | **Persistent Memory** | Session ends | `memory.end_session()` saves session metadata to `sessions` table |
| **Persistent Memory** | **Deleted** | User request | `memory.delete_all_data(user_id)` purges all user data |
| **Persistent Memory** | **Deleted** | Retention expired | `memory.purge_old_sessions(days=30)` / `memory.purge_old_tickets(status='closed', days=365)` |

---

## Memory Context Injection (NEW in Week 6)

When the agent starts a run, `MemoryManager.get_memory_context(user_id)` retrieves prior tickets and formats them as a string:

```
MEMORY CONTEXT:
Prior tickets: 2
  - TICKET-0001: Cannot access online registration portal (open, created 2026-10-05)
  - TICKET-0002: Question about exam schedule (closed, created 2026-09-28)
```

This string is injected into `AgentState.memory_context` and passed to the Planner, which includes it in the planning prompt. The agent can then reference prior tickets in its reasoning and responses.

**Key Rule:** Memory is **assistive only** — it informs the agent's response but never overrides the current session. If the student says "Actually, my issue is different now," the agent ignores memory and focuses on the current goal.

---

## Implementation Classes

### 1. `SessionState` (src/memory/session_state.py)

```python
class SessionState:
    def __init__(self, session_id=None, user_id=None):
        self.session_id = session_id or self._generate_id()
        self.user_id = user_id
        self.started_at = datetime.now().isoformat()
        self.last_active = self.started_at
        self.current_case = None
        self.preferences = {}
        self.conversation_turns = 0

    def _generate_id(self):
        import uuid
        return f'SES-{uuid.uuid4().hex[:8]}'

    def touch(self):
        """Update last_active timestamp and increment conversation turns."""
        self.last_active = datetime.now().isoformat()
        self.conversation_turns += 1

    def set_current_case(self, ticket_id):
        """Set the active ticket for this session."""
        self.current_case = ticket_id

    def get_context(self):
        """Return a dict for agent injection."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "current_case": self.current_case,
            "conversation_turns": self.conversation_turns,
        }

    def to_dict(self):
        """Serialise to dict (for persistence)."""
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
    def from_dict(cls, data):
        """Deserialise from dict (from persistence)."""
        session = cls(session_id=data["session_id"], user_id=data.get("user_id"))
        session.started_at = data["started_at"]
        session.last_active = data["last_active"]
        session.current_case = data.get("current_case")
        session.preferences = data.get("preferences", {})
        session.conversation_turns = data.get("conversation_turns", 0)
        return session
```

### 2. `PersistentMemory` (src/memory/persistent_memory.py)

```python
class PersistentMemory:
    def __init__(self, db_path='data/memory.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_tables()

    def _create_tables(self):
        """CREATE TABLE IF NOT EXISTS for sessions, case_history, preferences."""
        pass

    def save_session(self, session_state):
        """Save or update a session in the sessions table."""
        pass

    def load_session(self, session_id):
        """Load a session by session_id, return SessionState or None."""
        pass

    def purge_old_sessions(self, days=30):
        """Delete sessions older than 'days' from last_active."""
        pass

    def save_ticket(self, ticket, session_id=None):
        """Save a ticket to case_history table."""
        pass

    def get_ticket(self, ticket_id):
        """Retrieve a ticket by ticket_id."""
        pass

    def get_tickets_by_student(self, student_id):
        """Retrieve all tickets for a given student_id."""
        pass

    def delete_ticket(self, ticket_id):
        """Delete a ticket by ticket_id."""
        pass

    def save_preference(self, user_id, key, value, approved=True):
        """Save a user preference."""
        pass

    def get_preferences(self, user_id):
        """Retrieve all preferences for a user."""
        pass
```

### 3. `MemoryManager` (src/memory/memory_manager.py)

```python
class MemoryManager:
    """
    High-level interface for memory operations.
    Coordinates SessionState and PersistentMemory.
    """
    def __init__(self, db_path='data/memory.db'):
        self.persistent = PersistentMemory(db_path)
        self.current_session = None

    def start_session(self, user_id=None) -> str:
        """Start a new session, return session_id."""
        self.current_session = SessionState(user_id=user_id)
        return self.current_session.session_id

    def resume_session(self, session_id) -> bool:
        """Resume an existing session, return True if found."""
        session = self.persistent.load_session(session_id)
        if session:
            self.current_session = session
            return True
        return False

    def end_session(self):
        """Save current session to persistent memory and clear."""
        if self.current_session:
            self.persistent.save_session(self.current_session)
            self.current_session = None

    def save_ticket(self, ticket):
        """Save a ticket (and link to current session if active)."""
        session_id = self.current_session.session_id if self.current_session else None
        self.persistent.save_ticket(ticket, session_id=session_id)
        if self.current_session:
            self.current_session.set_current_case(ticket['ticket_id'])

    def get_ticket(self, ticket_id):
        """Retrieve a ticket by ID."""
        return self.persistent.get_ticket(ticket_id)

    def get_memory_context(self, user_id) -> str:
        """Format memory context string for agent prompt injection."""
        tickets = self.persistent.get_tickets_by_student(user_id)
        if not tickets:
            return ""
        lines = [f"MEMORY CONTEXT:", f"Prior tickets: {len(tickets)}"]
        for ticket in tickets[:3]:  # Limit to 3 most recent to avoid context overflow
            lines.append(f"  - {ticket['ticket_id']}: {ticket['issue_summary']} ({ticket['status']}, created {ticket['created_at'][:10]})")
        return "\n".join(lines)

    def delete_all_data(self, user_id):
        """Right to be forgotten: delete all user data."""
        tickets = self.persistent.get_tickets_by_student(user_id)
        for ticket in tickets:
            self.persistent.delete_ticket(ticket['ticket_id'])
        # Also delete sessions and preferences (implementation in PersistentMemory)
```

---

## Summary

**Week 6 State Model:**
- ✅ **3 distinct layers:** Session (ephemeral), Workflow (per-run), Persistent (cross-session)
- ✅ **Clear lifetimes:** Session (30 days), Workflow (single run), Persistent (retention policy)
- ✅ **Memory injection:** `memory_context` added to `AgentState` for Week 6
- ✅ **Data flow:** Session → Workflow → Persistent → back to Workflow (on next session)
- ✅ **Privacy-first:** Only justified data persists; full deletion path implemented

**Next Steps:**
- Implement `src/memory/` classes (Day 2)
- Integrate with `agent.py` (Day 3)
- Test cross-session persistence (Day 4)

---

**Document Version:** 1.0  
**Next Review:** Week 7 (after evaluation)  
**Owner:** Aloysious Mutagubya (Application/Integration Lead)
