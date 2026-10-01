# Agent Architecture

## Overview
The StudentSupportAgent is a bounded, goal-directed agent that resolves
student issues through a Sense → Plan → Act → Observe → Evaluate loop.
"Bounded" means the loop always terminates — on a final answer, a stop
condition, or a hard iteration limit — never runs indefinitely.

## The Loop (Figure 2)
User (Student)
-> Agent Orchestrator (src/agent/agent.py)

SENSE (context) -> PLAN (decide) -> ACT (execute) -> OBSERVE (update) -> EVALUATE (stop?)
^ |
|_______________________ Continue: loop back to SENSE ___________________|

EVALUATE -> Stop -> Final Response
| Step | Responsibility |
|---|---|
| 1. SENSE | Understand the goal and current state |
| 2. PLAN | Decide the next action (Planner.plan_next_action) |
| 3. ACT | Execute a tool call or generate an answer |
| 4. OBSERVE | Process the result, update agent state |
| 5. EVALUATE | Check stop condition: continue (loop to SENSE) or stop (return final response + trace) |

## Supporting Layers
The orchestrator calls down into three layers, each backed by a data store:

| Layer | Role | Backing store |
|---|---|---|
| RAG Pipeline | Retrieval | Chroma DB (vectors) |
| Tool Layer | 2 tools (get_course_info, create_support_ticket) | courses.json / tickets.db |
| Guardrails | Limits | Approval Controller (human gate) |

## Stop Conditions
The agent stops (EVALUATE → Stop) when any of these are true:
- The planner returns an `answer` action — goal resolved
- The planner returns a `stop` action — no progress possible
- `state.iteration` reaches `max_iterations` (hard limit: 5)
- `state.tool_call_count` reaches its limit (3) or `state.rag_call_count` reaches its limit (2)

Otherwise EVALUATE returns "continue" and the loop runs SENSE again with
the updated state.

## Example Multi-Step Flow
1. SENSE: goal = "What are the prerequisites for BSE4104, and is my
   registration still open?"
2. PLAN: decide `call_tool(get_course_info, BSE4104, prerequisites)`
3. ACT: execute tool call
4. OBSERVE: record result, update state
5. EVALUATE: continue — registration question still unanswered
6. SENSE → PLAN: decide `rag_retrieve("registration deadline")`
7. ACT → OBSERVE → EVALUATE: continue
8. SENSE → PLAN: decide `answer(...)` combining both results
9. EVALUATE: stop → final response + full trace returned to student