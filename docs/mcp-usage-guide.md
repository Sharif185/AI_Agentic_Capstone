# Model Context Protocol (MCP) Developer & Integration Usage Guide

This guide establishes the deployment profiles, architectural integrations, and security policies for interacting with the University Student-Support Case Agent's MCP-style interface.

---

## 1. For Developers: Direct Engine Invocation

Application developers working directly within the repository can interact with the agent via the native python interface wrapper.

### How to Invoke a Capability

Import the `StudentSupportInterface` module, instantiate the class, and pass the targeted capability token along with its required parameters via the unified `invoke()` gateway.

### Standard Response Format

All capabilities respond with a consistent dictionary payload structure:

- **Success Output:** `{"success": True, ...data}`
- **Failure Output:** `{"success": False, "error": "Clear description of error state", "error_code": "STANDARD_ERROR_TOKEN"}`

### Error Handling Standard Implementation

```python
# docs/examples/invocation_example.py
from src.interfaces.mcp_interface import StudentSupportInterface

# Initialize the interface engine
interface = StudentSupportInterface()

# Execute a target capability invocation
result = interface.invoke('get_course_info', {
    'course_code': 'BSE4104',
    'info_type': 'prerequisites'
})

# Standardized error verification pipeline
if not result['success']:
    print(f"Invocation Failed! Error ({result.get('error_code')}): {result['error']}")
else:
    print(f"Success! Retrieved Payload: {result['data']}")
```

---

## 2. For External Systems: Integration Profiles

For systems operating outside the core Python execution context, the platform exposes three primary communication abstractions.

### Profile A: REST API Web Service Wrapper (Flask)

Expose the capabilities as a standard JSON over HTTP service layer for web clients.

```python
# src/interfaces/api_server.py
from flask import Flask, request, jsonify
from src.interfaces.mcp_interface import StudentSupportInterface

app = Flask(__name__)
mcp_engine = StudentSupportInterface()

@app.route('/api/v1/mcp/invoke', methods=['POST'])
def handle_mcp_invocation():
    payload = request.get_json() or {}
    capability = payload.get('capability')
    inputs = payload.get('inputs', {})
    session_id = request.headers.get('X-Session-ID')

    if not capability:
        return jsonify({"success": False, "error": "Missing capability target", "error_code": "INVALID_INPUT"}), 400

    result = mcp_engine.invoke(capability, inputs, session_id=session_id)

    status_code = 200
    if not result['success']:
        if result['error_code'] == 'NOT_FOUND': status_code = 404
        elif result['error_code'] == 'UNAUTHORIZED': status_code = 403
        else: status_code = 400

    return jsonify(result), status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Profile B: Native MCP Server Implementation

Integrate directly into standard LLM orchestrators (like Claude Desktop) using standard inputs and outputs over standard I/O streams.

```python
# src/interfaces/mcp_server_stdio.py
import sys
import json
from src.interfaces.mcp_interface import StudentSupportInterface

def run_stdio_server():
    engine = StudentSupportInterface()

    while True:
        try:
            line = sys.stdin.readline()
            if not line: break

            request_data = json.loads(line)
            # Process incoming protocol frames
            capability = request_data.get("method")
            params = request_data.get("params", {})

            if capability == "list_capabilities":
                response = engine.list_capabilities()
            else:
                response = engine.invoke(capability, params)

            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "result": response}) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    run_stdio_server()
```

### Profile C: Command Line Interface (CLI) Tool

A shell utility enabling system administrators to quickly audit and run pipeline tasks manually.

```bash
# Example syntax using a mock terminal runner entrypoint
python src/cli.py --capability check_ticket_status --input '{"ticket_id":"TICKET-0001"}'
```

---

## 3. Security Layers & Defensive Controls

The interface wraps all underlying agent pipelines inside an explicit, multi-layered security wrapper.

### Layer 1: Authentication & Identity Assurance

- **Mechanism:** Bearer token validation and API key authentication blocks are enforced at the network edge gateway.
- **Session Integrity:** Cross-session requests require a cryptographically valid `Session-ID` header token format verified against the database.

### Layer 2: Role-Based Authorization & Scopes

- **Scope Rules:** Execution rights are mapped directly to user permissions.
- **Restrictions:** Standard student roles can access `query_support` and `check_ticket_status`. Privileged workflows like modifying parameters or system flags require explicit operational approval scopes.

### Layer 3: Rate Limiting Matrix

To prevent denial of service (DoS) and model exploitation, strict traffic limits are defined at the capability gateway layer:

- `query_support`: 10 requests per minute max.
- `get_course_info`: 20 requests per minute max.
- `create_ticket`: 5 operations per session token max.

### Layer 4: Immutable Input Validation

- **Regex Filtering:** String inputs are automatically evaluated against explicit syntax guardrails (e.g., matching a ticket parameter against strict format patterns: `^TICKET-\d{4}$`).
- **Type Safety:** Malformed types or nested parameters automatically throw an immediate `INVALID_INPUT` error, safely dropping the execution run before it passes down into memory structures.

### Layer 5: Strict Compliance and Audit Logging

- **Zero PII Logging:** The interface sanitizes runtime parameters before appending them to the persistent execution trace logs. Plain-text passwords, tokens, or financial figures are completely blocked from logging entries.
- **Audit Trail:** Every discrete gateway interaction leaves an immutable execution record detailing the target timestamp, caller identification signature, capability string, and the structural `error_code` results if applicable.
