# Week 6 Memory Test Cases

**Author:** Imaan Duga (Quality/Security Lead)  
**Date:** 5th October 2026  
**Week:** 6 — Memory, State and Interoperability  
**Test Script:** `tests/run_memory_tests.py` (unit) + `tests/test_memory_integration.py` (integration)

---

## Test Design Overview

Memory testing for Week 6 covers 5 critical areas:

| Part | Focus | Tests |
|------|-------|-------|
| **Part 1** | Memory Persistence | Tests 1–4: Ticket saved, retrievable across sessions, multiple tickets, session isolation |
| **Part 2** | Memory Privacy | Tests 5–8: No passwords, no financial data, deletion on request, retention enforced |
| **Part 3** | Memory Boundaries | Tests 9–12: No grade control, session overrides memory, consent respected, stale memory flagged |
| **Part 4** | Memory Improves Task | Tests 13–16: Ticket lookup, context improves response, no repeated questions |
| **Part 5** | MCP-Style Interface | Tests 17–20: Capability listed, schema validated, permission enforced, output consistent |

**Total Tests:** 20 (design) + 6 (automated unit) + 1 (integration) + 7 (MCP) = **34 tests**

---

## Part 1: Memory Persistence

### TEST-M-001: Ticket Saved to Database
**Category:** Persistence  
**Method:** Unit Test (automated)

**Steps:**
1. Create a `MemoryManager` with a test database path
2. Start a session with `user_id='test_student'`
3. Call `save_ticket({'ticket_id': 'TICKET-0001', 'student_id': 'test_student', 'issue_summary': 'Test issue', ...})`
4. Query SQLite `case_history` table directly

**Expected Result:**  
- `TICKET-0001` exists in the `case_history` table
- All fields saved correctly (ticket_id, student_id, issue_summary, status, timestamps)

**Pass Criteria:** `success = True`, ticket present in DB

---

### TEST-M-002: Ticket Retrievable Across Sessions
**Category:** Persistence  
**Method:** Integration Test (automated)

**Steps:**
1. **Session 1:** Create `MemoryManager(db_path='data/test_cross_session.db')`, start session, save `TICKET-0001`, end session
2. **Session 2:** Create NEW `MemoryManager(db_path='data/test_cross_session.db')`, start fresh session
3. Call `mm2.get_ticket('TICKET-0001')`

**Expected Result:**  
- `TICKET-0001` is retrieved in Session 2
- `retrieved['ticket_id'] == 'TICKET-0001'`
- `retrieved['issue_summary'] == 'Cannot access online registration portal'`

**Pass Criteria:** `retrieved is not None`, correct fields present

**Verification:**
```python
assert retrieved is not None, "Ticket should be retrievable in a new session"
assert retrieved['ticket_id'] == 'TICKET-0001'
print("✅ Memory persists across sessions!")
```

---

### TEST-M-003: Multiple Tickets for Same Student
**Category:** Persistence  
**Method:** Unit Test (automated)

**Steps:**
1. Start a session for `user_id='multi_student'`
2. Save `TICKET-0001` (category: registration)
3. Save `TICKET-0002` (category: exams)
4. Save `TICKET-0003` (category: fees)
5. Call `persistent.get_tickets_by_student('multi_student')`

**Expected Result:**  
- Returns a list of 3 tickets
- All tickets have `student_id='multi_student'`
- Ordered by most recent first (or by creation order)

**Pass Criteria:** `len(tickets) == 3`, all tickets present

---

### TEST-M-004: Session Isolation
**Category:** Persistence  
**Method:** Unit Test (automated)

**Steps:**
1. **Student A:** Start session, save `TICKET-A001` with `student_id='student_a'`
2. **Student B:** Start session, save `TICKET-B001` with `student_id='student_b'`
3. Retrieve tickets for `student_a`
4. Retrieve tickets for `student_b`

**Expected Result:**  
- `student_a` tickets only contain `TICKET-A001`
- `student_b` tickets only contain `TICKET-B001`
- No cross-contamination between students

**Pass Criteria:** Student A cannot see Student B's tickets and vice versa

---

## Part 2: Memory Privacy

