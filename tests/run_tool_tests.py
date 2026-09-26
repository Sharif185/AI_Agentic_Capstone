"""
run_tool_tests.py
-----------------
Author  : Imaan (Quality/Security Lead)
Date    : 23rd September 2026
Purpose : Programmatically run all 11 tool failure and authorization tests,
          print a human-readable summary, and save results to
          tests/week4-tool-results.json.

Test coverage:
  - Missing required parameters (executor-level validation)
  - Invalid input values (tool-level validation)
  - Authorization gate (approval_required tools)
  - Service unavailability (missing data sources)
  - Unknown tool names
  - Input normalization (case/whitespace)
"""

import sys
import os
import json
from datetime import datetime

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.tools.course_tool import CourseTool
from src.tools.ticket_tool import TicketTool
from src.orchestration.tool_executor import ToolExecutor
from src.orchestration.approval_controller import ApprovalController


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_executor(auto_approve=True, interactive=False):
    """Build a ToolExecutor with real tools and a configured ApprovalController."""
    # Use absolute paths so tests work regardless of CWD
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    courses_path = os.path.join(project_root, "data", "courses.json")
    db_path = os.path.join(project_root, "data", "test_tickets.db")

    from src.tools.ticket_storage import TicketStorage
    course_tool = CourseTool(data_path=courses_path)
    ticket_tool = TicketTool(storage=TicketStorage(db_path=db_path))

    approval = ApprovalController(auto_approve=auto_approve, interactive=interactive)
    return ToolExecutor(tools=[course_tool, ticket_tool], approval_controller=approval)


def pass_fail(condition):
    return "PASS" if condition else "FAIL"


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

results = []


def run_test(test_id, description, fn):
    """Execute a single test function and record the result."""
    try:
        passed, details = fn()
        status = "PASS" if passed else "FAIL"
    except Exception as e:
        passed = False
        status = "ERROR"
        details = f"Unhandled exception: {str(e)}"

    results.append({
        "test_id": test_id,
        "description": description,
        "status": status,
        "details": details
    })

    icon = "✓" if passed else "✗"
    print(f"  [{icon}] {test_id}: {description}")
    if not passed:
        print(f"        → {details}")
    return passed


# ── Part 1: Missing Parameter Tests ─────────────────────────────────────────

def test_missing_course_code():
    """TC-01: get_course_info called with no arguments."""
    executor = make_executor()
    r = executor.execute("get_course_info", {})
    passed = r["success"] is False and "required" in r.get("error", "").lower()
    return passed, f"success={r['success']}, error={r.get('error')}"


def test_missing_issue_summary():
    """TC-02: create_support_ticket missing issue_summary."""
    executor = make_executor()
    r = executor.execute("create_support_ticket", {"student_name": "Alice Nakato"})
    passed = r["success"] is False and "required" in r.get("error", "").lower()
    return passed, f"success={r['success']}, error={r.get('error')}"


def test_missing_student_name():
    """TC-03: create_support_ticket missing student_name."""
    executor = make_executor()
    r = executor.execute("create_support_ticket", {"issue_summary": "Lost student ID card"})
    passed = r["success"] is False and "required" in r.get("error", "").lower()
    return passed, f"success={r['success']}, error={r.get('error')}"


# ── Part 2: Invalid Input Tests ──────────────────────────────────────────────

def test_invalid_course_code():
    """TC-05: course_code that doesn't exist in the database."""
    executor = make_executor()
    r = executor.execute("get_course_info", {"course_code": "INVALID999"})
    # Tool-level error: r["result"]["error"] contains the message
    error_msg = r.get("result", {}).get("error", "") if isinstance(r.get("result"), dict) else ""
    passed = r["success"] is False and "not found" in error_msg.lower()
    return passed, f"success={r['success']}, result_error={error_msg}"


def test_invalid_info_type():
    """TC-06: info_type enum value not in allowed list."""
    executor = make_executor()
    r = executor.execute("get_course_info", {"course_code": "BSE4104", "info_type": "syllabus"})
    error_msg = r.get("result", {}).get("error", "") if isinstance(r.get("result"), dict) else ""
    passed = r["success"] is False and "info_type must be one of" in error_msg
    return passed, f"success={r['success']}, result_error={error_msg}"


def test_issue_summary_too_long():
    """TC-07: issue_summary exceeds 500-character limit."""
    executor = make_executor()
    long_summary = "x" * 501
    r = executor.execute("create_support_ticket", {
        "student_name": "Alice Nakato",
        "issue_summary": long_summary
    })
    error_msg = r.get("result", {}).get("error", "") if isinstance(r.get("result"), dict) else ""
    passed = r["success"] is False and "exceeds 500" in error_msg
    return passed, f"success={r['success']}, result_error={error_msg}"


