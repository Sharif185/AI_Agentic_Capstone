# Week 6 Progress Report

**Project:** University Student-Support Case Agent  
**Week:** 6 — Memory, State and Interoperability  
**Dates:** 5th – 9th October 2026  
**Report Author:** Noah (DevOps/Documentation Lead)  
**Date Written:** 8th October 2026

---

## Objectives and Status

| Objective | Status | Evidence |
|-----------|--------|----------|
| Model workflow/session state with 3 distinct layers | ✅ Complete | `docs/state-model.md`, `docs/architecture/state-model-diagram.md` |
| Implement persistent memory (SQLite) | ✅ Complete | `src/memory/persistent_memory.py`, `src/memory/memory_manager.py` |
| Document data handling and privacy | ✅ Complete | `docs/memory-design.md` |
| Demonstrate memory improves task (cross-session) | ✅ Complete | `evidence/week6-memory-demo.txt` |
| Implement MCP-style interface (4 capabilities) | ✅ Complete | `src/interfaces/mcp_interface.py`, `docs/mcp-interface-spec.md` |
| Pass all memory and interface tests | ✅ Complete | `tests/week6-memory-results.md` |

---

## What Was Built

### Week 5 Baseline (No Memory)
The agent from Week 5 operated entirely within a single session. When a student returned and asked "What's the status of my ticket?", the agent had no context — the student had to re-explain from scratch.

### Week 6 Addition: Justified, Bounded Memory
The agent now persists ticket history to a SQLite database. When a student returns in a new session, the agent loads prior tickets and can answer status questions immediately — no re-explanation needed.

**The core memory flow:**
```
Session 1: Student creates TICKET-0001 → saved to memory.db
Session 2: Agent loads memory context → "Prior tickets: 1 — TICKET-0001 (open)"
Student:   "What's the status of my ticket?"
Agent:     "Your ticket TICKET-0001 about 'Cannot access registration portal'
            is currently open."  ← answered from memory, no re-ask
```

---

## Key Engineering Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Memory use case: Case history only** | Justified, bounded, useful — students need ticket status across sessions |
| 2 | **SQLite for persistence** | Simple, local, zero external dependencies, works on all platforms |
| 3 | **30-day session retention** | Balances usefulness (can resume recent sessions) with privacy (stale sessions purged) |
| 4 | **Assistive-only memory** | Memory informs responses; never controls grades, admissions, or fee decisions |
| 5 | **MCP-style interface with 4 capabilities** | Clean contracts enable external integration and consistent testing |
| 6 | **`check_ticket_status` tool** | New tool (Week 6) leverages persistent memory for read-only ticket lookup |
| 7 | **Memory context injected into planning prompt** | Agent sees prior tickets in its planning context; planner decides when to use them |
| 8 | **3-ticket limit on context** | Prevents prompt overflow when students have many tickets (truncate to most recent 3) |
| 9 | **`delete_all_data(user_id)`** | Implements right-to-be-forgotten; tested and verified in demo |

---

## Three-Layer State Architecture

```
SESSION STATE (in-memory, per conversation)
    session_id, user_id, current_case, preferences, conversation_turns
         │
         │ passed to agent on each message
         ▼
WORKFLOW STATE (in-memory, per agent run)
    goal, iteration, history, tool_results, memory_context ← NEW
         │
         │ ticket created → saved to DB
         │ new session starts → context loaded from DB
         ▼
PERSISTENT MEMORY (SQLite, cross-session)
    sessions table · case_history table · preferences table
```

---

## Files Created / Modified This Week

### New Files

