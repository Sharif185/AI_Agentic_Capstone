# MCP-Style Interface Specification

**Project:** University Student-Support Case Agent  
**Version:** 1.0  
**Date:** 5th October 2026  
**Author:** Noah (DevOps/Documentation Lead)

---

## Overview

The agent exposes a **Model Context Protocol (MCP)-style interface** as a clean, documented contract between the agent's capabilities and any external system or internal component that wants to invoke them.

This interface documents **4 capabilities**, each with:
- Input/output JSON schemas
- Permissions and authorization requirements
- Rate limits
- Security boundaries
- Error codes

**Interface class:** `src/interfaces/mcp_interface.py`  
**Interface version:** `1.0`

---

## Capabilities Summary

| Capability | Purpose | Permissions | Rate Limit |
|------------|---------|-------------|------------|
| `query_support` | Answer student queries using RAG | Public | 10/min |
| `get_course_info` | Retrieve structured course information | Public | 20/min |
| `create_ticket` | Create a support ticket | Requires approval | 5/session |
| `check_ticket_status` | Retrieve existing ticket status (**NEW Week 6**) | Session | 10/min |

---

## Capability 1: `query_support`

### Purpose
Answer general student support questions using RAG (retrieval-augmented generation) over university documents.

### Permissions
**Public** — no authentication required. Any student can query.