### TEST-M-005: Passwords Are Never Stored
**Category:** Privacy  
**Method:** Negative Test (design verification)

**Steps:**
1. Inspect `PersistentMemory` schema (all 3 tables)
2. Inspect `SessionState` class
3. Inspect `TicketTool.execute()` input fields

**Expected Result:**  
- No `password`, `credentials`, `auth`, or `secret` fields in any schema
- No table column accepting password-like data
- `TicketTool` does not accept or forward password fields

**Pass Criteria:** Confirmed by code inspection — no password fields in any data class

**Evidence:**  
```
Database tables: sessions, case_history, preferences
Fields checked: ✅ No password/credential fields found
Design confirmation: passwords are NEVER in scope for memory storage
```

---

### TEST-M-006: Financial Data Not Stored
**Category:** Privacy  
**Method:** Negative Test (design verification)

**Steps:**
1. Inspect all fields in `case_history` table schema
2. Check `TicketTool` allowed input fields
3. Verify no financial data categories

**Expected Result:**  
- No `balance`, `payment`, `fees`, `account_number`, or `financial` fields in schema
- `TicketTool` category enum: `["registration", "exams", "fees", "academic", "other"]` — "fees" only captures the *category*, not actual fee data

**Pass Criteria:** Confirmed by inspection — no actual financial values stored

---

### TEST-M-007: Ticket Deletion On Request
**Category:** Privacy  
**Method:** Unit Test (automated)

**Steps:**
1. Create `MemoryManager`, start session, save `TICKET-DEL001`
2. Confirm ticket exists: `get_ticket('TICKET-DEL001')` returns data
3. Call `persistent.delete_ticket('TICKET-DEL001')`
4. Call `get_ticket('TICKET-DEL001')` again

**Expected Result:**  
- Before deletion: ticket is present
- After deletion: `get_ticket('TICKET-DEL001')` returns `None`

**Pass Criteria:** Ticket is `None` after deletion

---

### TEST-M-008: Full Data Deletion (Right to be Forgotten)
**Category:** Privacy  
**Method:** Unit Test (automated)

**Steps:**
1. Create session for `user_id='student_to_delete'`
2. Save 2 tickets for that student
3. Save 1 preference for that student
4. Call `memory.delete_all_data('student_to_delete')`
5. Call `persistent.get_tickets_by_student('student_to_delete')`
6. Call `persistent.get_preferences('student_to_delete')`

**Expected Result:**  
- After deletion: `get_tickets_by_student('student_to_delete')` returns empty list `[]`
- After deletion: `get_preferences('student_to_delete')` returns empty dict `{}`
- All data gone

**Pass Criteria:** All user data removed from all tables

---

## Part 3: Memory Boundaries

### TEST-M-009: Memory Does NOT Control Grade Decisions
**Category:** Boundaries  
**Method:** Prompt Review (manual)

**Steps:**
1. Review `agent-system-prompt-v4.1.txt` for grade-related memory constraints
2. Check that MEMORY BOUNDARIES section explicitly forbids grade decisions
3. Verify the rule is present: "Never make grade, admissions, or fee decisions based on memory"

**Expected Result:**  
- Prompt explicitly states: "Memory is ASSISTIVE, not controlling"
- Prompt explicitly states: "Never make grade, admissions, or fee decisions based on memory"
- No code path in `MemoryManager` writes grade data

**Pass Criteria:** Constraint is present in prompt and no grade fields in database schema

---

### TEST-M-010: Current Session Overrides Memory
**Category:** Boundaries  
**Method:** Unit Test (automated)

**Steps:**
1. Save ticket: `TICKET-0001`, category: `registration`, issue: "Cannot register"
2. Start new session for same student
3. Build memory context → shows prior ticket about registration
4. In new session, student says: "Actually, my problem is about exam scheduling, not registration"
5. Verify agent prompt includes: "current session ALWAYS wins" constraint

**Expected Result:**  
- Memory context is injected (shows registration ticket)
- Agent prompt includes the override constraint
- If tested with agent: agent would respond to the NEW goal (exams), not the memory-recalled one

