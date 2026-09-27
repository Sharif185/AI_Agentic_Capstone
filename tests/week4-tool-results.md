# Week 4 Tool Testing Results

**Author:** Imaan (Quality/Security Lead)  
**Date:** 25th September 2026  
**Tests run:** 15 total (11 unit + 4 end-to-end)  
**Result:** 15/15 passed ✓

---

## Executive Summary

All tool failure and authorization tests passed. The pipeline correctly:
- Catches missing required parameters at the executor level before invoking any tool
- Handles invalid input values inside each tool's own validation, returning structured errors
- Enforces the approval gate for every write operation (`create_support_ticket`)
- Degrades gracefully when data sources are unavailable (no unhandled exceptions)
- Normalizes student input (lowercase, whitespace) transparently

No security issues were identified. The approval gate cannot be bypassed.

---

## Part 1: Unit Test Results (`run_tool_tests.py`)

**11/11 passed**

### Part 1.1: Missing Parameter Tests

| Test ID | Description | Result | Notes |
|---------|-------------|--------|-------|
| TC-01 | `get_course_info` with no args | ✓ PASS | Executor caught missing `course_code` |
| TC-02 | Ticket with no `issue_summary` | ✓ PASS | Executor caught missing required param |
| TC-03 | Ticket with no `student_name` | ✓ PASS | Executor caught missing required param |

**Finding:** `ToolExecutor._validate_arguments` correctly blocks tool execution when required schema params are absent. Error format: `r["success"]=False`, `r["error"]="param is required"`.

### Part 1.2: Invalid Input Tests

| Test ID | Description | Result | Notes |
|---------|-------------|--------|-------|
| TC-05 | Non-existent course code `INVALID999` | ✓ PASS | Tool returned "Course INVALID999 not found" |
| TC-06 | Invalid `info_type="syllabus"` | ✓ PASS | Tool returned enum validation error |
| TC-07 | `issue_summary` with 501 characters | ✓ PASS | Tool returned "exceeds 500 characters" |
| TC-08 | `priority="urgent"` (invalid) | ✓ PASS | Tool returned "priority must be low, medium, or high" |

**Finding:** Tool-level errors are returned in `r["result"]["error"]`, distinct from executor-level errors in `r["error"]`. Both layers return `r["success"]=False`.

### Part 1.3: Authorization Tests

| Test ID | Description | Result | Notes |
|---------|-------------|--------|-------|
| TC-09 | `auto_approve=True` → ticket created | ✓ PASS | Ticket ID: `TICKET-XXXX`, gate fired in log |
| TC-10 | `auto_approve=False`, non-interactive → denied | ✓ PASS | Error: "Human approval denied" |

**Finding (Security):** The `ApprovalController` is always consulted for `requires_approval=True` tools. There is no code path that allows `create_support_ticket` to execute without first passing through the approval gate. Denial mode defaults to reject in non-interactive environments, which is the safe default.

### Part 1.4: Unavailable Service Tests

| Test ID | Description | Result | Notes |
|---------|-------------|--------|-------|
| TC-12 | `CourseTool` with non-existent data path | ✓ PASS | Returned "Course database unavailable" |

**Finding:** `CourseTool._load_data()` sets `self.courses = None` when the file is absent. The `execute()` method checks for this and returns a clean error, preventing any `FileNotFoundError` or `AttributeError` from surfacing to the caller.

### Part 1.5: Unknown Tool Tests

| Test ID | Description | Result | Notes |
|---------|-------------|--------|-------|
| TC-14 | Execute unregistered `unknown_tool` | ✓ PASS | Executor returned "Tool unknown_tool not found" |

---

## Part 2: End-to-End Scenario Results (`test_tool_calling.py`)

**4/4 passed**

