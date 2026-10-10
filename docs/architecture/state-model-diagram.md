# State Model Diagram

**Project:** University Student-Support Case Agent  
**Version:** 1.0  
**Date:** 6th October 2026  
**Author:** Noah (DevOps/Documentation Lead)

---

## Three-Layer State Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        SESSION STATE                             │
│                                                                  │
│             (in-memory, lives for one conversation)              │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  session_id: SES-xxxxxxxx                                │ │
│   │  user_id: student_001                                    │ │
│   │  started_at: 2026-10-05T10:00:00Z                        │ │
│   │  last_active: 2026-10-05T10:15:23Z                       │ │
│   │  current_case: TICKET-0001                               │ │
│   │  preferences: {language: 'en'}                           │ │
│   │  conversation_turns: 5                                   │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│   Lifetime: Active conversation (max 30 days, then purged)      │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          │ 1. User sends message
                          │    → Session context passed to agent
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                        WORKFLOW STATE                            │
│                                                                  │
│              (in-memory, lives for one agent run)                │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  goal: "I want to register for BSE4104"                  │ │
│   │  student_name: "Alice"                                   │ │
│   │  iteration: 2                                            │ │
│   │  max_iterations: 5                                       │ │
│   │  history: [plan, rag_retrieve, call_tool, ...]          │ │
│   │  retrieved_documents: [{...RAG result...}]               │ │
│   │  tool_results: [{...tool call result...}]                │ │
│   │  current_plan: {action: 'call_tool', ...}               │ │
│   │  completed: False                                        │ │
│   │  final_response: ""                                      │ │
│   │  stop_reason: null                                       │ │
│   │  tool_call_count: 1                                      │ │
│   │  rag_call_count: 0                                       │ │
│   │  memory_context: "Prior tickets: 1\n  - TICKET-0001"    │ │  ← NEW (Week 6)
│   └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│   Lifetime: Single agent execution (goal completion or stop)     │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          │ 2. Memory loaded at run start
                          │    ← get_memory_context(user_id)
                          │
                          │ 3. Ticket created
                          │    → save_ticket(ticket, session_id)
                          │
                          │ 4. Agent execution ends
                          │    → trace saved to JSON file
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                      PERSISTENT MEMORY                           │
│                                                                  │
│                (SQLite, lives across sessions)                   │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  Database: data/memory.db                                │ │
│   │                                                          │ │
│   │  TABLE sessions:                                         │ │
│   │    session_id | user_id | started_at | last_active |... │ │
│   │    SES-abc123 | stu_001 | 2026-10-05 | 2026-10-05   ... │ │
│   │    SES-def456 | stu_002 | 2026-10-06 | 2026-10-06   ... │ │
│   │                                                          │ │
│   │  TABLE case_history:                                     │ │
│   │    ticket_id | student_id | issue_summary | status |... │ │
│   │    TICKET-01 | stu_001    | Cannot access | open    ... │ │
│   │    TICKET-02 | stu_002    | Exam question | closed  ... │ │
│   │                                                          │ │
│   │  TABLE preferences:                                      │ │
│   │    id | user_id | key      | value | approved           │ │
│   │    1  | stu_001 | language | en    | 1                  │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│   Lifetime: Per retention policy                                 │
│   - Sessions: 30 days from last_active                           │
│   - Open tickets: 90 days from created_at                        │
│   - Closed tickets: 1 year from updated_at                       │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          │ 5. User request: delete data
                          │    → delete_all_data(user_id)
                          │
                          ▼
                      [DELETED]
```

---

## Data Flow Between Layers

### 1. Session Start → Workflow Start

```
User Input: "I want to register for BSE4104"
       ↓
Session State created (or resumed)
       ↓
MemoryManager.start_session(user_id='student_001')
       ↓
session_id = 'SES-abc123'
       ↓
Agent.run(goal, user_id='student_001')
       ↓
AgentState created
       ↓
memory_context = MemoryManager.get_memory_context(user_id='student_001')
       ↓
AgentState.memory_context = "Prior tickets: 1\n  - TICKET-0001: ..."
       ↓
Agent loop starts (Plan → Act → Observe → Evaluate)
```

### 2. Ticket Creation → Persistent Storage

```
Agent Planner: {action: 'call_tool', tool_name: 'create_support_ticket', ...}
       ↓
