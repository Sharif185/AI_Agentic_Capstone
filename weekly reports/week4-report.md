# Week 4 Progress Report

**Group:** BSE4104 Capstone Team | **Project:** University Student-Support Case Agent | **Week Ending:** 25th September 2026

## Work Completed Against Objectives

| Objective                       |  Status   | Evidence                                       |
| :------------------------------ | :-------: | :--------------------------------------------- |
| Define 2+ tools with schemas    | completed | `docs/tool-catalogue.md`                       |
| Implement tool/function calling | completed | `src/orchestration/`                           |
| Tool 1: Retrieve current data   | completed | `src/tools/course_tool.py`                     |
| Tool 2: Low-risk side effect    | completed | `src/tools/ticket_tool.py`                     |
| Test missing parameters         | completed | `tests/week4-tool-results.md`                  |
| Test unauthorized requests      | completed | Approval tests pass                            |
| Test unavailable services       | completed | Error handling verified                        |
| Test unexpected responses       | completed | Recovery test passes                           |
| Add human approval              | completed | `src/orchestration/approval_controller.py`     |
| Update architecture diagram     | completed | `docs/architecture/updated-architecture-v3.md` |

## Key Engineering Decisions

- **Two tools only:** `get_course_info` (read-only) and `create_support_ticket` (write)
- **Approval gate for writes:** Human confirmation mandatory for `create_support_ticket`
- **SQLite storage:** Simple, local persistence for tickets without external database overhead
- **JSON for course data:** Easy maintenance for static read-only course info
- **Single tool call per turn:** Bounded agency constraint prior to Week 5 agentic loops
- **Explicit schema validation:** JSON validation prior to tool execution
- **Graceful error recovery:** Model handles tool failures naturally

## Failures & Challenges

| Challenge                             | Response                                                              |  Status  |
| :------------------------------------ | :-------------------------------------------------------------------- | :------: |
| Model called tool when not needed     | Added "when to use tools" rules to Prompt v3.0                        |  Fixed   |
| Approval prompt interrupted test flow | Added `auto_approve` flag to `ApprovalController` for automated tests | Resolved |
| Ticket DB path missing on boot        | Auto-created `data/` directory during storage initialization          |  Fixed   |

## Risks & Mitigations

| Risk                          | Mitigation                           |
| :---------------------------- | :----------------------------------- |
| **Agent may loop infinitely** | Max iterations = 5, hard stop        |
| **Tool misuse**               | Allow-list only approved tools       |
| **Model chooses wrong tool**  | Test with scenarios, improve prompt  |
| **Approval fatigue**          | Only high-impact tools need approval |

## Individual Contributions

- **Sharif:** Tool Catalogue, team coordination (`docs/tool-catalogue.md`).
- **Mus:** CourseTool, TicketTool, main CLI integration (`src/tools/`, `src/main.py`).
- **Louis:** Tool orchestration, ToolExecutor, system prompt v3.0 (`src/orchestration/`, `prompts/`).
- **Imaan:** Failure tests, test runner, recovery testing (`tests/`).
- **Noah:** SQLite ticket storage, architecture diagrams, user guides, progress report (`src/tools/ticket_storage.py`, `docs/architecture/`, `weekly-reports/week4-report.md`).

## Plan for Week 5

- Design bounded agentic workflow (Sense → Plan → Act → Observe → Stop).
- Set max iterations (5), stop conditions, and tool allow-lists.
- Capture execution traces (success, failure, recovery).
