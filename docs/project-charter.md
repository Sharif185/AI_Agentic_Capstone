# PROJECT CHARTER

## University Student-Support Case Agent

**Target Institution:** Makerere University

### 1. Problem Statement

University students frequently need assistance with routine academic and administrative matters such as course requirements, registration procedures, examination timetables, university policies, and support-case status. Currently, students may need to search through scattered documents or contact departmental offices, resulting in delayed responses and repetitive workload for support staff.

Students also lack a convenient way to track issues they have reported, such as timetable clashes or examination-venue concerns. There is therefore a need for a system that can provide reliable first-line support while escalating cases that require human intervention.

### 2. Project Goal

To develop a bounded AI-powered student-support agent that provides **document-grounded answers**, retrieves the status of synthetic support cases, creates and routes support tickets for unresolved issues, and maintains the context of an active case throughout a conversation.

### 3. Target Users

* **Undergraduate students:** Seek information, report support issues, and track existing cases.
* **Academic/support staff:** Receive and manage cases requiring human intervention.
* **Department administrators:** Receive appropriately routed simulated support tickets.

### 4. AI-Native Value Proposition

The system will combine **Retrieval-Augmented Generation (RAG), agentic tool use, and conversational memory**.

The agent will:

* Retrieve and reason over approved university documents to answer questions with source attribution.
* Determine whether a query can be answered from available information or requires a case lookup or support ticket.
* Use controlled tools to retrieve case status, create tickets, and route cases.
* Remember the student's active support case during the conversation.
* Explicitly acknowledge when information is unavailable rather than generating unsupported answers.

Deterministic software will control authentication, authorization, database operations, ticket creation, routing, and permitted state changes.

### 5. Scope

**In Scope**

* Grounded Q&A using a small corpus of public Makerere University documents.
* Course and academic-procedure information retrieval.
* Synthetic student and support-case lookup.
* Support-ticket creation and routing.
* Active-case conversational memory.
* Human escalation for cases requiring institutional judgment.
* Logging of agent actions and selected failure/recovery scenarios.

**Out of Scope**

* Admissions or admission decisions.
* Grading or assessment decisions/changes.
* Disciplinary decisions.
* Fee waivers, adjustments, or financial transactions.
* Modification of official student records.
* Integration with confidential university systems such as AIMS, MUELE, or financial systems.
* Autonomous decisions affecting student rights or academic standing.

### 6. Data Strategy

The project will follow a **public and synthetic data approach**. Publicly available university handbooks, course outlines, academic guidelines, published timetables, and related materials will form the knowledge base. Student profiles, case records, ticket histories, and other personal data required for demonstrations will be synthetic and created by the project team.

No confidential or personally identifiable student information will be used without explicit authorization.

### 7. Core Agent Workflow

The primary workflow will be:

**Student Query → Intent Understanding → Document Retrieval / Case Lookup / Ticket Action → Agent Response → Active Case Memory**

For routine questions, the agent retrieves relevant documents and provides a grounded answer with sources. For personal cases, it checks the student's synthetic case record. When an issue cannot be resolved through self-service, the agent creates and routes a support ticket for human action.

### 8. Safety Boundary

The agent is limited to **informing, retrieving, logging, routing, and escalating**. It must not make admissions, grading, disciplinary, financial, or other high-impact decisions.

Actions beyond permitted low-risk operations will require human intervention. Access controls will ensure that a student can only retrieve their own synthetic case information.

### 9. Success Criteria

The system will be evaluated using at least **30 predefined scenarios** and should:

* Achieve at least **90% accuracy** on document-grounded questions.
* Provide correct source attribution for supported answers.
* Correctly state when the knowledge base does not contain sufficient information.
* Achieve at least **95% accuracy** in retrieving synthetic case status.
* Correctly create and route support tickets in at least **95%** of applicable scenarios.
* Maintain accurate active-case context during conversations.
* Demonstrate **100% compliance with defined safety boundaries** in evaluation scenarios.
* Provide inspectable logs/traces for agent actions and at least one documented failure and recovery.

### 10. Key Deliverables

By the end of the eight-week project, the team will deliver:

1. A functional web-based student-support agent.
2. A curated university-document knowledge base.
3. Synthetic student and support-case datasets.
4. Controlled agent tools for retrieval, case lookup, ticket creation, and routing.
5. Conversational active-case memory.
6. Safety and access-control mechanisms.
7. Evaluation scenarios, results, and agent execution traces.
8. Technical and project documentation.

### 11. Eight-Week Plan

| Week | Focus                                             |
| ---- | ------------------------------------------------- |
| 1    | Problem definition, requirements and architecture |
| 2    | Technology/LLM selection and initial prototype    |
| 3    | Document processing and RAG                       |
| 4    | Synthetic case database and backend services      |
| 5    | Agent workflow and tool integration               |
| 6    | Memory, ticketing and routing                     |
| 7    | Testing and evaluation                            |
| 8    | Refinement, documentation and final demonstration |

### 12. Project Principle

The project follows the principle:

> **The AI agent determines what information or tool is needed, while deterministic software enforces what the agent is permitted to do.**

This ensures that the system demonstrates meaningful agentic capabilities while remaining safe, auditable, and feasible within the eight-week capstone period.