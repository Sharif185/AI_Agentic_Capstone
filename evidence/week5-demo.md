# Week 5 Demo Evidence: Bounded Agent Loop

**Component:** Application/Integration (Mus)
**Loop:** Sense → Plan → Act → Observe → Evaluate, limits `max_iterations=5`, `max_tool_calls=3`, `max_rag_calls=2`, no-progress detection.

## How to read this document

Two kinds of evidence, kept apart:

- **Live (your machine, real Gemini planner).** Only what you actually ran and reported. Anything not yet run is marked pending.
- **Orchestration traces (sandbox, scripted planner).** `TRACE-001..003.json` in `evidence/traces/` were produced by running the real `StudentSupportAgent`, `ToolExecutor`, `CourseTool`, `TicketTool` and `StopConditions` with a *scripted* planner and stub RAG, and an auto-approve decision. They prove the loop, stop conditions and tracing work. They do **not** show how the live model plans.

## Scenario 1: course registration question

**Goal:** `I want to register for BSE4104. What do I need?`

| | Live (your machine) | Orchestration trace (sandbox) |
|---|---|---|
| Trace file | `TRACE-20261002061616-d87bbd` | `TRACE-001.json` |
| Iterations | 2 | 3 (rag_retrieve → call_tool → answer) |
| Tools | (paste from trace) | `get_course_info` → BSE3101, BSE3102, CS103 |
| Stop reason | `goal_achieved` ✅ | `goal_achieved` |
| Final response | (paste) | grounded in the tool result |

## Scenario 2: failure and recovery

**Goal:** `What are the prerequisites for XYZ999?`
**Target (acceptance criteria):** lookup fails, retrieval finds nothing, agent escalates by creating a ticket (with human approval) and says so.

| | Live (your machine) | Orchestration trace (sandbox) |
|---|---|---|
| Trace file | `TRACE-20261002061647-41a265` | `TRACE-002.json` |
| Iterations | 4 | 4 |
| Sequence | **Not yet confirmed. Paste the trace.** | `get_course_info` (course not found) → `rag_retrieve` (0 results) → `create_support_ticket` (approved, `TCK-0001`) → `stop` |
| Stop reason | `stop_requested` | `stop_requested` |
| Final response | "unable to retrieve... due to system issues with our course database and search services"; no ticket mentioned | "couldn't find course XYZ999... created a support ticket" |

**Open issue:** the live reply blames "system issues" rather than saying the course does not exist, and does not mention a ticket. Open `evidence/traces/TRACE-20261002061647-41a265.json` and check `tool_calls` and `human_approvals`: if `get_course_info` returned `No course found`, the planner's wording is the problem (planner prompt, Louis); if a tool call errored, that is a defect to fix. Not resolved here.

Note: stop reason is `stop_requested` when the planner chooses `stop`, and `human_handoff` only when an approval is denied.

## Scenario 3: vague request

**Goal:** `I have a problem.`
**Target:** agent stops safely and asks for detail instead of guessing.

| | Live (your machine) | Orchestration trace (sandbox) |
|---|---|---|
| Trace file | ⏳ pending, run it | `TRACE-003.json` |
| Iterations | | 2 (same `rag_retrieve` twice) |
| Stop reason | | `no_progress_detected` |
| Final response | | asks for more detail or offers a human |

## Documented failure and recovery

Gemini 3.x "thinking" tokens consumed the 500-token output budget, truncating the planner's JSON after about 60 characters, so every run ended `stop_requested` with `invalid_or_unparseable_planner_output`. Fix: `ModelClient.generate(..., disable_thinking=True)` for planner calls (thinking budget 0) plus a balanced-brace JSON parser. After the fix Scenario 1 passed live.

## Known gaps

- Acceptance-criteria text mentions `TICKET-0003` and `human_handoff` for Scenario 2; the code issues `TCK-xxxx` IDs and sets `human_handoff` only on denied approval.
- `docs/ai-boundary-matrix.md` says ticket creation needs no approval; the code requires it.
- The planner is a stand-in and needs review by the AI Engineering Lead.
