# Week 4 Demo Evidence — Tools & Function Calling

**Component:** Application/Integration (Mus)
**Branch:** `Aloysious-Mutagubya`
**Tool-layer tests run:** 8 October 2026

## How to read this document

Two kinds of evidence are kept apart on purpose:

- **✅ Tool-layer (executed, real output).** `CourseTool`, `TicketTool`, `ApprovalController` and `ToolExecutor` were run directly against the repo code, independent of any model. The output below is copied from that run. The ticket-approval step used a scripted decision (`ApprovalController(decision_fn=...)`); the real CLI asks `y/n` interactively.
- **⏳ Live model run (paste from your machine).** Whether the model chooses the right tool, and what it finally says, can only be confirmed with a real Gemini call. Those cells are blank for you to fill in from `python src/main.py`. Nothing in them is invented, and nothing is marked as passed until you paste the output.

## Pre-conditions for the live run

1. `.env` has a valid key and `MODEL_NAME=gemini-3.6-flash`.
2. Dependencies installed: `python -m pip install langchain-google-genai langchain-chroma` (plus `requirements.txt`).
3. Vector store built with your Gemini-embeddings `vector_store.py`. Run from `src/` after `load_dotenv('../.env')`, then `RAGPipeline().index()`.
4. Use `prompts/system-prompt-v1.1.txt` (the default in `main.py`).
5. Run from the repo root: `python src\main.py`.

---

## Demo 1 — Successful course lookup (Scenario A)

**User input:** `What are the prerequisites for BSE4104?`

| Field | Tool-layer (✅ executed) | Live model run (⏳ paste) |
|---|---|---|
| Tool selected | `get_course_info` | |
| Arguments | `{"course_code": "BSE4104", "info_type": "prerequisites"}` | |
| Approval state | N/A, read-only (`requires_approval = False`) | |
| Tool result | `{"success": true, "course_code": "BSE4104", "info_type": "prerequisites", "data": {"prerequisites": ["BSE3101", "BSE3102", "CS103"]}}` | |
| Final response | n/a | |

- **Expected:** model calls `get_course_info`, then answers with BSE3101, BSE3102 and CS103 from the tool result.
- **Actual (tool layer):** ✅ matches. **Actual (model):** ⏳ pending.

## Demo 2 — Ticket creation with human approval (Scenario B)

**User input:** `I can't access the registration portal. Can you create a ticket?`

| Field | Tool-layer (✅ executed) | Live model run (⏳ paste) |
|---|---|---|
| Tool selected | `create_support_ticket` | |
| Arguments | `{"student_name": "Jane Nabbosa", "student_id": "2024/BCS/001", "issue_summary": "Cannot access the registration portal", "priority": "high", "category": "registration"}` | |
| Approval state | Approved (scripted decision) | (paste the `Approve this action? [y/n]` prompt and your answer) |
| Tool result | `{"success": true, "ticket": {"ticket_id": "TCK-0001", "student_name": "Jane Nabbosa", "student_id": "2024/BCS/001", "issue_summary": "Cannot access the registration portal", "priority": "high", "category": "registration", "status": "open", "created_at": "2026-10-08T08:40:34+00:00"}, "approved": true}` | |
| Final response | n/a | |

- **Expected:** the ticket exists only after approval; the ticket ID is given back to the student.
- **Actual (tool layer):** ✅ matches. **Actual (model):** ⏳ pending.

## Demo 3 — Lookup failure and graceful recovery (Scenario C)

**User input:** `What are the prerequisites for XYZ999?`

| Field | Tool-layer (✅ executed) | Live model run (⏳ paste) |
|---|---|---|
| Tool selected | `get_course_info` | |
| Arguments | `{"course_code": "XYZ999"}` | |
| Approval state | N/A | |
| Tool result | `{"success": false, "error": "No course found with code 'XYZ999'."}` | |
| Final response | n/a | |

- **Expected:** the model says the course was not found and does not invent prerequisites.
- **Actual (tool layer):** ✅ structured error returned, nothing invented. **Actual (model):** ⏳ pending.

## Demo 4 — RAG-only answer, no tool (Scenario D)

**User input:** `When is the registration deadline?`

| Field | Live model run (⏳ paste) |
|---|---|
| Tool selected | none expected |
| Retrieved sources | |
| Final response | |

- **Expected:** answer from retrieved context with a source, and no `[Tool selected]` line. If the corpus has no deadline, the model should say so rather than guess.
- **Actual:** ⏳ pending. There is no tool-layer equivalent for this demo.

---

## Test 5 — Approval denied (✅ executed)

| Check | Result |
|---|---|
| Tool result | `{"success": false, "error": "Human approval denied", "approved": false}` |
| Tickets in storage before / after | 1 / 1, so no ticket was created |

## Error-handling matrix (✅ executed, real output)

| Layer | Case | Result |
|---|---|---|
| CourseTool | Missing `course_code` | `Missing or invalid 'course_code'. A non-empty course code string is required.` |
| CourseTool | Invalid `info_type` | `Invalid 'info_type': 'syllabus'. Must be one of: prerequisites, credits, schedule, description, all.` |
| CourseTool | Lowercase code `bse4104` | Normalized and matched BSE4104 (credits: 4) |
| CourseTool | Missing `courses.json` | `Course database is unavailable (not found at ...)` |
| TicketTool | Missing `student_name` | `Missing or invalid 'student_name'. This field is required.` |
| TicketTool | Missing `issue_summary` | `Missing or invalid 'issue_summary'. This field is required.` |
| TicketTool | 501-character summary | `'issue_summary' is 501 characters, exceeding the 500-character limit.` |
| TicketTool | Priority `urgent` | `Invalid 'priority': 'urgent'. Must be one of: low, medium, high.` |
| TicketTool | Category `parking` | `Invalid 'category': 'parking'. Must be one of: registration, exams, fees, academic, other.` |
| TicketTool | Storage unwritable | `Ticket storage is unavailable (could not write ...)` |
| ToolExecutor | Unknown tool `delete_all_students` | `Unknown tool requested: 'delete_all_students'.` |
| ToolExecutor | Non-JSON arguments | `Tool 'get_course_info' received malformed (non-JSON) arguments.` |
| ToolExecutor | Extra parameter | `Tool 'get_course_info' received unexpected parameter(s): unexpected_field.` |

**Registration check:** registered tools are `create_support_ticket` and `get_course_info`. `requires_approval` is `false` for `get_course_info` and `true` for `create_support_ticket`.

**Not executed:** "more than one tool call in a turn". `main.py` handles it in code by executing only the first call and printing a notice, but this was read, not run. To test it live, ask something that could trigger two tools, e.g. `Tell me the prerequisites for BSE4104 and create a ticket about registration`, and paste the notice here:

```
(paste output)
```

## Live transcript (paste)

```
(paste the terminal session for Demos 1-4 here)
```