**Pass Criteria:**  
- Memory context contains old ticket info
- Prompt constraint "current session ALWAYS wins" is present
- `AgentState.memory_context` is read-only — agent can't be locked into old context

---

### TEST-M-011: Consent Respected
**Category:** Boundaries  
**Method:** Design Review (manual)

**Steps:**
1. Review `MemoryManager` for opt-out/deletion pathway
2. Verify `delete_all_data(user_id)` exists and removes all data
3. Check prompt for "forget this" / "delete my data" instruction handling

**Expected Result:**  
- `delete_all_data(user_id)` successfully removes all data (proven by TEST-M-008)
- Prompt acknowledges "forget this" / "delete my data" commands
- Consent notice is documented in `docs/memory-design.md`

**Pass Criteria:** Deletion pathway exists and works; prompt handles opt-out language

---

### TEST-M-012: Memory Context Length Bounded
**Category:** Boundaries  
**Method:** Unit Test (automated)

**Steps:**
1. Save 10 tickets for one student
2. Call `get_memory_context('student_with_lots_of_tickets')`
3. Count ticket references in the returned string

**Expected Result:**  
- Returns at most 3 ticket references (truncation applied)
- Context string does not grow unboundedly with number of tickets
- Total context length is under 500 characters

**Pass Criteria:** `context.count('TICKET-') <= 3`

---

## Part 4: Memory Improves Task

### TEST-M-013: Ticket Status Lookup Without Re-Explaining
**Category:** Task Improvement  
**Method:** Integration Test (automated)

**Steps:**
1. **Session 1:** Student creates ticket about "Cannot access online registration portal"
2. **Session 2:** Student asks "What's the status of my ticket?"
3. Agent uses `get_memory_context()` to find prior ticket
4. Agent calls `check_ticket_status('TICKET-0001')`
5. Agent returns status without asking "What is your issue?"

**Expected Result:**  
- Agent answers using memory context
- No "Could you describe your issue?" follow-up question
- Response includes: ticket ID, status, and issue summary

**Pass Criteria:** Ticket retrieved, status returned, student did not need to re-explain

---

### TEST-M-014: Memory Context Includes Ticket Reference
**Category:** Task Improvement  
**Method:** Unit Test (automated)

**Steps:**
1. Save `TICKET-0001` for `user_id='context_student'`
2. Call `memory.get_memory_context('context_student')`
3. Check returned string

**Expected Result:**  
- `'TICKET-0001' in context` is True
- Context includes issue summary
- Context includes status

**Pass Criteria:** `'TICKET-0001' in context`

---

### TEST-M-015: No Repeated Questions About Known Info
**Category:** Task Improvement  
**Method:** Integration Test (manual)

**Steps:**
1. Session 1: Student provides name ("Alice"), creates ticket
2. Session 2: Agent has memory context with name from ticket
3. Agent should NOT ask "What is your name?" again

**Expected Result:**  
- Student name is available via `ticket['student_name']`
- Agent uses this from memory rather than asking again

**Pass Criteria:** Agent can construct a personalized response without re-asking for name

---

### TEST-M-016: Memory Context Correctly Formatted for Prompt
**Category:** Task Improvement  
**Method:** Unit Test (automated)

**Steps:**
1. Save 2 tickets: `TICKET-0001` (open), `TICKET-0002` (closed)
2. Call `get_memory_context('format_student')`
3. Parse the returned string

**Expected Result:**  
- String starts with `"MEMORY CONTEXT:"`
- Contains `"Prior tickets: 2"`
- Each ticket on its own line with `"  - TICKET-XXXX:"` format
- Status included: `"(open)"` or `"(closed)"`

**Pass Criteria:** Context string follows the expected format for prompt injection

---

## Part 5: MCP-Style Interface

### TEST-M-017: Capabilities Listed Correctly
**Category:** MCP Interface  
**Method:** Unit Test (automated)

**Steps:**
1. Create `StudentSupportInterface()`
2. Call `interface.list_capabilities()`
3. Check returned dict

**Expected Result:**  
- Returns `{'version': '1.0', 'capabilities': [...]}` 
- Contains exactly 4 capabilities: `query_support`, `get_course_info`, `create_ticket`, `check_ticket_status`
- Each capability has: `description`, `permissions`, `rate_limit`, `input_schema`, `output_schema`

