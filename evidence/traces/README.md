# Evidence — Agent Traces

This directory contains JSON execution traces from the bounded StudentSupportAgent (Week 5).

## Trace Index

| File | Scenario | Goal | Stop Reason |
|---|---|---|---|
| `TRACE-001.json` | Happy path | "I want to register for BSE4104. What do I need?" | `goal_achieved` |
| `TRACE-002.json` | Approval gate | "What are the prerequisites for XYZ999?" | `goal_achieved` or `human_handoff` |
| `TRACE-003.json` | Bounded failure | "I have a problem." | `max_iterations_reached` / `no_progress_detected` |
| `run-summary.json` | All scenarios | — | Summary of all 3 runs |

## Trace Schema

Each `TRACE-NNN.json` file contains:

```
{
  "trace_id":        string   — unique trace identifier
  "goal":            string   — student's original question
  "started_at":      string   — ISO timestamp
  "iterations":      array    — per-iteration records (action, plan, observation)
  "tool_calls":      array    — every tool execution with arguments and result
  "rag_calls":       array    — every RAG query with num_results and sources
  "human_approvals": array    — every approval decision (tool, arguments, approved)
  "final_response":  string   — agent's final reply to the student
  "stop_reason":     string   — why the loop ended
  "completed_at":    string   — ISO timestamp
}
```

## Bounded-Autonomy Limits Verified

| Limit | Value |
|---|---|
| Max iterations | 5 |
| Max tool calls | 3 |
| Max RAG calls | 2 |

## How to Re-Run

```bash
cd "d:\SOFTWARE ENGINEERING\YR4 SEM1\EMERGING TRENDS\AI_Agentic Capstone\AI_Agentic_Capstone-main"
python tests/test_agent.py
```

Traces are overwritten each run. Archive previous traces before re-running if you need to compare.

## Notes

- `auto_approve=True` is used in the test script so it runs unattended.
- For interactive approval (production mode), run `python src/run_agent.py`.
- Traces are not committed to git (see `.gitignore` — `evidence/` is excluded).
