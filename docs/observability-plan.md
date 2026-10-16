# Observability Plan — University Student-Support Case Agent

## Six logging layers
| # | Layer | Captures |
|---|---|---|
| 1 | Model Calls | model, prompt/response preview, tokens, latency, success |
| 2 | RAG Retrievals | query preview, result count, sources, latency, success |
| 3 | Tool Calls | tool, sanitised arguments, success, result preview, latency |
| 4 | Approvals | tool, arguments, decision, mode |
| 5 | Agent Iterations | iteration, action (sense/plan/act/observe), data preview |
| 6 | Guardrail Events | guardrail name, input preview, reason, decision |

## Storage
- Format: JSON Lines (one event per line, valid JSON).
- Location: `logs/<session_id>.log`, one file per session.
- Summary: `logs/<session_id>_summary.json`.
- Traces: `evidence/traces/<scenario_id>.json`.

## Retention and access
- Retention target: 30 days (aligned with memory policy). Enforced by deployment
  cron / logrotate — documented here, not implemented in application code.
- Access: team-only. Logs are not committed to git; the `logs/` directory is
  git-ignored. Nothing containing credentials or full student records is
  written to disk.

## Redaction rules
The logger redacts these keys recursively at any depth:
`password, passwd, pwd, api_key, apikey, token, access_token, refresh_token,
secret, client_secret, private_key, authorization, auth, credential, credentials,
session_key, student_record`.
All preview strings are truncated. Full student names are not logged.

## Views
- Live debug console during development.
- Post-run trace JSON per scenario.
- Week 7 evaluation dashboard (aggregate metrics + failure catalogue).