ToolExecutor.execute('create_support_ticket', {...args...})
       ↓
ApprovalController: User approves "Create this ticket?"
       ↓
TicketTool.execute() → ticket created, written to tickets.json
       ↓
MemoryManager.save_ticket(ticket)
       ↓
PersistentMemory.save_ticket(ticket, session_id='SES-abc123')
       ↓
SQLite INSERT INTO case_history (...) VALUES (...)
       ↓
SessionState.current_case = 'TICKET-0001'
       ↓
Ticket now retrievable in future sessions
```

### 3. Memory Retrieval → Prompt Injection

```
New Session: Student returns next day
       ↓
MemoryManager.start_session(user_id='student_001')
       ↓
Agent.run(goal="What's the status of my ticket?", user_id='student_001')
       ↓
memory_context = MemoryManager.get_memory_context(user_id='student_001')
       ↓
PersistentMemory.get_tickets_by_student('student_001')
       ↓
SQL: SELECT * FROM case_history WHERE student_id='student_001' ORDER BY created_at DESC LIMIT 3
       ↓
tickets = [TICKET-0001, ...]
       ↓
Format as string: "MEMORY CONTEXT:\nPrior tickets: 1\n  - TICKET-0001: Cannot access portal (open)"
       ↓
AgentState.memory_context = formatted string
       ↓
Planner receives memory context in planning prompt
       ↓
Planner decides: {action: 'call_tool', tool_name: 'check_ticket_status', arguments: {ticket_id: 'TICKET-0001'}}
       ↓
Agent answers: "Your ticket TICKET-0001 is currently open. Created: 2026-10-05."
```

### 4. Session End → Persistence

```
User ends conversation (or 30 min timeout)
       ↓
MemoryManager.end_session()
       ↓
PersistentMemory.save_session(current_session)
       ↓
SQL: INSERT OR REPLACE INTO sessions (...) VALUES (...)
       ↓
SessionState cleared (current_session = None)
       ↓
Session metadata now saved to DB, can be resumed via resume_session(session_id)
```

### 5. Data Deletion (Right to be Forgotten)

```
Student: "Delete my data"
       ↓
Agent recognizes deletion request
       ↓
MemoryManager.delete_all_data(user_id='student_001')
       ↓
PersistentMemory.get_tickets_by_student('student_001')
       ↓
for each ticket: PersistentMemory.delete_ticket(ticket_id)
       ↓
SQL: DELETE FROM case_history WHERE ticket_id IN (...)
       ↓
SQL: DELETE FROM sessions WHERE user_id='student_001'
       ↓
SQL: DELETE FROM preferences WHERE user_id='student_001'
       ↓
All user data purged
       ↓
Agent: "Done — your data has been deleted."
```

---

## State Transition Diagram

```
   ┌──────────────┐
   │   NO STATE   │
   └──────┬───────┘
          │
          │ User starts conversation
          ▼
   ┌────────────────────┐
   │  SESSION CREATED   │
   │  (SessionState)    │
   └──────┬─────────────┘
          │
          │ User sends message
          ▼
   ┌────────────────────┐         ┌─────────────────────┐
   │  AGENT RUNNING     │───────▶ │  MEMORY LOADED      │
   │  (AgentState)      │  ←──────│  (memory_context)   │
   └──────┬─────────────┘         └─────────────────────┘
          │                                    ▲
          │ Agent executes                     │
          │ (Plan → Act → Observe → Evaluate)  │
          │                                    │
          │ Ticket created ────────────────────┘
          │ (saved to Persistent Memory)
          │
          ▼
   ┌────────────────────┐
   │  AGENT COMPLETE    │
   │  (stop_reason set) │
   └──────┬─────────────┘
          │
          │ Response returned
          │ Trace saved to JSON
          ▼
   ┌────────────────────┐
   │  SESSION ACTIVE    │
   │  (awaits next msg) │
   └──────┬─────────────┘
          │
          │ User ends session or timeout (30 min)
          ▼
   ┌────────────────────┐
   │  SESSION ENDED     │
   │  (saved to DB)     │
   └──────┬─────────────┘
          │
          │ 30 days pass or user request
          ▼
   ┌────────────────────┐
   │  DATA PURGED       │
   │  (deleted from DB) │
   └────────────────────┘