**Pass Criteria:** All 4 capabilities present with required fields

---

### TEST-M-018: Input Schema Validated
**Category:** MCP Interface  
**Method:** Unit Test (automated)

**Steps:**
1. Call `interface.invoke('get_course_info', {})` — missing required `course_code`
2. Call `interface.invoke('check_ticket_status', {'ticket_id': 'TICKET-0001'})` — valid input
3. Call `interface.invoke('create_ticket', {'issue_summary': 'test'})` — missing `student_name`

**Expected Result:**  
- Empty input: `{'success': False, 'error': '...', 'error_code': 'INVALID_INPUT'}`
- Valid input: `{'success': True, ...}` (or `NOT_FOUND` if ticket doesn't exist)
- Missing required field: `{'success': False, 'error_code': 'INVALID_INPUT'}`

**Pass Criteria:** Invalid inputs return `INVALID_INPUT` error code; valid inputs proceed

---

### TEST-M-019: Permission Enforced for Ticket Creation
**Category:** MCP Interface  
**Method:** Unit Test (automated)

**Steps:**
1. Call `interface.invoke('create_ticket', {'student_name': 'Test', 'issue_summary': 'Test issue'})` without a session ID
2. Check whether `create_ticket` requires session context (permission check)

**Expected Result:**  
- `create_ticket` requires session authorization
- Without session: should still work in current implementation (no auth in Week 6)
- Returns `ticket_id` on success

**Pass Criteria:** Ticket created successfully with required inputs; interface handles the call

---

### TEST-M-020: Interface Output Consistent
**Category:** MCP Interface  
**Method:** Unit Test (automated)

**Steps:**
1. Call `interface.invoke('query_support', {'query': 'What are BSE4104 prerequisites?'})`
2. Call `interface.invoke('get_course_info', {'course_code': 'BSE4104', 'info_type': 'prerequisites'})`
3. Call `interface.invoke('invalid_capability', {})`
4. Inspect all three responses

**Expected Result:**  
- All responses have `success` key (bool)
- Success responses have data fields
- Failure responses have `error` and `error_code` fields
- Invalid capability: `{'success': False, 'error_code': 'NOT_FOUND'}`

**Pass Criteria:** All responses are JSON-serializable dicts with consistent schema

---

## Evaluation Criteria

| Criterion | Target | Rationale |
|-----------|--------|-----------|
| **Persistence works** | 100% | Memory only has value if data survives across sessions |
| **Privacy rules enforced** | 100% | Zero tolerance for credential/financial data storage |
| **Boundaries respected** | 100% | Memory must never control grades/fees decisions |
| **Task improvement demonstrated** | 100% | Must prove agent answers without re-asking (the core value) |
| **MCP interface validated** | 90%+ | Interface is the integration contract; minor edge cases acceptable |

---

## Test Execution Plan

| Test Group | Script | Run Day |
|------------|--------|---------|
| Part 1 (Persistence) | `tests/run_memory_tests.py` | Day 4 |
| Part 2 (Privacy) | `tests/run_memory_tests.py` | Day 4 |
| Part 3 (Boundaries) | Manual + `tests/run_memory_tests.py` | Day 4 |
| Part 4 (Task Improvement) | `tests/test_memory_integration.py` | Day 4 |
| Part 5 (MCP Interface) | `tests/test_mcp_interface.py` | Day 4 |

---

## Test Environment Notes

- Each test uses an **isolated database** (`data/test_*.db`) — no shared state between tests
- Test databases are created before tests and cleaned up after
- Tests must work with no external API calls (memory tests are fully local)
- All tests should run in < 5 seconds (SQLite is fast)

---

## Known Risks

| Risk | Mitigation |
|------|------------|
| Session ID collision if tests run concurrently | Use unique per-test DB paths |
| Stale test data if cleanup fails | Use `try/finally` to ensure cleanup |
| Memory context too long for prompt injection | Limit to 3 tickets (tested in TEST-M-012) |
| SQLite locked if multiple tests open same DB | Isolated DBs per test |