| File | Owner | Purpose |
|------|-------|---------|
| `docs/memory-design.md` | Sharif | Memory design and data handling note |
| `docs/state-model.md` | Mus | 3-layer state model definition |
| `docs/architecture/state-model-diagram.md` | Noah | ASCII state diagram with data flows |
| `docs/mcp-interface-spec.md` | Noah | Full MCP capability spec (schemas, permissions, error codes) |
| `docs/mcp-usage-guide.md` | Noah | Developer and integration guide |
| `prompts/agent-system-prompt-v4.0.txt` | Louis | Memory-aware prompt (Day 1 design) |
| `prompts/agent-system-prompt-v4.1.txt` | Louis | Concrete memory rules + disambiguation |
| `src/memory/__init__.py` | Mus | Memory package init |
| `src/memory/session_state.py` | Mus | Session state class |
| `src/memory/persistent_memory.py` | Mus | SQLite CRUD layer (3 tables) |
| `src/memory/memory_manager.py` | Mus | High-level memory coordinator |
| `src/tools/ticket_status_tool.py` | Louis | `check_ticket_status` tool (read-only) |
| `src/interfaces/__init__.py` | Noah | Interface package init |
| `src/interfaces/mcp_interface.py` | Noah | MCP-style interface (4 capabilities) |
| `src/demo_memory.py` | Mus | Two-session demonstration script |
| `tests/week6-memory-tests.md` | Imaan | 20 test case designs |
| `tests/run_memory_tests.py` | Imaan | 6 automated unit tests |
| `tests/test_memory_integration.py` | Imaan | Cross-session integration test |
| `tests/test_mcp_interface.py` | Louis | 7 MCP capability tests |
| `tests/week6-memory-results.md` | Imaan | Full test results summary |
| `evidence/week6-memory-demo.txt` | Mus | Captured demo output |
| `evidence/week6-mcp-test.txt` | Louis | Captured MCP test output |
| `weekly reports/week6-report.md` | Noah | This report |

### Modified Files

| File | Change |
|------|--------|
| `src/agent/agent.py` | Added `memory_manager` param, `check_ticket_status` to APPROVED_TOOLS, memory context injection |
| `src/agent/state.py` | Added `memory_context` attribute to `AgentState` |
| `src/agent/planner.py` | Injected memory context into planning prompt; added `check_ticket_status` to available tools |
| `src/run_agent.py` | Full memory integration: session lifecycle, memory-aware tools |
| `src/tools/ticket_tool.py` | Added optional `memory` parameter; auto-saves tickets to persistent memory |
| `prompts/version-history.md` | Added v4.0 and v4.1 entries |

---

## Test Results

### Memory Unit Tests (`tests/run_memory_tests.py`)

| Test | Result |
|------|--------|
| Session created with SES- prefix | ✅ PASS |
| Ticket saved and retrieved | ✅ PASS |
| Memory context includes ticket reference | ✅ PASS |
| Ticket deletion | ✅ PASS |
| Preferences saved and retrieved | ✅ PASS |
| No passwords stored (design check) | ✅ PASS |

**6/6 passed**

### Integration Test (`tests/test_memory_integration.py`)

| Test | Result |
|------|--------|
| Cross-session memory persistence | ✅ PASS |

**1/1 passed**

### MCP Interface Tests (`tests/test_mcp_interface.py`)

| Test | Result |
|------|--------|
| List capabilities (4 caps, version 1.0) | ✅ PASS |
| get_course_info — valid course | ✅ PASS |
| get_course_info — unknown course (NOT_FOUND) | ✅ PASS |
| check_ticket_status — not found (NOT_FOUND) | ✅ PASS |
| Invalid capability (NOT_FOUND) | ✅ PASS |
| Missing required input (INVALID_INPUT) | ✅ PASS |
| Output consistency (success key on all responses) | ✅ PASS |

**7/7 passed**

**Total: 14 tests, 14 passed, 0 failed**

---

## Memory Demo Evidence

Actual output from `python src/demo_memory.py`:

```
--- SESSION 1: Student creates a ticket ---
Session: SES-6985d985
✅ Ticket created: TICKET-0001
   Issue: Cannot access online registration portal
   Status: open
[Session 1 ended]

--- SESSION 2: Student returns next day ---
Session: SES-c1da422e
🧠 Agent's memory context:
MEMORY CONTEXT:
Prior tickets: 1
  - TICKET-0001: Cannot access online registration portal (open, created 2026-10-08)

Student: What's the status of my ticket?

🤖 Agent (using memory):
   Your ticket TICKET-0001 about 'Cannot access online registration portal'
   is currently open. Created: 2026-10-08

✅ Memory improved the task: Student didn't need to re-explain

--- Testing Right to be Forgotten ---
Student requests: 'Delete my data'
✅ Deleted: 1 ticket(s), 2 session(s), 0 preference(s)
Total tickets after deletion: 0
```

Full output: `evidence/week6-memory-demo.txt`

---

## Challenges and Resolutions

