"""Scripted demo runner — Week 8 deliverable.

Runs seven curated scenarios through the real StudentSupportAgent and
prints a readable trace. No LLM dependency in the runner itself; the
agent uses whatever model is configured in .env.

Usage:
    python demo/run_demo.py                  # all scenarios, paused
    python demo/run_demo.py --scenario 4     # one scenario
    python demo/run_demo.py --fast           # no pauses (for evidence)
"""
import argparse
import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _REPO_ROOT / "src"
for _p in (_REPO_ROOT, _SRC_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
except ImportError:
    pass

from agent.agent import StudentSupportAgent
from agent.planner import Planner
from guardrails.guardrail_manager import GuardrailManager
from models.model_client import ModelClient
from observability.logger import AgentLogger
from orchestration.tool_executor import ToolExecutor
from rag.pipeline import RAGPipeline
from tools.course_tool import CourseTool
from tools.ticket_tool import TicketTool
from tools.ticket_status_tool import TicketStatusTool


def build_agent():
    log = AgentLogger(log_dir="logs/demo")
    executor = ToolExecutor(
        [CourseTool(), TicketTool(), TicketStatusTool()], logger=log
    )
    return StudentSupportAgent(
        model_client=ModelClient(),
        rag_pipeline=RAGPipeline(logger=log),
        tool_executor=executor,
        planner=Planner(ModelClient(), logger=log),
        logger=log,
        guardrails=GuardrailManager(logger=log),
    ), log


def print_header(i, total, scenario):
    print()
    print("=" * 68)
    print(f"  SCENARIO {i}/{total}  —  {scenario['title']}")
    print("=" * 68)
    print(f"  NARRATIVE:  {scenario['narrative']}")
    print(f"  QUESTION:   {scenario['question']}")
    print(f"  EXPECTED:   stop_reason = {scenario['expected_stop_reason']}")
    print("-" * 68)


def print_result(result, log, scenario):
    print(f"  RESPONSE:   {result['response'][:400]}")
    print(f"  STOP:       {result['stop_reason']}")
    print(f"  ITERATIONS: {result['iterations']}")
    print(f"  TRACE:      {result['trace_file']}")
    print(f"  LOG:        {log.log_file}")
    expected = scenario["expected_stop_reason"]
    if isinstance(expected, str):
        expected = [expected]
    passed = result["stop_reason"] in expected
    print(f"  RESULT:     [{'PASS' if passed else 'FAIL'}]")
    print("=" * 68)
    return passed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=int, help="run only scenario N")
    parser.add_argument("--fast", action="store_true", help="no pauses")
    args = parser.parse_args()

    scenarios = json.loads(
        (_REPO_ROOT / "demo" / "scenarios.json").read_text(encoding="utf-8")
    )["scenarios"]
    if args.scenario:
        scenarios = [scenarios[args.scenario - 1]]

    agent, log = build_agent()
    passed = 0
    for i, scenario in enumerate(scenarios, 1):
        print_header(i, len(scenarios), scenario)
        t0 = time.time()
        try:
            result = agent.run(scenario["question"])
        except Exception as e:
            print(f"  EXCEPTION:  {e}")
            print("=" * 68)
            continue
        print(f"  LATENCY:    {time.time() - t0:.2f}s")
        if print_result(result, log, scenario):
            passed += 1
        if not args.fast and i < len(scenarios):
            input("\n  [Enter] for next scenario... ")

    print(f"\n{passed}/{len(scenarios)} scenarios in expected state")
    return 0 if passed == len(scenarios) else 1


if __name__ == "__main__":
    sys.exit(main())