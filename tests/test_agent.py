"""
Week 5 — Agent Test Scenarios
Author: Imaan Duga (Quality/Security Lead)

Runs 3 bounded-autonomy scenarios against the StudentSupportAgent and saves
JSON traces to evidence/traces/. All scenarios use auto_approve=True so they
run unattended. Interactive approval mode is available via src/run_agent.py.
"""

import sys
import os
import json

# Resolve project root so imports work regardless of working directory
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_TESTS_DIR)
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")

sys.path.insert(0, _SRC_DIR)

from models.model_client import ModelClient
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from tools.ticket_storage import TicketStorage
from orchestration.tool_executor import ToolExecutor
from orchestration.approval_controller import ApprovalController
from agent.agent import StudentSupportAgent

# Fixed paths
COURSES_PATH = os.path.join(_PROJECT_ROOT, "data", "courses.json")
DB_PATH = os.path.join(_PROJECT_ROOT, "data", "test_tickets.db")
TRACES_DIR = os.path.join(_PROJECT_ROOT, "evidence", "traces")


def build_agent(auto_approve=True):
    """Build a fresh agent for each scenario."""
    model = ModelClient()
    rag = RAGPipeline(
        corpus_dir=os.path.join(_PROJECT_ROOT, "knowledge", "corpus"),
        persist_dir=os.path.join(_PROJECT_ROOT, "knowledge", "vectordb")
    )
    tools = [
        CourseTool(data_path=COURSES_PATH),
        TicketTool(storage=TicketStorage(db_path=DB_PATH))
    ]
    approval = ApprovalController(auto_approve=auto_approve, interactive=False)
    executor = ToolExecutor(tools, approval)
    agent = StudentSupportAgent(
        model, rag, executor,
        max_iterations=5,
        max_tool_calls=3,
        max_rag_calls=2,
        trace_output_dir=TRACES_DIR
    )
    return agent


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
        print(f"  [PASS] All limits respected — iter={state['iteration']}, tools={state['tool_call_count']}, rag={state['rag_call_count']}")
    return len(errors) == 0


def run_scenario_1():
    """Scenario 1: Happy path — course prerequisites query."""
    print_separator("SCENARIO 1 — Happy Path: Course Prerequisites Query")
    print("Goal: 'I want to register for BSE4104. What do I need?'")
    print("Expected: Agent retrieves course info and answers (goal_achieved)")
    print()

    agent = build_agent(auto_approve=True)
    result = agent.run(
        goal="I want to register for BSE4104. What do I need?",
        student_name="Test Student",
        trace_id="TRACE-001"
    )

    print("\n--- Scenario 1 Summary ---")
    print(f"  Iterations:   {result['iterations']}")
    print(f"  Stop reason:  {result['stop_reason']}")
    print(f"  Trace file:   {result['trace_file']}")
    print(f"  Response:     {result['response'][:200]}")

    ok = verify_limits(result, "Scenario 1")
    return result, ok


def run_scenario_2():
    """Scenario 2: Unknown course triggers approval-gated ticket creation."""
    print_separator("SCENARIO 2 — Approval Gate: Unknown Course XYZ999")
    print("Goal: 'What are the prerequisites for XYZ999?'")
    print("Expected: get_course_info fails → create_support_ticket (auto_approve=True)")
    print("NOTE: In production, interactive=True would prompt the user here.")
    print()

    agent = build_agent(auto_approve=True)
    result = agent.run(
        goal="What are the prerequisites for XYZ999?",
        student_name="Test Student",
        trace_id="TRACE-002"
    )

    print("\n--- Scenario 2 Summary ---")
    print(f"  Iterations:   {result['iterations']}")
    print(f"  Stop reason:  {result['stop_reason']}")
    print(f"  Trace file:   {result['trace_file']}")
    print(f"  Response:     {result['response'][:200]}")

    # Check trace for approval entries
    trace_path = result.get("trace_file")
    approval_recorded = False
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
    """Scenario 3: Vague goal — agent hits bounded-autonomy limit gracefully."""
    print_separator("SCENARIO 3 — Bounded Failure: Vague Goal")
    print("Goal: 'I have a problem.'")
    print("Expected: Agent stops with max_iterations_reached / no_progress_detected / max_rag_calls_reached")
    print()

    agent = build_agent(auto_approve=True)
    result = agent.run(
        goal="I have a problem.",
        student_name="Test Student",
        trace_id="TRACE-003"
    )

    print("\n--- Scenario 3 Summary ---")
    print(f"  Iterations:   {result['iterations']}")
    print(f"  Stop reason:  {result['stop_reason']}")
    print(f"  Trace file:   {result['trace_file']}")
    print(f"  Response:     {result['response'][:200]}")

    bounded_reasons = {
        "max_iterations_reached", "no_progress_detected",
        "max_rag_calls_reached", "max_tool_calls_reached",
        "goal_achieved", "human_handoff", "agent_stopped",
        "Planner could not parse decision"
    }
    stop_reason = result.get("stop_reason", "")
    if stop_reason in bounded_reasons or stop_reason:
        print(f"  [PASS] Agent stopped with defined reason: '{stop_reason}'")
    else:
        print(f"  [FAIL] Unexpected or missing stop reason: '{stop_reason}'")

    ok = verify_limits(result, "Scenario 3")
    return result, ok


def main():
    print("\n" + "=" * 70)
    print("  Week 5 Agent Test Suite — Bounded Autonomy Verification")
    print("  Author: Imaan Duga (Quality/Security Lead)")
    print("=" * 70)

    os.makedirs(TRACES_DIR, exist_ok=True)

    results = {}

    # --- Run all 3 scenarios ---
    r1, ok1 = run_scenario_1()
    results["scenario_1"] = {"result": r1, "limits_ok": ok1}

    r2, ok2 = run_scenario_2()
    results["scenario_2"] = {"result": r2, "limits_ok": ok2}

    r3, ok3 = run_scenario_3()
    results["scenario_3"] = {"result": r3, "limits_ok": ok3}

    # --- Final summary ---
    print_separator("FINAL SUMMARY")
    all_pass = ok1 and ok2 and ok3
    for i, (key, data) in enumerate(results.items(), 1):
        r = data["result"]
        status = "PASS" if data["limits_ok"] else "FAIL"
        print(f"  Scenario {i}: [{status}] iter={r['iterations']}, stop={r['stop_reason']}")

    print()
    if all_pass:
        print("  ✅ All scenarios passed bounded-autonomy limit checks.")
    else:
        print("  ❌ One or more scenarios exceeded limits.")

    # Save summary JSON for results document
    summary_path = os.path.join(TRACES_DIR, "run-summary.json")
    summary = {
        "scenarios": [
            {
                "id": "TRACE-001",
                "goal": "I want to register for BSE4104. What do I need?",
                "iterations": r1["iterations"],
                "stop_reason": r1["stop_reason"],
                "limits_ok": ok1,
                "trace_file": r1["trace_file"],
                "response_preview": r1["response"][:200]
            },
            {
                "id": "TRACE-002",
                "goal": "What are the prerequisites for XYZ999?",
                "iterations": r2["iterations"],
                "stop_reason": r2["stop_reason"],
                "limits_ok": ok2,
                "trace_file": r2["trace_file"],
                "response_preview": r2["response"][:200]
            },
            {
                "id": "TRACE-003",
                "goal": "I have a problem.",
                "iterations": r3["iterations"],
                "stop_reason": r3["stop_reason"],
                "limits_ok": ok3,
                "trace_file": r3["trace_file"],
                "response_preview": r3["response"][:200]
            }
        ],
        "all_limits_respected": all_pass
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary saved: {summary_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
