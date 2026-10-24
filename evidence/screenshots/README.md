# System Verification Screenshots Manifest Ledger

This folder archives the 10 immutable image files demonstrating the end-to-end security, performance, and memory compliance parameters of the agent system.

| #      | Filename                    | System Behavior Verified        | Visible Interface Properties                                                                            |
| :----- | :-------------------------- | :------------------------------ | :------------------------------------------------------------------------------------------------------ |
| **1**  | `01-rag-answer.png`         | RAG Pipeline Document Ingestion | Agent answers "When is registration deadline?" with precise source citation blocks.                     |
| **2**  | `02-tool-call.png`          | Tool Routing Verification       | Model cleanly isolates variables and calls `get_course_info` for BSE4104.                               |
| **3**  | `03-approval-prompt.png`    | Human-in-the-Loop Control       | Terminal runtime engine stops and prompts for manual developer confirmation before finalizing a ticket. |
| **4**  | `04-ticket-created.png`     | Persistent Database Injection   | UI prints confirmation code verifying successful ticket storage (`TICKET-0001`).                        |
| **5**  | `05-memory-retrieval.png`   | Cross-Session Memory Usage      | Agent automatically recalls and prints the details of a previous ticket upon user return.               |
| **6**  | `06-injection-refused.png`  | Prompt-Injection Defense        | System blocks an adversarial command string and responds using safe fallback dialogue templates.        |
| **7**  | `07-prohibited-refused.png` | Boundary Enforcement            | System rejects an unauthorized user instruction demanding an administrative grade modification.         |
| **8**  | `08-trace-file.png`         | Observability Verification      | Open view of a structured JSON execution trace showing clear planning logs.                             |
| **9**  | `09-evaluation-results.png` | Programmatic Benchmarking       | Summary dashboard detailing success data across all 34 evaluation scenarios.                            |
| **10** | `10-clickup-board.png`      | Project Management Clearance    | Snapshot of the team ClickUp board displaying all 143 project cards flipped to **Done**.                |