### Rate Limit
**10 requests/minute** per source IP. Prevents abuse of the LLM endpoint.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "The student's natural language question",
      "minLength": 1,
      "maxLength": 1000
    },
    "session_id": {
      "type": "string",
      "description": "Optional session identifier for conversation continuity",
      "pattern": "^SES-[a-f0-9]{8}$"
    }
  },
  "required": ["query"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the query was processed"
    },
    "response": {
      "type": "string",
      "description": "The agent's answer to the student's question"
    },
    "sources": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Source documents used to generate the response"
    },
    "iterations": {
      "type": "integer",
      "description": "Number of agent iterations taken"
    },
    "stop_reason": {
      "type": "string",
      "description": "Why the agent stopped: goal_achieved, stop_requested, max_iterations_reached"
    }
  },
  "required": ["success", "response"]
}
```

### Example Request

```json
{
  "query": "What are the prerequisites for BSE4104?",
  "session_id": "SES-a1b2c3d4"
}
```

### Example Response

```json
{
  "success": true,
  "response": "BSE4104 requires: BSE3101, BSE3102, and CS103. It is a 4-credit course offered in Semester One, Year 4.",
  "sources": ["courses.json"],
  "iterations": 2,
  "stop_reason": "goal_achieved"
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| `INVALID_INPUT` | Query is empty or exceeds max length |
| `RATE_LIMITED` | Too many requests (10/min exceeded) |
| `INTERNAL_ERROR` | RAG pipeline or model failure |

---

## Capability 2: `get_course_info`

### Purpose
Retrieve structured course information (prerequisites, credits, schedule, description) for a specific course code.

### Permissions
**Public** — no authentication required. Fast, direct lookup.

### Rate Limit
**20 requests/minute** — higher than `query_support` because it's a fast database lookup, not an LLM call.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "course_code": {
      "type": "string",
      "description": "University course code, e.g. 'BSE4104'",
      "pattern": "^[A-Z]{2,4}[0-9]{3,4}$"
    },
    "info_type": {
      "type": "string",
      "enum": ["prerequisites", "credits", "schedule", "description", "all"],
      "description": "Which type of information to retrieve. Use 'all' for complete record.",
      "default": "all"
    }
  },
  "required": ["course_code"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "course_code": {
      "type": "string"
    },
    "course_name": {
      "type": "string"
    },
    "prerequisites": {
      "type": "array",
      "items": {"type": "string"}
    },
    "credits": {
      "type": "integer"
    },
    "schedule": {
      "type": "string"
    },
    "description": {
      "type": "string"
    }
  },
  "required": ["success", "course_code"]
}
```

### Example Request

```json
{
  "course_code": "BSE4104",
  "info_type": "prerequisites"
}
```

### Example Response

```json
{
  "success": true,
  "course_code": "BSE4104",
  "course_name": "Emerging Trends in Software Engineering",
  "prerequisites": ["BSE3101", "BSE3102", "CS103"],
  "credits": 4
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| `INVALID_INPUT` | Missing course_code, invalid format, or unknown info_type |
| `NOT_FOUND` | Course code not found in the course database |
| `RATE_LIMITED` | Too many requests (20/min exceeded) |
| `INTERNAL_ERROR` | Database read failure |

---

## Capability 3: `create_ticket`

### Purpose
Create a support ticket for a student issue that cannot be resolved through available information. Requires human approval before creation.

### Permissions
**Requires Approval** — the agent's `ApprovalController` must approve this write action before the ticket is created. Not fully open to public automation.

### Rate Limit
**5 tickets/session** — prevents spam ticket creation in a single session.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "student_name": {
      "type": "string",
      "description": "Full name of the student",
      "minLength": 1,
      "maxLength": 100
    },
    "student_id": {
      "type": "string",
      "description": "University student ID, e.g. '2024/BCS/001'",
      "maxLength": 50
    },
    "issue_summary": {
      "type": "string",
      "description": "Concise description of the student's issue (max 500 chars)",
      "minLength": 1,
      "maxLength": 500
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high"],
      "default": "medium"
    },
    "category": {
      "type": "string",
      "enum": ["registration", "exams", "fees", "academic", "other"],
      "default": "other"
    },
    "session_id": {
      "type": "string",
      "description": "Session ID to link to persistent memory"
    }
  },
  "required": ["student_name", "issue_summary"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "ticket_id": {
      "type": "string",
      "description": "Unique ticket identifier, e.g. 'TICKET-0001'"
    },
    "status": {
      "type": "string",
      "enum": ["open"]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "message": {
      "type": "string",
      "description": "Confirmation message for the student"
    }
  },
  "required": ["success"]
}
```

### Example Request

```json
{
  "student_name": "Alice Nakawesa",
  "student_id": "2024/BCS/042",
  "issue_summary": "Cannot access the online registration portal — login page gives 404 error.",
  "priority": "high",
  "category": "registration"
}
```

### Example Response

```json
{
  "success": true,
  "ticket_id": "TICKET-0001",
  "status": "open",
  "created_at": "2026-10-08T10:00:00Z",
  "message": "Ticket TICKET-0001 created. A staff member will follow up within 24 hours."
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| `INVALID_INPUT` | Missing student_name or issue_summary, or fields too long/invalid |
| `UNAUTHORIZED` | Approval was denied (ApprovalController returned False) |
| `RATE_LIMITED` | 5 tickets/session limit reached |
| `INTERNAL_ERROR` | Storage write failure |

---

## Capability 4: `check_ticket_status` *(NEW — Week 6)*

### Purpose
Retrieve the current status and details of a previously created support ticket. This is a read-only operation enabled by the new persistent memory layer.

### Permissions
**Session** — the ticket must have been created in the same session or by the same student (`user_id` match). No approval needed (read-only).

### Rate Limit
**10 requests/minute** per session — reasonable for status checks.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "ticket_id": {
      "type": "string",
      "description": "The ticket ID to look up, e.g. 'TICKET-0001'",
      "pattern": "^TICKET-[0-9]{4}$"
    },
    "session_id": {
      "type": "string",
      "description": "Optional session ID for authorization context"
    }
  },
  "required": ["ticket_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "ticket_id": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": ["open", "closed"]
    },
    "issue_summary": {
      "type": "string"
    },
    "priority": {
      "type": "string"
    },
    "category": {
      "type": "string"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["success"]
}
```

### Example Request

```json
{
  "ticket_id": "TICKET-0001",
  "session_id": "SES-a1b2c3d4"
}
```

### Example Response

```json
{
  "success": true,
  "ticket_id": "TICKET-0001",
  "status": "open",
  "issue_summary": "Cannot access the online registration portal — login page gives 404 error.",
  "priority": "high",
  "category": "registration",
  "created_at": "2026-10-08T10:00:00Z",
  "updated_at": "2026-10-08T10:00:00Z"
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| `INVALID_INPUT` | Missing ticket_id or invalid format |
| `NOT_FOUND` | Ticket ID does not exist in the database |
| `UNAUTHORIZED` | Ticket belongs to a different student (future: session-based auth) |
| `INTERNAL_ERROR` | Database read failure |

---

## Security Boundaries Summary

| Capability | Data Written | Data Read | Network | Auth Required |
|------------|-------------|-----------|---------|---------------|
| `query_support` | None | RAG documents | LLM API call | None |
| `get_course_info` | None | Course database (local) | None | None |
| `create_ticket` | Ticket to DB + memory | None | None | Approval gate |
| `check_ticket_status` | None | Ticket from memory DB | None | Session match |

### Key Security Principles

1. **Write operations require approval:** `create_ticket` is the only write operation and it routes through `ApprovalController` before execution
2. **Read operations are fast and safe:** `get_course_info` and `check_ticket_status` never write; no approval needed
3. **No cross-student data access:** `check_ticket_status` returns tickets by ID; future auth will enforce ownership
4. **No PII in logs:** Logs record capability name, timestamp, success/fail — never ticket content
5. **Rate limits on all capabilities:** Prevents both abuse and accidental loops from the agent itself
6. **LLM only invoked for `query_support`:** Other capabilities use structured tools — no LLM, no hallucination risk

---

## Error Code Reference

| Code | HTTP Equivalent | Meaning |
|------|----------------|---------|
| `INVALID_INPUT` | 400 Bad Request | Required field missing or invalid |
| `NOT_FOUND` | 404 Not Found | Resource doesn't exist (course, ticket) |
| `UNAUTHORIZED` | 401 Unauthorized | Approval denied or session mismatch |
| `RATE_LIMITED` | 429 Too Many Requests | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 Internal Server Error | Unexpected failure (storage, model) |

---

## Compliance Section

### Data Minimization
- `query_support`: Passes query string to RAG, receives answer — no student PII required or stored
- `get_course_info`: Course code only — no student data involved
- `create_ticket`: Stores only what the student explicitly provides (name, ID, issue)
- `check_ticket_status`: Reads existing ticket by ID — no new data collected

### No PII in Logs
All interface logs record:
- Capability invoked
- Timestamp
- Success/failure flag
- Error code (if failed)

Logs do **NOT** record:
- Student names or IDs
- Issue summaries or ticket content
- Query text (to avoid accidental PII logging)

### Consent for Ticket Storage
When `create_ticket` succeeds, the response message informs the student that their data is stored:
> "Ticket TICKET-0001 created. A staff member will follow up within 24 hours. Your issue has been saved and will be kept for 90 days."

Students can request deletion via the agent at any time.

### Retention Policy
- Ticket data follows `docs/memory-design.md`: 90 days (open), 1 year (closed)
- Interface does not override retention policy

---

## Invocation Example

```python
from src.interfaces.mcp_interface import StudentSupportInterface

interface = StudentSupportInterface()

# List capabilities
caps = interface.list_capabilities()
print(caps['version'])  # '1.0'
print(list(caps['capabilities'].keys()))  # ['query_support', 'get_course_info', ...]

# Get course info
result = interface.invoke('get_course_info', {
    'course_code': 'BSE4104',
    'info_type': 'prerequisites'
})
if result['success']:
    print(result['prerequisites'])  # ['BSE3101', 'BSE3102', 'CS103']
else:
    print(f"Error ({result['error_code']}): {result['error']}")

# Check ticket status
status = interface.invoke('check_ticket_status', {
    'ticket_id': 'TICKET-0001'
})
if status['success']:
    print(f"Ticket is: {status['status']}")  # open
else:
    print(f"Error: {status['error']}")  # Ticket not found
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 5 Oct 2026 | Initial spec — 4 capabilities, full schemas, security boundaries |

---

**Document Version:** 1.0  
**Owner:** Noah (DevOps/Documentation Lead)  
**Next Review:** Week 7 (after evaluation)
