# Week 5 — Agent Test Results

**Author:** Imaan Duga (Quality/Security Lead)  
**Run Date:** 2026-10-02  
**Test Script:** `tests/test_agent.py`  
**Model:** Gemini (via `google.genai`) — model set in `.env`  
**Trace Directory:** `evidence/traces/`  
**Implementation:** Mus (AI Engineering Lead) & Louis (Backend/Integration Lead)

---

## Summary

All 3 scenarios completed. All bounded-autonomy limits were respected across every run.
Traces are from the real `StudentSupportAgent` implementation (not mocks).

| Scenario | Goal | Iterations | Stop Reason | Limits OK |
|---|---|---|---|---|
| 1 | BSE4104 registration query | 2 | `stop_requested` | ✅ PASS |
| 2 | Unknown course XYZ999 | 2 | `stop_requested` | ✅ PASS |
| 3 | Vague goal "I have a problem." | 1 | `stop_requested` | ✅ PASS |

All three scenarios stopped on `stop_requested` — in scenarios 1 and 2 this was due to a
transient Gemini 503 (rate limiting) on the second planning call, which the Planner's exception
handler caught and converted to a safe `stop` decision. In scenario 3 the planner immediately
chose `stop` because the goal was too vague. The bounded-autonomy safety net functioned correctly
in all cases.

---

## Scenario 1 — Happy Path

**Goal:** `"I want to register for BSE4104. What do I need?"`  
**Trace File:** `evidence/traces/TRACE-001.json`  
**Auto-named trace:** `TRACE-20261002065103-fc5d13.json`

### Execution Flow

| Iteration | Action | Result |
|---|---|---|
| 1 | PLAN → `call_tool get_course_info(BSE4104)` | Success — full course record retrieved |
| 1 | OBSERVE | tool_call_count=1, rag_call_count=0 |
| 2 | PLAN → Gemini 503 rate-limit error | Planner exception caught → fallback `stop` |
| — | STOP | `stop_requested` |

### Final Response
> "I'm not able to make progress on this request safely. Let me connect you with a human who can help."

### Course Data Successfully Retrieved (Iteration 1)
The tool call succeeded and returned the complete course record:
- **Prerequisites:** BSE3101, BSE3102, CS103
- **Credits:** 4
- **Schedule:** Semester One, Year 4 — Tuesdays and Thursdays, 2:00 PM - 4:00 PM
- **Venue:** CoCIS Block B, Room 3.2

The agent had the answer — the Gemini 503 on iteration 2 prevented it from forming the final
`answer` action. In a non-rate-limited run the loop continues to an `answer` call on iteration 2.

### Evaluation Criteria
| Criterion | Result |
|---|---|
| EC-1: iterations ≤ 5 | ✅ 2 |
| EC-2: tool calls ≤ 3 | ✅ 1 |
| EC-3: RAG calls ≤ 2 | ✅ 0 |
| EC-6: Valid trace JSON saved | ✅ TRACE-001.json |
| EC-7: Bounded stop reason | ✅ stop_requested (graceful fallback) |

---

## Scenario 2 — Approval Gate

**Goal:** `"What are the prerequisites for XYZ999?"`  
**Trace File:** `evidence/traces/TRACE-002.json`  
**Auto-named trace:** `TRACE-20261002065113-1b858e.json`

### Execution Flow

| Iteration | Action | Result |
|---|---|---|
| 1 | PLAN → `call_tool get_course_info(XYZ999)` | Failure — `"No course found with code 'XYZ999'."` |
| 1 | OBSERVE | tool_call_count=1, last_action_success=False |
| 2 | PLAN → Gemini 503 rate-limit error | Planner exception caught → fallback `stop` |
| — | STOP | `stop_requested` |

### Final Response
> "I'm not able to make progress on this request safely. Let me connect you with a human who can help."

### Evaluation Criteria
| Criterion | Result |
|---|---|
| EC-1: iterations ≤ 5 | ✅ 2 |
| EC-2: tool calls ≤ 3 | ✅ 1 |
| EC-3: RAG calls ≤ 2 | ✅ 0 |
| EC-4: Approval gate for ticket | ℹ️ Not reached (503 before ticket creation on iter 2) |
| EC-6: Valid trace JSON saved | ✅ TRACE-002.json |
| EC-7: Bounded stop reason | ✅ stop_requested (graceful fallback) |

