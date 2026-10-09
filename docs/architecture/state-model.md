┌──────────────────────────────────────────────────────────────────┐
│ SESSION STATE │
│ (in-memory, lives for one conversation) │
│ session_id • user_id • current_case • preferences │
└────────────────────────┬─────────────────────────────────────────┘
│ passed to agent
▼
┌──────────────────────────────────────────────────────────────────┐
│ WORKFLOW STATE │
│ (in-memory, lives for one agent run) │
│ goal • iteration • history • tool_results │
└────────────────────────┬─────────────────────────────────────────┘
│ reads / writes
▼
┌──────────────────────────────────────────────────────────────────┐
│ PERSISTENT MEMORY │
│ (SQLite, lives across sessions) │
│ sessions table • case_history table • preferences table │
└──────────────────────────────────────────────────────────────────┘
