# MCP Interface Usage Guide

**Project:** University Student-Support Case Agent  
**Version:** 1.0  
**Date:** 8th October 2026  
**Author:** Noah (DevOps/Documentation Lead)

---

## Overview

The `StudentSupportInterface` exposes 4 capabilities through a clean, versioned interface. This guide covers how to invoke capabilities, handle responses, and integrate the interface into external systems.

---

## For Developers — Direct Python Invocation

### Setup

```python
import sys
sys.path.insert(0, 'src')   # run from project root

from interfaces.mcp_interface import StudentSupportInterface

interface = StudentSupportInterface()
```

### List available capabilities

```python
caps = interface.list_capabilities()
print(caps['version'])                # '1.0'
print(list(caps['capabilities'].keys()))
# ['query_support', 'get_course_info', 'create_ticket', 'check_ticket_status']
```

### Response format

Every `invoke()` call returns a dict with `success: bool`.

```python
# Success
{"success": True, ...data fields...}

# Failure
{"success": False, "error": "human-readable reason", "error_code": "INVALID_INPUT"}
```

Always check `success` before reading data fields:

```python
result = interface.invoke('get_course_info', {'course_code': 'BSE4104'})
if result['success']:
    print(result['prerequisites'])
else:
    print(f"Error ({result['error_code']}): {result['error']}")
```

---

## Capability Examples

### 1. `get_course_info`

```python
result = interface.invoke('get_course_info', {
    'course_code': 'BSE4104',
    'info_type': 'prerequisites'
})

# Success response
# {
#   "success": True,
#   "course_code": "BSE4104",
#   "course_name": "Emerging Trends in Software Engineering",
#   "prerequisites": ["BSE3101", "BSE3102", "CS103"],
#   "credits": 4
# }
```

**Required inputs:** `course_code`  
**Optional inputs:** `info_type` (default `"all"`)  
**Permissions:** Public  
**Rate limit:** 20/min

---

### 2. `query_support`

```python
result = interface.invoke('query_support', {
    'query': 'What are the prerequisites for BSE4104?',
    'session_id': 'SES-a1b2c3d4'
}, session_id='SES-a1b2c3d4')

# Success response
# {
#   "success": True,
#   "response": "BSE4104 requires BSE3101, BSE3102, and CS103...",
#   "sources": ["courses.json"],
#   "iterations": 2,
#   "stop_reason": "goal_achieved"
# }
```

**Required inputs:** `query`  
**Optional inputs:** `session_id`  
**Permissions:** Public  
**Rate limit:** 10/min  
**Note:** Invokes the full RAG agent loop — slower than `get_course_info`

---

### 3. `create_ticket`

```python
result = interface.invoke('create_ticket', {
    'student_name': 'Alice Nakawesa',
    'student_id': '2024/BCS/042',
    'issue_summary': 'Cannot log in to the registration portal',
    'priority': 'high',
    'category': 'registration'
})

# Success response
# {
#   "success": True,
#   "ticket_id": "TICKET-0001",
#   "status": "open",
#   "created_at": "2026-10-08T10:00:00Z"
# }

# Approval denied response
# {
#   "success": False,
#   "error": "Ticket creation was not approved",
#   "error_code": "UNAUTHORIZED"
# }
```

**Required inputs:** `student_name`, `issue_summary`  
**Optional inputs:** `student_id`, `priority`, `category`  
**Permissions:** Requires approval (routes through `ApprovalController`)  
**Rate limit:** 5/session

---

### 4. `check_ticket_status` *(New in Week 6)*

```python
result = interface.invoke('check_ticket_status', {
    'ticket_id': 'TICKET-0001'
})

# Success response
# {
#   "success": True,
#   "ticket_id": "TICKET-0001",
#   "status": "open",
#   "issue_summary": "Cannot log in to the registration portal",
#   "priority": "high",
#   "category": "registration",
#   "created_at": "2026-10-08T10:00:00Z",
#   "updated_at": "2026-10-08T10:00:00Z"
# }

# Not found response
# {
#   "success": False,
#   "error": "Ticket 'TICKET-0001' was not found",
#   "error_code": "NOT_FOUND"
# }
```

**Required inputs:** `ticket_id`  
**Permissions:** Session (ticket must exist in memory database)  
**Rate limit:** 10/min

---

## Error Handling

