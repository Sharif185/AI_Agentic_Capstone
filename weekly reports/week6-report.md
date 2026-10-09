# Week 6 Progress Report: Memory, State, and Interoperability

## 1. Project Objectives & Status

| Objective                        | Status | Evidence                        |
| :------------------------------- | :----- | :------------------------------ |
| Model workflow/session state     | Passed | docs/state-model.md             |
| Implement persistent memory      | Passed | src/memory/persistent_memory.py |
| Document data handling           | Passed | docs/memory-design.md           |
| Demonstrate memory improves task | Passed | evidence/week6-memory-demo.txt  |
| Implement MCP-style interface    | Passed | src/interfaces/mcp_interface.py |

## 2. Key Engineering Decisions

1. **Justified Memory Boundaries:** Restricted persistent memory solely to "Case History" (Ticket ID, student info, timestamps, and issue summaries) to ensure data minimization.
2. **Persistence Layer Engine:** Implemented a lightweight, local SQLite database (`data/memory.db`) to ensure ultra-low latency without adding external cloud infrastructure dependencies.
3. **Retention & Privacy Constraints:** Enforced a strict 30-day purge cycle for session lifespans and a 1-year archival boundary for closed support tickets.
4. **Assistive-Only Guardrails:** Isolated agent memory from backend administrative tasks; memory can never control or alter grades, tuition fees, or admissions criteria.
5. **Standardized Protocol Interoperability:** Created a strict 4-capability MCP-style interface layout utilizing strict JSON schemas, permission scopes, and specific rate limits.

## 3. Engineering Challenges & Mitigations

| Challenge                  | Technical Mitigation                                                                                           | Status |
| :------------------------- | :------------------------------------------------------------------------------------------------------------- | :----- |
| **Session ID Collision**   | Replaced sequential counters with a custom UUID hex token prefix (`SES-xxxxxxxx`).                             | Fixed  |
| **State Leakage in Tests** | Isolated automated testing execution paths to separate memory databases, running setup/teardown cleanups.      | Fixed  |
| **Context Window Bloat**   | Implemented a strict context truncation rule limit, injecting a maximum of 3 historical student tickets.       | Fixed  |
| **Test Approval Blocks**   | Integrated an internal `auto_approve` flag within mock environments to cleanly test ticket creation workflows. | Fixed  |

## 4. Individual Contributions

| Team Member | Role                           | Key Focus & Deliverables                                                                          |
| :---------- | :----------------------------- | :------------------------------------------------------------------------------------------------ |
| **Sharif**  | Project / Requirements Lead    | Drafted Memory Design Note, handled scope coordination, and conducted final sign-offs.            |
| **Mus**     | Application / Integration Lead | Developed Session State logic, CRUD engine in SQLite, and verified multi-session runtime scripts. |
| **Louis**   | AI Engineering Lead            | Developed System Prompts (v4.0/v4.1), ticket tracking tool integration, and MCP unit tests.       |
| **Imaan**   | Quality / Security Lead        | Designed 20 memory test assertions, verified retention/privacy, and compiled metrics.             |
| **Noah**    | DevOps / Documentation Lead    | Built the MCP interface wrapper, wrote spec & usage guides, and designed architecture diagrams.   |
