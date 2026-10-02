"""
Week 5 — Agent Test Scenarios
Author: Imaan Duga (Quality/Security Lead)

Runs 3 bounded-autonomy scenarios against the StudentSupportAgent and saves
JSON traces to evidence/traces/. All scenarios use auto_approve=True so they
run unattended. Interactive approval mode is available via src/run_agent.py.

Uses the real agent API from Mus and Louis's implementation:
  - tools.approval_controller.ApprovalController
  - tools.tool_executor.ToolExecutor
  - agent.planner.Planner
  - agent.agent.StudentSupportAgent
"""

import sys
import os
import json
import shutil

# Resolve project root so imports work regardless of working directory
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_TESTS_DIR)
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")

sys.path.insert(0, _SRC_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from tools.approval_controller import ApprovalController
from tools.tool_executor import ToolExecutor
from agent.planner import Planner
from agent.agent import StudentSupportAgent

# Fixed paths
COURSES_PATH = os.path.join(_PROJECT_ROOT, "data", "courses.json")
TICKETS_PATH = os.path.join(_PROJECT_ROOT, "data", "test_tickets.json")
TRACES_DIR = os.path.join(_PROJECT_ROOT, "evidence", "traces")


def build_agent():
    """
    Build a fresh agent for each scenario using the real API.
    auto_approve=True is implemented via decision_fn — the ONLY supported
    way to bypass the interactive prompt per ApprovalController's contract.
    """
    model = ModelClient()

    rag = RAGPipeline(
        corpus_dir=os.path.join(_PROJECT_ROOT, "knowledge", "corpus"),
        persist_dir=os.path.join(_PROJECT_ROOT, "knowledge", "vectordb"),
    )

    # ApprovalController: pass decision_fn to auto-approve all tool calls
    approval = ApprovalController(decision_fn=lambda tool_name, args: True)

    # ToolExecutor takes only the approval_controller; tools registered separately
    executor = ToolExecutor(approval)
    executor.register(CourseTool(data_path=COURSES_PATH))
    executor.register(TicketTool(storage_path=TICKETS_PATH))

    planner = Planner(model)

    agent = StudentSupportAgent(
        model_client=model,
        rag_pipeline=rag,
        tool_executor=executor,
        planner=planner,
        max_iterations=5,
        max_tool_calls=3,
        max_rag_calls=2,
        trace_dir=TRACES_DIR,
    )
    return agent


def copy_trace_to_fixed_name(trace_file, fixed_name):
    """
    Copy the auto-named trace (TRACE-YYYYMMDDHHMMSS-xxxxxx.json) produced
    by Mus's Tracer to a fixed name (TRACE-001.json etc.) for Louis to
    find consistently.  The auto-named original is kept as well.
    """
    if trace_file and os.path.exists(trace_file):
        dest = os.path.join(TRACES_DIR, fixed_name)
        shutil.copy2(trace_file, dest)
        print(f"  Copied trace → {dest}")
        return dest
    print(f"  [WARN] Trace file not found, could not copy to {fixed_name}")
    return None


def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def verify_limits(result, scenario_name):
    """Assert bounded-autonomy limits were respected."""
    state = result["state"]
    errors = []
    if state["iteration"] > 5:
        errors.append(f"EXCEEDED iteration limit: {state['iteration']}")
    if state["tool_call_count"] > 3:
        errors.append(f"EXCEEDED tool call limit: {state['tool_call_count']}")
    if state["rag_call_count"] > 2:
        errors.append(f"EXCEEDED RAG call limit: {state['rag_call_count']}")
    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
    else:
        print(
            f"  [PASS] All limits respected — "
            f"iter={state['iteration']}, "
            f"tools={state['tool_call_count']}, "
            f"rag={state['rag_call_count']}"
        )
    return len(errors) == 0


def run_scenario_1():
    """Scenario 1: Happy path — course prerequisites query."""
    print_separator("SCENARIO 1 — Happy Path: Course Prerequisites Query")
    print("Goal: 'I want to register for BSE4104. What do I need?'")
    print("Expected: Agent retrieves course info and answers (goal_achieved)")
    print()

    agent = build_agent()
    result = agent.run(
        goal="I want to register for BSE4104. What do I need?",
        student_name="Test Student",
    )

    print("\n--- Scenario 1 Summary ---")
    print(f"  Iterations:   {result['iterations']}")
    print(f"  Stop reason:  {result['stop_reason']}")
    print(f"  Auto trace:   {result['trace_file']}")
    print(f"  Response:     {result['response'][:200]}")

    copy_trace_to_fixed_name(result["trace_file"], "TRACE-001.json")
    ok = verify_limits(result, "Scenario 1")
    return result, ok


def run_scenario_2():
    """Scenario 2: Unknown course — should fail lookup, potentially create ticket."""
    print_separator("SCENARIO 2 — Approval Gate: Unknown Course XYZ999")
    print("Goal: 'What are the prerequisites for XYZ999?'")
    print("Expected: get_course_info fails → create_support_ticket (auto_approve=True)")
    print("NOTE: In production, interactive=True would prompt the user here.")
    print()

    agent = build_agent()
    result = agent.run(
        goal="What are the prerequisites for XYZ999?",
        student_name="Test Student",
    )

    print("\n--- Scenario 2 Summary ---")
    print(f"  Iterations:   {result['iterations']}")
    print(f"  Stop reason:  {result['stop_reason']}")
    print(f"  Auto trace:   {result['trace_file']}")
    print(f"  Response:     {result['response'][:200]}")

    copy_trace_to_fixed_name(result["trace_file"], "TRACE-002.json")

    # Inspect trace for approval entries and ticket attempts
    trace_path = result.get("trace_file")
    if trace_path and os.path.exists(trace_path):
        with open(trace_path, "r", encoding="utf-8") as f:
            trace = json.load(f)
        approval_recorded = len(trace.get("human_approvals", [])) > 0
        ticket_attempted = any(
            tc.get("tool") == "create_support_ticket"
            for tc in trace.get("tool_calls", [])
        )
        if ticket_attempted:
            print("  [PASS] create_support_ticket was attempted")
        else:
            print("  [INFO] create_support_ticket was not attempted (agent may have answered differently)")
        if approval_recorded:
            print("  [PASS] Approval gate recorded in trace")
        else:
            print("  [INFO] No approval entries (ticket may not have been created)")

    ok = verify_limits(result, "Scenario 2")
    return result, ok


def run_scenario_3():
    """Scenario 3: Vague goal — agent stops gracefully without exceeding limits."""
    print_separator("SCENARIO 3 — Bounded Failure: Vague Goal")
    print("Goal: 'I have a problem.'")
    print("Expected: Agent stops with a defined stop_reason (no crash)")
    print()

    agent = build_agent()
    result = agent.run(
        goal="I have a problem.",
        student_name="Test Student",
    )

    print("\n--- Scenario 3 Summary ---")
    print(f"  Iterations:   {result['iterations']}")
    print(f"  Stop reason:  {result['stop_reason']}")
    print(f"  Auto trace:   {result['trace_file']}")
    print(f"  Response:     {result['response'][:200]}")

    copy_trace_to_fixed_name(result["trace_file"], "TRACE-003.json")

    stop_reason = result.get("stop_reason", "")
    if stop_reason:
        print(f"  [PASS] Agent stopped with defined reason: '{stop_reason}'")
    else:
        print(f"  [FAIL] Missing stop reason")

    ok = verify_limits(result, "Scenario 3")
    return result, ok


def main():
    print("\n" + "=" * 70)
    print("  Week 5 Agent Test Suite — Bounded Autonomy Verification")
    print("  Author: Imaan Duga (Quality/Security Lead)")
    print("=" * 70)

    os.makedirs(TRACES_DIR, exist_ok=True)

    # --- Run all 3 scenarios ---
    r1, ok1 = run_scenario_1()
    r2, ok2 = run_scenario_2()
    r3, ok3 = run_scenario_3()

    # --- Final summary ---
    print_separator("FINAL SUMMARY")
    all_pass = ok1 and ok2 and ok3
    scenarios = [(1, r1, ok1), (2, r2, ok2), (3, r3, ok3)]
    for i, r, ok in scenarios:
        status = "PASS" if ok else "FAIL"
        print(f"  Scenario {i}: [{status}] iter={r['iterations']}, stop={r['stop_reason']}")

    print()
    if all_pass:
        print("  \u2705 All scenarios passed bounded-autonomy limit checks.")
    else:
        print("  \u274c One or more scenarios exceeded limits.")

    # Save machine-readable summary for run-summary.json
    summary_path = os.path.join(TRACES_DIR, "run-summary.json")
    summary = {
        "scenarios": [
            {
                "id": "TRACE-001",
                "goal": "I want to register for BSE4104. What do I need?",
                "iterations": r1["iterations"],
                "stop_reason": r1["stop_reason"],
                "limits_ok": ok1,
                "auto_trace_file": r1["trace_file"],
                "fixed_trace_file": os.path.join(TRACES_DIR, "TRACE-001.json"),
                "response_preview": r1["response"][:200],
            },
            {
                "id": "TRACE-002",
                "goal": "What are the prerequisites for XYZ999?",
                "iterations": r2["iterations"],
                "stop_reason": r2["stop_reason"],
                "limits_ok": ok2,
                "auto_trace_file": r2["trace_file"],
                "fixed_trace_file": os.path.join(TRACES_DIR, "TRACE-002.json"),
                "response_preview": r2["response"][:200],
            },
            {
                "id": "TRACE-003",
                "goal": "I have a problem.",
                "iterations": r3["iterations"],
                "stop_reason": r3["stop_reason"],
                "limits_ok": ok3,
                "auto_trace_file": r3["trace_file"],
                "fixed_trace_file": os.path.join(TRACES_DIR, "TRACE-003.json"),
                "response_preview": r3["response"][:200],
            },
        ],
        "all_limits_respected": all_pass,
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary saved: {summary_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