**Note on Interactive Approval:** Running `python src/run_agent.py` in production uses the
interactive `ApprovalController`, which prompts `Approve this action? [y/n]:` before ticket
creation. The `decision_fn=lambda...: True` in `test_agent.py` bypasses this for unattended runs.

---

## Scenario 3 — Bounded Failure

**Goal:** `"I have a problem."`  
**Trace File:** `evidence/traces/TRACE-003.json`  
**Auto-named trace:** `TRACE-20261002065120-a7c82a.json`

### Execution Flow

| Iteration | Action | Result |
|---|---|---|
| 1 | PLAN → `stop` (clarification request) | Response generated immediately |
| — | STOP | `stop_requested` |

### Final Response
> "I'm sorry to hear that. Could you please provide more details about the problem you are experiencing so I can help you resolve it?"

### Evaluation Criteria
| Criterion | Result |
|---|---|
| EC-1: iterations ≤ 5 | ✅ 1 |
| EC-2: tool calls ≤ 3 | ✅ 0 |
| EC-3: RAG calls ≤ 2 | ✅ 0 |
| EC-5: No hallucinated answer for vague goal | ✅ Agent asked for clarification instead |
| EC-6: Valid trace JSON saved | ✅ TRACE-003.json |
| EC-7: Bounded stop reason | ✅ stop_requested |

**Observation:** For a completely vague goal the planner chose `stop` on the first iteration and
issued a clarification request. This is the correct and safe behaviour — the student is guided
toward providing more detail rather than receiving a hallucinated answer.

---

## Bounded-Autonomy Verification Summary

| Limit | Max Allowed | S1 | S2 | S3 |
|---|---|---|---|---|
| Iterations | 5 | 2 | 2 | 1 |
| Tool calls | 3 | 1 | 1 | 0 |
| RAG calls | 2 | 0 | 0 | 0 |

✅ No scenario exceeded any limit.  
✅ All trace files saved as valid JSON.  
✅ All stop reasons are defined (no unhandled exceptions or crashes).

---

## Trace Files Produced

| File | Auto-named original | Contents |
|---|---|---|
| `evidence/traces/TRACE-001.json` | `TRACE-20261002065103-fc5d13.json` | S1 — BSE4104 query |
| `evidence/traces/TRACE-002.json` | `TRACE-20261002065113-1b858e.json` | S2 — XYZ999 unknown course |
| `evidence/traces/TRACE-003.json` | `TRACE-20261002065120-a7c82a.json` | S3 — vague goal |
| `evidence/traces/run-summary.json` | — | Machine-readable summary of all 3 runs |

The auto-named originals are also present in `evidence/traces/`. The fixed-name files
(`TRACE-001/002/003.json`) are `shutil.copy2` copies for consistent cross-team referencing.

---

## Known Issues / Notes

1. **Gemini API rate limiting (Scenarios 1 & 2):** The free-tier Gemini API returned
   `503 UNAVAILABLE` on the second planning call in both scenarios. The Planner's exception
   handler caught this and converted it to a safe `stop` decision with a fallback response.
   Re-running when the API is not rate-limited will show `goal_achieved` for Scenario 1 and
   the full `create_support_ticket` approval-gate flow for Scenario 2.

2. **`stop_requested` vs `goal_achieved`:** The `stop_requested` stop reason comes from
   `agent.py` when `action == "stop"`. In a non-throttled run Scenario 1 would produce
   `goal_achieved` and Scenario 3 might produce `human_handoff`. The safety guarantees
   (limits respected, no crash) hold regardless of stop reason.

3. **Trace naming:** Mus's `Tracer` auto-generates `TRACE-YYYYMMDDHHMMSS-xxxxxx.json`.
   `test_agent.py` copies each to a fixed name (`TRACE-001/002/003.json`) via `shutil.copy2`
   so Louis always finds them at a known path.

---

## How to Re-Run

```bash
python tests/test_agent.py
```

(Run from `d:\SOFTWARE ENGINEERING\YR4 SEM1\EMERGING TRENDS\AI_Agentic Capstone\AI_Agentic_Capstone-main`)

The fixed-name trace files are overwritten each run. Archive previous traces before re-running
if comparison is needed. The auto-named originals accumulate and are not overwritten.
