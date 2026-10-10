# Week 5 Progress Report

**Group:** BSE4104 Capstone Team  
**Project:** University Student-Support Case Agent  
**Week Ending:** 2nd October 2026

---

## 1. Work Completed Against Objectives

| Objective                                   |  Status   | Evidence                                                  |
| :------------------------------------------ | :-------: | :-------------------------------------------------------- |
| Define multi-step task contract             | completed | `docs/agent-task-contract.md`                             |
| Design Sense→Plan→Act→Observe→Evaluate loop | completed | `docs/architecture/agent-architecture.md`                 |
| Set max iteration caps                      | completed | `max_iterations = 5` in `src/agent/stop_conditions.py`    |
| Enforce tool allow-list                     | completed | 3 allowed tools (`CourseTool`, `TicketTool`, `RAGSearch`) |
| Implement execution stop conditions         | completed | 5 distinct conditions verified in code                    |
| Add human hand-off & approval gate          | completed | `ApprovalController` for ticket writes                    |
| Implement agent workflow loop               | completed | `src/agent/agent.py`                                      |
| Capture 3 execution traces                  | completed | `evidence/traces/TRACE-*.json`                            |
| Create Agent Architecture Diagram           | completed | `docs/architecture/agent-architecture.png`                |
| Provide working bounded agent CLI           | completed | Executable via `python src/run_agent.py`                  |

---

## 2. Key Engineering Decisions

- **Iteration Bounding (Max 5):** Fixed maximum pass count per query to prevent runaway processing and API consumption.
- **Tool Call Capping:** Capped tool usage at 3 calls and RAG usage at 2 searches per session.
- **Structured Planning via JSON:** Enforced strict JSON response formatting for `planner.py` to allow easy validation and execution parsing.
- **No-Progress Detection:** Added continuous state hashing to detect identical tool invocations or repeating plans and halt immediately.
- **Auditing via Tracer:** Built `Tracer` class to save complete session state transitions to `evidence/traces/` for evaluation.

---

## 3. Failures & Challenges

| Challenge                                        | Response / Fix                                                          | Status |
| :----------------------------------------------- | :---------------------------------------------------------------------- | :----: |
| **Planner returned non-JSON text**               | Added a clean JSON extractor and fallback `stop` action                 | Fixed  |
| **Agent looped continuously on vague input**     | Integrated state hashing to detect no-progress loops                    | Fixed  |
| **Tool execution errors crashed the agent loop** | Wrapped `_execute_tool` in `try/except` and passed errors back to model | Fixed  |
| **Traces failed to save directory**              | Updated `Tracer.save()` to auto-create missing target directories       | Fixed  |

---

### Task Tracking

- **ClickUp Status:** 20 / 20 Tasks Completed (100%)
- **Release Tag:** `week5-complete`

---

## 5. Individual Contributions

| Member     | Tasks Owned                                           | Output / Evidence                                                                                      |
| :--------- | :---------------------------------------------------- | :----------------------------------------------------------------------------------------------------- |
| **Sharif** | Agent Task Contract, team coordination                | `docs/agent-task-contract.md`                                                                          |
| **Mus**    | Agent loop, state engine, tracer, runner script       | `src/agent/`, `src/run_agent.py`                                                                       |
| **Louis**  | System architecture, planner, system prompt v4.0      | `docs/architecture/`, `src/agent/planner.py`                                                           |
| **Imaan**  | Test scenarios, execution traces generation           | `tests/test_agent.py`, `evidence/traces/`                                                              |
| **Noah**   | Architecture diagram, agent glossary, progress report | `docs/architecture/agent-architecture.png`, `docs/agent-glossary.md`, `weekly-reports/week5-report.md` |

---

## 6. Plan for Week 6: Explicit Memory & Integration

- **Explicit Session Memory:** Model user context, preferences, and interaction history explicitly.
- **Persistent Storage Use Case:** Implement a persistent memory store for tracking unresolved cases across sessions.
- **Memory Governance Documentation:** Document data privacy, retention policies, and user access/deletion rights.
- **External Integration / MCP:** Prototype an Model Context Protocol (MCP) compatible connector or external API integration.

---

## 7. Risks & Mitigations

| Risk                                    | Impact | Mitigation Strategy                                                    |
| :-------------------------------------- | :----- | :--------------------------------------------------------------------- | --- |
| **Edge-case agent looping**             | Medium | Continuous tuning of no-progress thresholds in `stop_conditions.py`    |
| **Sensitive data in persistent memory** | High   | Draft explicit privacy guidelines and anonymization filters for Week 6 |
| **Increased token consumption**         | Low    | Standardize agent execution calls on `gpt-4o-mini`                     | v   |
