# Week 4 Tool Failure & Authorization Test Cases

**Author:** Imaan (Quality/Security Lead)  
**Date:** 22nd September 2026  
**Purpose:** Document failure and authorization test cases for the tool execution pipeline.  
**Scope:** ToolExecutor, ApprovalController, CourseTool, TicketTool

---

## Overview

This document covers 16 test cases across 5 parts, focusing on how the tool pipeline handles bad input, missing parameters, authorization gates, service failures, and unexpected tool responses. All tests are designed to verify that failures are handled gracefully — returning clear error messages rather than unhandled exceptions.

**Tools under test:**
- `get_course_info` (CourseTool) — read-only, no approval required
- `create_support_ticket` (TicketTool) — write operation, requires human approval

---

## Part 1: Missing Parameter Tests

These tests verify that calling a tool without required parameters is caught at the ToolExecutor validation layer **before** the tool is ever invoked.

| Test ID | Tool | Action | Expected Result |
|---------|------|--------|-----------------|
| TC-01 | `get_course_info` | Call with empty `{}` | Executor returns `success=False`, error contains "required" |
| TC-02 | `create_support_ticket` | Call with only `{"student_name": "Alice"}` — missing `issue_summary` | Executor returns `success=False`, error contains "required" |
| TC-03 | `create_support_ticket` | Call with only `{"issue_summary": "Lost ID"}` — missing `student_name` | Executor returns `success=False`, error contains "required" |
| TC-04 | `create_support_ticket` | Call with `{}` — both required params missing | Executor returns `success=False`, error contains "required" |

**Expected behavior:** The `ToolExecutor._validate_arguments` method checks the tool's schema `required` list and returns an error immediately. The tool's `execute()` method is never called.

---

## Part 2: Invalid Input Tests

These tests verify that tools correctly reject invalid input values even when required parameters are present. Errors originate inside the tool's `execute()` method.

| Test ID | Tool | Action | Expected Result |
|---------|------|--------|-----------------|
| TC-05 | `get_course_info` | `course_code="INVALID999"` | Tool returns `success=False`, result error: "Course INVALID999 not found" |
| TC-06 | `get_course_info` | `course_code="BSE4104"`, `info_type="syllabus"` (invalid enum) | Tool returns `success=False`, result error contains "info_type must be one of" |
| TC-07 | `create_support_ticket` | `issue_summary` = 501-character string (over limit) | Tool returns `success=False`, result error: "issue_summary exceeds 500 characters" |
| TC-08 | `create_support_ticket` | `priority="urgent"` (invalid enum) | Tool returns `success=False`, result error: "priority must be low, medium, or high" |

**Expected behavior:** Executor passes arguments through to the tool. The tool's internal validation catches the error and returns `{"success": False, "error": "..."}`. The executor wraps this as `r["success"]=False`, `r["result"]["error"]` contains the message.

---

## Part 3: Authorization Tests

These tests verify the approval gate for `create_support_ticket`, which has `requires_approval=True`. The ApprovalController must be consulted before the ticket is ever written.

| Test ID | Approval Mode | Action | Expected Result |
|---------|--------------|--------|-----------------|
| TC-09 | `auto_approve=True` | Valid ticket creation | Approval granted automatically; ticket created successfully |
| TC-10 | `auto_approve=False`, `interactive=False` | Valid ticket creation | Approval denied (non-interactive default); `success=False`, error: "Human approval denied" |
| TC-11 | `auto_approve=True` | Verify approval log is populated | `approval_log` contains one entry with `approved=True`, `mode="auto"` |

**Expected behavior:** The ApprovalController is called before tool execution for any tool where `requires_approval=True`. A non-interactive, non-auto-approve controller defaults to denial. The approval log records every decision.

**Security note:** The `create_support_ticket` tool must never execute without passing through the ApprovalController check, even with valid arguments.

---

## Part 4: Unavailable Service Tests

These tests verify graceful degradation when underlying data sources or services are unavailable.

| Test ID | Tool | Setup | Expected Result |
|---------|------|-------|-----------------|
| TC-12 | `get_course_info` | Instantiate CourseTool with a non-existent `data_path` | Tool returns `success=False`, error: "Course database unavailable" |
| TC-13 | `create_support_ticket` | Instantiate TicketStorage with an invalid/read-only `db_path`, then call TicketTool | Tool returns `success=False`, error contains "Ticket system unavailable" |

**Expected behavior:** Tools handle missing files and broken storage gracefully. No unhandled exceptions propagate to the caller. The error message clearly identifies the service that failed.

---

## Part 5: Unexpected Tool Response Tests

These tests verify that the ToolExecutor handles edge cases in tool responses and non-existent tool names robustly.

| Test ID | Scenario | Action | Expected Result |
|---------|----------|--------|-----------------|
| TC-14 | Unknown tool | Call `executor.execute("unknown_tool", {})` | Executor returns `success=False`, error: "Tool unknown_tool not found" |
| TC-15 | Case sensitivity | Call `get_course_info` with `course_code="bse4104"` (lowercase) | CourseTool normalizes to uppercase; returns `success=True` with BSE4104 data |
| TC-16 | Whitespace in input | Call `get_course_info` with `course_code="  BSE4104  "` (padded spaces) | CourseTool strips whitespace; returns `success=True` with BSE4104 data |

**Expected behavior:** Non-existent tools are caught at the executor level before any validation. Course codes are normalized (uppercase + strip) inside CourseTool.execute() to handle common student input variations.

---

## Evaluation Criteria

| Criterion | Description | Weight |
|-----------|-------------|--------|
| Graceful failure | All errors returned as structured dicts, no unhandled exceptions | 30% |
| Correct error layer | Executor-level vs tool-level errors returned at the right layer | 20% |
| Authorization gate | Approval checked before every write operation | 25% |
| Input normalization | Case/whitespace handled transparently | 10% |
| Service unavailability | Missing data files handled without crashes | 15% |

---

## Notes on Error Layers

Understanding which layer catches an error is important for test assertions:

**Executor-level errors** (checked in `ToolExecutor` before calling the tool):
- Tool not found → `r["success"] = False`, `r["error"] = "Tool X not found"`
- Required param missing → `r["success"] = False`, `r["error"] = "param is required"`
- Approval denied → `r["success"] = False`, `r["error"] = "Human approval denied"`

**Tool-level errors** (returned by `tool.execute()`):
- Invalid course code → `r["success"] = False`, `r["result"]["error"] = "Course X not found"`
- Invalid enum value → `r["success"] = False`, `r["result"]["error"] = "info_type must be one of..."`
- Issue summary too long → `r["success"] = False`, `r["result"]["error"] = "issue_summary exceeds 500 characters"`
- Service unavailable → `r["success"] = False`, `r["result"]["error"] = "Course database unavailable"`