| Challenge | Response | Status |
|-----------|----------|--------|
| SQLite file held open by Windows after tests | Used `try/except OSError` on `os.remove()` instead of crashing | ✅ Fixed |
| Memory leaking between tests if shared DB | Gave each test group a unique DB path (`test_memory_unit.db`, `test_session_memory.db`) | ✅ Fixed |
| Context too long for prompt injection | Truncate to 3 most recent tickets in `get_memory_context()` | ✅ Fixed |
| `check_ticket_status` returning ticket from wrong student | Tool returns by ticket_id; DB matches on student_id in `get_tickets_by_student()` — isolated correctly | ✅ No issue |

---

## Individual Contributions

| Member | Tasks Owned | Evidence |
|--------|-------------|----------|
| **Sharif** | Memory Design Note, coordination, final review | `docs/memory-design.md` |
| **Mus** | Session state, persistent memory, memory manager, agent integration, demo | `src/memory/`, `src/demo_memory.py`, `src/agent/` updates |
| **Louis** | Memory prompts v4.0/v4.1, ticket status tool, MCP tests, planner update | `prompts/`, `src/tools/ticket_status_tool.py`, `tests/test_mcp_interface.py` |
| **Imaan** | Memory test design (20 cases), test runner, integration test, results doc | `tests/run_memory_tests.py`, `tests/test_memory_integration.py`, `tests/week6-memory-results.md` |
| **Noah** | State model diagram, MCP spec, MCP interface, usage guide, progress report | `docs/architecture/state-model-diagram.md`, `src/interfaces/mcp_interface.py`, `docs/mcp-usage-guide.md` |

---

## Week 6 Deliverables Checklist

| Deliverable | File | Owner | Status |
|-------------|------|-------|--------|
| State Model | `docs/state-model.md` | Mus | ✅ |
| State Model Diagram | `docs/architecture/state-model-diagram.md` | Noah | ✅ |
| Memory Design Note | `docs/memory-design.md` | Sharif | ✅ |
| Session State | `src/memory/session_state.py` | Mus | ✅ |
| Persistent Memory | `src/memory/persistent_memory.py` | Mus | ✅ |
| Memory Manager | `src/memory/memory_manager.py` | Mus | ✅ |
| Ticket Status Tool | `src/tools/ticket_status_tool.py` | Louis | ✅ |
| Memory-Aware Prompt v4.0 | `prompts/agent-system-prompt-v4.0.txt` | Louis | ✅ |
| Memory-Aware Prompt v4.1 | `prompts/agent-system-prompt-v4.1.txt` | Louis | ✅ |
| Memory Demo Script | `src/demo_memory.py` | Mus | ✅ |
| Memory Test Runner | `tests/run_memory_tests.py` | Imaan | ✅ |
| Integration Test | `tests/test_memory_integration.py` | Imaan | ✅ |
| MCP Interface | `src/interfaces/mcp_interface.py` | Noah | ✅ |
| MCP Spec | `docs/mcp-interface-spec.md` | Noah | ✅ |
| MCP Usage Guide | `docs/mcp-usage-guide.md` | Noah | ✅ |
| MCP Tests | `tests/test_mcp_interface.py` | Louis | ✅ |
| Test Results | `tests/week6-memory-results.md` | Imaan | ✅ |
| Demo Evidence | `evidence/week6-memory-demo.txt` | Mus | ✅ |
| MCP Test Evidence | `evidence/week6-mcp-test.txt` | Louis | ✅ |
| Week 6 Progress Report | `weekly reports/week6-report.md` | Noah | ✅ |

**20/20 deliverables complete.**

---

## What Week 6 Proved

1. **Memory persists across sessions** — ticket created in Session 1 is fully retrievable in Session 2 (proven by integration test and demo)
2. **Memory improves the task** — student answered status question without re-explaining (proven by demo output)
3. **Memory is bounded** — only ticket data stored; no passwords, grades, financial info
4. **Right to be forgotten works** — `delete_all_data()` removes all user data (proven by demo)
5. **MCP interface contracts hold** — all 4 capabilities return consistent shapes with correct error codes

---

## Plan for Week 7 — Evaluation and Guardrails

| Task | Owner | Focus |
|------|-------|-------|
| Create 30+ scenario evaluation dataset | Imaan | Coverage of happy path, edge cases, failures |
| Define measurable criteria | Sharif | Task completion %, groundedness, latency |
| Add logs/traces for model, prompt, retrieval, tool calls | Noah | Structured trace format |
| Implement guardrails | Mus | Input/output validation, tool allow-list, iteration limits, approval controls |
| Create Failure Catalogue | Louis | 5+ genuine failures with root cause and fix |
| Re-test after guardrail implementation | Imaan | Regression + new guardrail tests |
