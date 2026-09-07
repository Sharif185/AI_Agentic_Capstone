# AI Boundary Matrix

## Overview

This document defines the boundaries of AI involvement in the system. It specifies what the AI agent handles autonomously, what is governed by deterministic (rule-based) logic, and what requires explicit human approval before any action is taken.

---

## Boundary Matrix

| # | Action | AI Capability | Deterministic Control | Human Approval Required |
|---|--------|---------------|-----------------------|-------------------------|
| 1 | Answer FAQ | ✅ Generate from RAG | ✅ Validate against corpus | ❌ |
| 2 | Check Timetable | ✅ Interpret query | ✅ Database query | ❌ |
| 3 | Create Support Ticket | ✅ Summarize issue | ✅ Validate data, assign ID | ❌ |
| 4 | Check Case Status | ✅ Understand query | ✅ Query database | ❌ |
| 5 | Complex Issue Resolution | ❌ | ❌ | ✅ Escalate to staff |
| 6 | Enrollment Decisions | ❌ | ❌ | ✅ Staff only |
| 7 | Grade Information | ❌ | ✅ Display from system | ❌ |

---

## Legend

| Symbol | Meaning                                      |
|--------|----------------------------------------------|
| ✅     | Active — capability or control applies       |
| ❌     | Not applicable or not permitted              |

---

## Column Definitions

| Column                    | Description                                                                                         |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| AI Capability             | The agent can understand, generate, or process this request using NLP or RAG.                       |
| Deterministic Control     | The action is governed by fixed, rule-based logic (e.g., database queries, data validation).        |
| Human Approval Required   | A staff member must review and approve. The agent cannot proceed autonomously.                      |

---

## Escalation Policy

Actions marked **Human Approval Required** must be routed to the appropriate staff channel. The agent must:

1. Acknowledge the request to the user.
2. Collect relevant context or details.
3. Create an escalation record and notify the responsible staff member.
4. Inform the user of expected response timelines.

---

> **Note:** This matrix should be reviewed as new agent capabilities are introduced. Any expansion of AI autonomy into human-gated actions requires sign-off from the project lead.
