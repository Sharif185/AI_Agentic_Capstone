# Model Context Protocol (MCP) Interface Specification

## 1. Core Capability Registry

The University Student-Support Case Agent exposes four modular capabilities through a unified gateway.

| Capability            | Purpose                                      | Permissions       | Rate Limit           |
| :-------------------- | :------------------------------------------- | :---------------- | :------------------- |
| `query_support`       | Answer student queries using RAG pipeline    | Public            | 10 requests / min    |
| `get_course_info`     | Retrieve structured course information       | Public            | 20 requests / min    |
| `create_ticket`       | Instantiate a new support ticket in the DB   | Requires Approval | 5 requests / session |
| `check_ticket_status` | Retrieve active or historical ticket details | Session Bound     | 10 requests / min    |

## 2. JSON Schemas & Data Contracts

### get_course_info

- **Input Schema:**

```json
{
  "\$schema": "http://json-schema.org",
  "type": "object",
  "properties": {
    "course_code": { "type": "string", "pattern": "^[A-Z]{3,4}\\d{4}\$" },
    "info_type": {
      "type": "string",
      "enum": ["prerequisites", "syllabus", "schedule"]
    }
  },
  "required": ["course_code", "info_type"]
}
```

- **Output Schema:**

```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "course_code": { "type": "string" },
    "data": { "type": "string" }
  },
  "required": ["success", "course_code", "data"]
}
```

### check_ticket_status (NEW)

- **Input Schema:**

```json
{
  "\$schema": "http://json-schema.org",
  "type": "object",
  "properties": {
    "ticket_id": { "type": "string", "pattern": "^TICKET-\\d{4}\$" }
  },
  "required": ["ticket_id"]
}
```

## 3. Security Boundaries & Compliance

- **Data Minimization:** No transactional logs will cache plain-text Student PII or access passwords.
- **Isolation:** Capabilities enforce session checks to ensure Student A cannot request statuses for Student B's tickets.
