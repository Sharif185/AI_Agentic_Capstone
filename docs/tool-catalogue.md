# Tool Catalogue

**Version:** 1.0  
**Date:** 21st September 2026  
**Author:** Sharif (Project Lead)  
**Status:** Draft

---

## Overview

This catalogue defines all tools available to the Student Support Agent. Each tool has a clear purpose, input schema, output schema, authorization level, and failure behaviour.

---

## Summary Table

| Tool | Type | Side Effect | Approval Required | Data Source |
|------|------|-------------|:-----------------:|-------------|
| `get_course_info` | Read | None | ❌ No | `data/courses.json` |
| `create_support_ticket` | Write | Creates ticket | ✅ Yes | `data/tickets.db` |

---

## Tool 1: `get_course_info`

**Purpose:** Retrieve structured course information (prerequisites, credits, schedule, description) from the local course database.

---

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "course_code": {
      "type": "string",
      "description": "The course code (e.g., BSE4104)"
    },
    "info_type": {
      "type": "string",
      "enum": ["prerequisites", "credits", "schedule", "description", "all"],
      "description": "Type of information needed",
      "default": "all"
    }
  },
  "required": ["course_code"]
}
```

---

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "course_code": {"type": "string"},
    "info_type": {"type": "string"},
    "data": {"type": "object"},
    "error": {"type": "string"}
  }
}
```

---

### Authorization

| Property | Value |
|----------|-------|
| Level | Public — no approval required |
| Data Source | Local JSON file (`data/courses.json`) |
| Side Effects | None (read-only) |

---

### Failure Behaviour

| Failure | Response |
|---------|----------|
| Missing `course_code` | `{"success": false, "error": "course_code is required"}` |
| Invalid `course_code` | `{"success": false, "error": "Course X not found"}` |
| Invalid `info_type` | `{"success": false, "error": "info_type must be one of: ..."}` |
| Data file missing | `{"success": false, "error": "Course database unavailable"}` |

---

### Example Call

```json
{
  "tool": "get_course_info",
  "arguments": {
    "course_code": "BSE4104",
    "info_type": "prerequisites"
  }
}
```

### Example Response

```json
{
  "success": true,
  "course_code": "BSE4104",
  "info_type": "prerequisites",
  "data": {
    "prerequisites": ["BSE3101", "BSE3102", "CS103"]
  }
}
```

---

## Tool 2: `create_support_ticket`

**Purpose:** Create a support ticket for a student whose issue cannot be resolved through RAG or course lookup.

---

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "student_name": {
      "type": "string",
      "description": "Student's full name"
    },
    "student_id": {
      "type": "string",
      "description": "Student ID number (optional)"
    },
    "issue_summary": {
      "type": "string",
      "description": "Brief description of the issue (max 500 chars)"
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
    }
  },
  "required": ["student_name", "issue_summary"]
}
```

---

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "ticket_id": {"type": "string"},
    "status": {"type": "string"},
    "message": {"type": "string"},
    "ticket": {"type": "object"},
    "error": {"type": "string"}
  }
}
```

---

### Authorization

| Property | Value |
|----------|-------|
| Level | Requires human approval |
| Data Source | Local SQLite database (`data/tickets.db`) |
| Side Effects | Creates a new ticket record |

---

### Failure Behaviour

| Failure | Response |
|---------|----------|
| Missing `student_name` | `{"success": false, "error": "student_name is required"}` |
| Missing `issue_summary` | `{"success": false, "error": "issue_summary is required"}` |
| `issue_summary` too long | `{"success": false, "error": "issue_summary exceeds 500 chars"}` |
| Invalid `priority` | `{"success": false, "error": "priority must be low/medium/high"}` |
| Approval denied | `{"success": false, "error": "Human approval denied"}` |
| Database error | `{"success": false, "error": "Ticket system unavailable"}` |

---

### Example Call

```json
{
  "tool": "create_support_ticket",
  "arguments": {
    "student_name": "John Doe",
    "student_id": "2024/BCS/001",
    "issue_summary": "Cannot access online registration portal",
    "priority": "high",
    "category": "registration"
  }
}
```

### Example Response

```json
{
  "success": true,
  "ticket_id": "TICKET-0001",
  "status": "open",
  "message": "Ticket TICKET-0001 created successfully",
  "ticket": {
    "id": "TICKET-0001",
    "student_name": "John Doe",
    "student_id": "2024/BCS/001",
    "issue_summary": "Cannot access online registration portal",
    "priority": "high",
    "category": "registration",
    "status": "open",
    "created_at": "2026-09-21T10:30:00"
  }
}
```

---

> **Note:** This catalogue should be updated whenever a new tool is added or an existing tool's schema or behaviour changes. All tool additions require sign-off from the project lead.