| Scenario | Description | Result | Key Assertion |
|----------|-------------|--------|---------------|
| S-01 | Course prerequisites query | ✓ PASS | `prerequisites = ['BSE3101', 'BSE3102', 'CS103']` |
| S-02 | Ticket creation + approval gate | ✓ PASS | `ticket_id=TICKET-0001`, `approval_gate_fired=True` |
| S-03 | Lowercase code `bse4104` normalized | ✓ PASS | `credits=4` (correct BSE4104 data returned) |
| S-04 | Padded code `  BSE4104  ` normalized | ✓ PASS | Full course name returned correctly |

**Finding (Input Normalization):** `CourseTool.execute()` applies `.upper().strip()` to all course codes. This means students can type `bse4104`, `BSE4104`, or `  bse4104  ` and all receive correct results. This is a meaningful UX improvement over case-sensitive lookups.

---

## Key Security & Quality Findings

### Finding 1: Approval Gate Is Robust ✓
The `create_support_ticket` tool has `requires_approval=True`. The `ToolExecutor` checks this flag **before** calling `tool.execute()`. Approval is requested via `ApprovalController.request_approval()`, and only if it returns `True` does execution proceed. In production (non-auto-approve) mode, this triggers an interactive prompt. In automated/non-interactive mode, the default is denial — the safe choice.

### Finding 2: Two-Layer Validation Is Working Correctly ✓
- **Layer 1 (Executor):** Schema-required params checked before the tool runs
- **Layer 2 (Tool):** Business logic validation (enum values, string length, data existence)

Both layers return `{"success": False, "error": "..."}` consistently. The distinction in the error location (`r["error"]` vs `r["result"]["error"]`) is by design and documented in `week4-tool-tests.md`.

### Finding 3: Graceful Degradation Is Consistent ✓
Neither `CourseTool` nor `TicketTool` raises an unhandled exception in any test scenario, including missing data files. All failure paths return structured error dicts that the orchestration layer can handle cleanly.

### Finding 4: Input Normalization Covers Common Student Errors ✓
Lowercase and whitespace variations are silently corrected. This is appropriate for a student-facing support agent where exact input formatting cannot be guaranteed.

---

## Issues Found and Resolved

| Issue | Root Cause | Fix Applied |
|-------|-----------|-------------|
| TC-09 initially failed | `TicketStorage` initialized with default `data/tickets.db` path (relative to CWD), then the db_path attribute was overridden after construction — but the table had already been created at the wrong path | Fixed by passing `TicketStorage(db_path=absolute_path)` at construction time |

---

## Recommendations

1. **Production approval UX:** The current `ApprovalController` requires a terminal `y/n` prompt. For the web-based agent, this should be replaced with an async approval callback (e.g., a confirmation modal or webhook).

2. **Extend input normalization:** Consider normalizing student names (`.strip()`, title-case) in `TicketTool.execute()` to prevent duplicate tickets from whitespace differences.

3. **Add TC-11 approval log assertion to run_tool_tests.py** in a future sprint — currently covered by S-02 in the end-to-end suite, but having a dedicated unit test would give faster feedback.

4. **`TicketTool` category validation** correctly rejects invalid categories, but the valid list is defined twice (in `schema` and in `execute()`). Refactor to a shared constant to avoid drift.

---

## Test Artifacts

| File | Description |
|------|-------------|
| `tests/week4-tool-tests.md` | 16 test case definitions (5 parts) |
| `tests/run_tool_tests.py` | 11 automated unit tests |
| `tests/test_tool_calling.py` | 4 end-to-end scenario tests |
| `tests/week4-tool-results.json` | Machine-readable results from `run_tool_tests.py` |
| `tests/week4-e2e-results.json` | Machine-readable results from `test_tool_calling.py` |
| `src/tools/base_tool.py` | Abstract base class for all tools |
| `src/tools/course_tool.py` | CourseTool implementation |
| `src/tools/ticket_tool.py` | TicketTool implementation |
| `data/courses.json` | Course database (4 courses) |
| `data/sample_students.json` | Sample student data (4 students) |
| `prompts/system-prompt-v3.0.txt` | v3.0 prompt with tool instructions |
