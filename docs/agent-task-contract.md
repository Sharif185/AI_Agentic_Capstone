# Agent Task Contract

**Project:** University Student-Support Case Agent
**Version:** 1.0
**Date:** 28th September 2026
**Author:** Sharif (Project/Requirements Lead)
**Status:** Draft

---

## 1. Agent Identity

| Property | Value |
|----------|-------|
| Name | `StudentSupportAgent` |
| Version | 1.0 |
| Purpose | Resolve student support issues through multi-step reasoning |

---

## 2. Goal

**Primary Goal:** Help a student resolve a university support issue by:

1. Understanding the issue from the student's message
2. Searching the knowledge base (RAG) for relevant information
3. Checking structured data (course info) when applicable
4. Determining if the issue can be resolved autonomously
5. Creating a support ticket (with approval) if unresolved
6. Confirming the outcome to the student

---

## 3. Agent Loop Design

The agent follows a **Sense → Plan → Act → Observe → Evaluate** loop at each iteration:

| Phase | Description |
|-------|-------------|
| **Sense** | Parse and understand the student's message |
| **Plan** | Decide which tool to call, or whether to respond directly |
| **Act** | Execute the selected tool (one tool per iteration) |
| **Observe** | Inspect the tool result and update state |
| **Evaluate** | Check stop conditions; continue or terminate |

> See the architecture diagram (`docs/architecture/`) for the full visual representation of this loop.

---

## 4. Approved Tools

| Tool | Type | Approval Required | Purpose |
|------|------|:-----------------:|---------|
| `rag_retrieve` | Read | ❌ No | Search the knowledge base for relevant documents |
| `get_course_info` | Read | ❌ No | Look up structured course data |
| `create_support_ticket` | Write | ✅ Yes | Create a ticket for unresolved issues |

> The agent MUST NOT call any tool not listed in this table.

---

## 5. State Model

The agent maintains the following state object across all iterations:

```json
{
    "goal": "Original student message",
    "iteration": 0,
    "max_iterations": 5,
    "history": [
        {"step": 1, "action": "sense",   "context": "..."},
        {"step": 2, "action": "plan",    "decision": "..."},
        {"step": 3, "action": "act",     "tool": "...", "result": "..."},
        {"step": 4, "action": "observe", "observation": "..."}
    ],
    "retrieved_documents": [],
    "tool_results": [],
    "current_plan": null,
    "completed": false,
    "human_needed": false,
    "final_response": null,
    "stop_reason": null
}
```

---

## 6. Limits

| Limit | Value | Reason |
|-------|-------|--------|
| Max iterations | 5 | Prevents infinite loops |
| Max tool calls per iteration | 1 | Keeps steps observable and auditable |
| Max tool calls total | 3 | Ensures bounded autonomy |
| Max RAG retrievals | 2 | Avoids redundant searches |
| Timeout per iteration | 30 seconds | Prevents the agent from hanging |

---

## 7. Stop Conditions

The agent **MUST** stop when **ANY** of the following is true:

| Condition | Description |
|-----------|-------------|
| ✅ Goal achieved | A final answer has been produced for the student |
| ⏱ Max iterations reached | The agent has completed 5 iterations without resolution |
| 🤝 Human hand-off | A ticket has been created or approval has been requested |
| ❌ Unrecoverable error | A tool failure that cannot be retried or recovered from |
| 🔁 No progress | Two consecutive iterations returned no new information |

---

## 8. Human Hand-off Conditions

| Condition | Action |
|-----------|--------|
| Issue requires ticket creation | Request human approval before calling `create_support_ticket` |
| Approval denied | Stop immediately and inform the student |
| Issue is out of scope | Redirect the student to the appropriate university office |
| Sensitive topic detected | Escalate without taking any autonomous action |
| Max iterations reached without resolution | Create a ticket tagged `"needs human review"` |

---

## 9. Prohibited Actions

The agent **MUST NEVER**:

- Change or suggest changes to grades
- Access real student records
- Make admissions decisions
- Process or initiate financial transactions
- Execute any tool not listed in Section 4
- Continue past the maximum iteration limit
- Call a write tool without explicit human approval

---

## 10. Success Criteria

| Criterion | Target |
|-----------|--------|
| Correct goal identification | 90%+ |
| Appropriate tool selection | 85%+ |
| Stop conditions respected | 100% |
| Max iterations never exceeded | 100% |
| Human approval enforced for all write tools | 100% |
| Graceful failure recovery | 90%+ |

---

> **Note:** This contract must be reviewed and updated whenever the agent's tools, iteration limits, or hand-off conditions change. All revisions require sign-off from the project lead.