```python
def call_interface(capability, inputs):
    result = interface.invoke(capability, inputs)

    if not result['success']:
        code = result.get('error_code', 'UNKNOWN')
        msg  = result.get('error', 'No message')

        if code == 'INVALID_INPUT':
            print(f"Bad input: {msg}")
        elif code == 'NOT_FOUND':
            print(f"Resource not found: {msg}")
        elif code == 'UNAUTHORIZED':
            print(f"Not authorised: {msg}")
        elif code == 'RATE_LIMITED':
            print(f"Slow down: {msg}")
        elif code == 'INTERNAL_ERROR':
            print(f"Server error: {msg}")
        else:
            print(f"Unknown error ({code}): {msg}")

        return None

    return result
```

| Error code | Meaning | Action |
|---|---|---|
| `INVALID_INPUT` | Missing or invalid parameter | Fix the input and retry |
| `NOT_FOUND` | Resource doesn't exist | Check the ID / code |
| `UNAUTHORIZED` | Approval denied or session mismatch | Request human approval |
| `RATE_LIMITED` | Too many requests | Back off and retry |
| `INTERNAL_ERROR` | Unexpected failure | Log and escalate |

---

## For External Systems

### REST API wrapper (Flask)

```python
from flask import Flask, request, jsonify
from interfaces.mcp_interface import StudentSupportInterface

app = Flask(__name__)
interface = StudentSupportInterface()

@app.route('/api/v1/invoke', methods=['POST'])
def invoke():
    body       = request.get_json()
    capability = body.get('capability')
    inputs     = body.get('inputs', {})
    session_id = body.get('session_id')

    if not capability:
        return jsonify({"success": False, "error": "'capability' is required",
                        "error_code": "INVALID_INPUT"}), 400

    result = interface.invoke(capability, inputs, session_id=session_id)
    status = 200 if result['success'] else _error_code_to_http(result.get('error_code'))
    return jsonify(result), status

def _error_code_to_http(code):
    return {'INVALID_INPUT': 400, 'NOT_FOUND': 404,
            'UNAUTHORIZED': 401, 'RATE_LIMITED': 429}.get(code, 500)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**Example request:**

```bash
curl -X POST http://localhost:5000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "get_course_info",
    "inputs": {"course_code": "BSE4104", "info_type": "prerequisites"}
  }'
```

---

### CLI wrapper

```python
#!/usr/bin/env python3
"""cli_interface.py — invoke any capability from the command line"""
import json, sys
sys.path.insert(0, 'src')

from interfaces.mcp_interface import StudentSupportInterface

def main():
    if len(sys.argv) < 3:
        print("Usage: python cli_interface.py <capability> '<json_inputs>'")
        sys.exit(1)

    capability = sys.argv[1]
    inputs     = json.loads(sys.argv[2])

    interface = StudentSupportInterface()
    result    = interface.invoke(capability, inputs)

    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
```

```bash
python cli_interface.py get_course_info '{"course_code": "BSE4104"}'
python cli_interface.py check_ticket_status '{"ticket_id": "TICKET-0001"}'
```

---

## Security Layers

### Authentication (future)
Current Week 6 implementation is local-only. For production deployment:
- Add JWT token validation on each request
- Restrict `create_ticket` to authenticated sessions
- Restrict `check_ticket_status` to the ticket's owning student

### Authorisation
- `query_support` and `get_course_info`: Public — no auth needed
- `create_ticket`: Routes through `ApprovalController` (human-in-the-loop)
- `check_ticket_status`: Session-based — only the creating student's session

### Rate Limiting
Implement per-IP rate limiting in the REST wrapper:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, app=app, default_limits=["200/day"])

@app.route('/api/v1/invoke', methods=['POST'])
@limiter.limit("10/minute")
def invoke():
    ...
```

Per-capability limits (from the spec):

| Capability | Rate Limit |
|---|---|
| `query_support` | 10/min |
| `get_course_info` | 20/min |
| `create_ticket` | 5/session |
| `check_ticket_status` | 10/min |

### Audit Logging
Log every invocation (capability name, timestamp, success/fail) without logging PII:

```python
import logging
log = logging.getLogger('mcp_interface')

# GOOD — logs capability and outcome only
log.info("invoke capability=%s success=%s error_code=%s",
         capability, result['success'], result.get('error_code'))

# BAD — never log ticket content or student names
# log.info("inputs=%s", inputs)   ← DO NOT DO THIS
```

### Input Validation
All capabilities validate required fields and return `INVALID_INPUT` before any tool or agent call:
- Required fields checked before execution
- String lengths bounded (issue_summary ≤ 500 chars, query ≤ 1000 chars)
- Enum fields validated against allowed values

---

## Running the Tests

```bash
# From project root
python tests/test_mcp_interface.py
```

Expected output: 7 tests, all passing.

---

**Document Version:** 1.0  
**Owner:** Noah (DevOps/Documentation Lead)