```

---

## Implementation Class Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                      MemoryManager                              │
│  (High-level interface for memory operations)                   │
│                                                                 │
│  Methods:                                                       │
│  - start_session(user_id) → session_id                          │
│  - resume_session(session_id) → bool                            │
│  - end_session()                                                │
│  - save_ticket(ticket)                                          │
│  - get_ticket(ticket_id)                                        │
│  - get_memory_context(user_id) → str                            │
│  - delete_all_data(user_id)                                     │
└──────────────┬─────────────────────────────┬────────────────────┘
               │                             │
               │ owns                        │ owns
               ▼                             ▼
┌──────────────────────────┐    ┌───────────────────────────────┐
│     SessionState         │    │     PersistentMemory          │
│  (Ephemeral session)     │    │  (SQLite database layer)      │
│                          │    │                               │
│  Properties:             │    │  Methods:                     │
│  - session_id            │    │  - save_session()             │
│  - user_id               │    │  - load_session()             │
│  - started_at            │    │  - purge_old_sessions()       │
│  - last_active           │    │  - save_ticket()              │
│  - current_case          │    │  - get_ticket()               │
│  - preferences           │    │  - get_tickets_by_student()   │
│  - conversation_turns    │    │  - delete_ticket()            │
│                          │    │  - save_preference()          │
│  Methods:                │    │  - get_preferences()          │
│  - touch()               │    │                               │
│  - set_current_case()    │    │  Database Tables:             │
│  - get_context()         │    │  - sessions                   │
│  - to_dict()             │    │  - case_history               │
│  - from_dict()           │    │  - preferences                │
└──────────────────────────┘    └───────────────────────────────┘
```

---

## Key Properties

### Session State
- **Lifetime:** Active conversation (max 30 days)
- **Scope:** One conversation session
- **Stored:** In-memory during session; optionally saved to DB on end
- **Access:** Current session only

### Workflow State
- **Lifetime:** One agent run (single goal)
- **Scope:** One Sense → Plan → Act → Observe → Evaluate loop
- **Stored:** In-memory during run; saved to trace JSON on completion
- **Access:** Agent loop only

### Persistent Memory
- **Lifetime:** Per retention policy (30 days sessions, 90 days open tickets, 1 year closed tickets)
- **Scope:** Cross-session (all interactions for one student)
- **Stored:** SQLite database (`data/memory.db`)
- **Access:** Via `MemoryManager` (session-based filtering)

---

## Memory Context Injection (Week 6 Feature)

```
Student returns after creating a ticket in Session 1
       ↓
Session 2 starts: MemoryManager.start_session(user_id='student_001')
       ↓
Agent.run(goal="What's my ticket status?", user_id='student_001')
       ↓
memory_context = MemoryManager.get_memory_context('student_001')
       │
       ├─ PersistentMemory.get_tickets_by_student('student_001')
       │  → SQL: SELECT * FROM case_history WHERE student_id='student_001' ORDER BY created_at DESC LIMIT 3
       │  → Returns [TICKET-0001, ...]
       │
       ├─ Format as string:
       │    "MEMORY CONTEXT:\n"
       │    "Prior tickets: 1\n"
       │    "  - TICKET-0001: Cannot access portal (open, created 2026-10-05)\n"
       │
       └─ Return formatted string
       ↓
AgentState.memory_context = formatted string
       ↓
Planner prompt injection:
    MEMORY CONTEXT:
    {memory_context}
       ↓
Planner sees prior ticket, decides to call check_ticket_status('TICKET-0001')
       ↓
Agent answers: "Your ticket TICKET-0001 is currently open."
```

**Key Rule:** Memory is **assistive only** — it informs the agent's response but never overrides the current session. If the student says "Actually, my issue is different now," the agent ignores memory and focuses on the current goal.

---

## Diagram Legend

| Symbol | Meaning |
|--------|---------|
| `┌─┐` | Component boundary |
| `→` | Data flow direction |
| `↓` | Sequential step |
| `▼` | Next state transition |
| `[...]` | Optional or future state |

---

**Document Version:** 1.0  
**Owner:** Noah (DevOps/Documentation Lead)  
**Next Review:** Week 7 (after evaluation)