def test_invalid_priority():
    """TC-08: priority value not in [low, medium, high]."""
    executor = make_executor()
    r = executor.execute("create_support_ticket", {
        "student_name": "Alice Nakato",
        "issue_summary": "Cannot register for BSE4104",
        "priority": "urgent"
    })
    error_msg = r.get("result", {}).get("error", "") if isinstance(r.get("result"), dict) else ""
    passed = r["success"] is False and "priority must be" in error_msg
    return passed, f"success={r['success']}, result_error={error_msg}"


# ── Part 3: Authorization Tests ──────────────────────────────────────────────

def test_approval_granted():
    """TC-09: auto_approve=True allows ticket creation."""
    executor = make_executor(auto_approve=True)
    r = executor.execute("create_support_ticket", {
        "student_name": "Alice Nakato",
        "issue_summary": "Need help with course registration"
    })
    passed = r["success"] is True and r.get("result", {}).get("ticket_id", "").startswith("TICKET-")
    ticket_id = r.get("result", {}).get("ticket_id", "none")
    return passed, f"success={r['success']}, ticket_id={ticket_id}"


def test_approval_denied():
    """TC-10: auto_approve=False, non-interactive → approval denied."""
    from src.tools.ticket_storage import TicketStorage
    approval = ApprovalController(auto_approve=False, interactive=False)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    courses_path = os.path.join(project_root, "data", "courses.json")
    db_path = os.path.join(project_root, "data", "test_tickets.db")
    course_tool = CourseTool(data_path=courses_path)
    ticket_tool = TicketTool(storage=TicketStorage(db_path=db_path))
    executor = ToolExecutor(tools=[course_tool, ticket_tool], approval_controller=approval)

    r = executor.execute("create_support_ticket", {
        "student_name": "Alice Nakato",
        "issue_summary": "Need help with course registration"
    })
    passed = r["success"] is False and "Human approval denied" in r.get("error", "")
    return passed, f"success={r['success']}, error={r.get('error')}"


# ── Part 4: Unavailable Service Tests ────────────────────────────────────────

def test_course_database_unavailable():
    """TC-12: CourseTool with a non-existent data_path."""
    course_tool = CourseTool(data_path="data/nonexistent_courses.json")
    approval = ApprovalController(auto_approve=True)
    executor = ToolExecutor(tools=[course_tool], approval_controller=approval)

    r = executor.execute("get_course_info", {"course_code": "BSE4104"})
    error_msg = r.get("result", {}).get("error", "") if isinstance(r.get("result"), dict) else ""
    passed = r["success"] is False and "unavailable" in error_msg.lower()
    return passed, f"success={r['success']}, result_error={error_msg}"


# ── Part 5: Unexpected Tool Response Tests ───────────────────────────────────

def test_unknown_tool():
    """TC-14: Execute a tool name that was never registered."""
    executor = make_executor()
    r = executor.execute("unknown_tool", {})
    passed = r["success"] is False and "not found" in r.get("error", "").lower()
    return passed, f"success={r['success']}, error={r.get('error')}"


# Note: TC-15 (lowercase) and TC-16 (whitespace) are covered in test_tool_calling.py
# as part of the end-to-end normalization scenarios.


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Week 4 Tool Tests — Failure & Authorization")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Part 1: Missing Parameters
    print("\n── Part 1: Missing Parameter Tests ──")
    run_test("TC-01", "Missing course_code → executor-level error", test_missing_course_code)
    run_test("TC-02", "Missing issue_summary → executor-level error", test_missing_issue_summary)
    run_test("TC-03", "Missing student_name → executor-level error", test_missing_student_name)

    # Part 2: Invalid Input
    print("\n── Part 2: Invalid Input Tests ──")
    run_test("TC-05", "Invalid course code → tool-level 'not found'", test_invalid_course_code)
    run_test("TC-06", "Invalid info_type → tool-level enum error", test_invalid_info_type)
    run_test("TC-07", "Issue summary > 500 chars → tool-level error", test_issue_summary_too_long)
    run_test("TC-08", "Invalid priority enum → tool-level error", test_invalid_priority)

    # Part 3: Authorization
    print("\n── Part 3: Authorization Tests ──")
    run_test("TC-09", "auto_approve=True → ticket created successfully", test_approval_granted)
    run_test("TC-10", "auto_approve=False, non-interactive → denied", test_approval_denied)

    # Part 4: Unavailable Service
    print("\n── Part 4: Unavailable Service Tests ──")
    run_test("TC-12", "Missing courses.json → 'database unavailable'", test_course_database_unavailable)

    # Part 5: Unexpected Responses
    print("\n── Part 5: Unexpected Tool Response Tests ──")
    run_test("TC-14", "Unknown tool name → 'not found' error", test_unknown_tool)

    # ── Summary ──────────────────────────────────────────────────────────────
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    total = len(results)

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  |  {failed} failed", end="")
    if errors:
        print(f"  |  {errors} errors", end="")
    print()
    print("=" * 60)

    # Save JSON results
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "week4-tool-results.json")
    report = {
        "run_at": datetime.now().isoformat(),
        "summary": {"passed": passed, "failed": failed, "errors": errors, "total": total},
        "tests": results
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    return 0 if (failed == 0 and errors == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
