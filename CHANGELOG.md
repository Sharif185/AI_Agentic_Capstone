# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-10-23

### Added
- Week 7 evaluation & guardrail layer:
  - 34-scenario evaluation dataset across 6 categories
    (normal, edge, incorrect info, adversarial, tool failure, unauthorized)
  - 8 measurable metrics with targets
  - Six-layer structured logger (JSON Lines + readable console)
  - Four guardrails enforced in the agent loop: input validation,
    output validation, tool allow-list, iteration limiter
  - Failure catalogue with 5 genuine failures, root causes, fixes,
    and re-test evidence
- Week 8 release preparation:
  - `scripts/full_system_test.py` — 5-suite orchestrator
  - `scripts/guardrail_acceptance.py` — 12 integration-boundary checks
  - `scripts/check_log_integrity.py` — JSON Lines and 6-layer coverage validator
  - `scripts/log_coverage.py` — emits one of each required layer for validation
  - `demo/` folder with 7 curated demo scenarios and narration script
  - `docs/week8-defect-triage.md` — complete defect log with root causes
  - `README.md`, `CHANGELOG.md` — release documentation

### Changed
- Agent loop now enforces input validation before any model/RAG/tool
  call, iteration limits at the top of every pass, and output
  validation on the final answer
- Planner logs every model call (model id, preview, latency, tokens)
- RAG pipeline logs every retrieval (query, count, sources, latency)
- Tool executor logs every attempt and every approval decision
- System prompt v5.0 — explicit injection-refusal patterns, prohibited
  action list, memory boundary restatement
- `demo/scenarios.json` — `expected_stop_reason` accepts a list of valid
  outcomes so demos reflect both ideal (`goal_achieved` with a populated
  index) and current (`stop_requested` with an empty index) behaviour

### Fixed
- `AgentLogger` module-global session registry caused `FileNotFoundError`
  when a second instance used the same `session_id` (Week 7 deliverable)
- `AgentLogger` had no `close()` method; FileHandler held a file lock on
  Windows through test teardown, causing `PermissionError`
- `src/demo_memory.py` crashed on Windows with `UnicodeEncodeError` when
  printing emoji (cp1252 default console)
- `src/demo_memory.py` called `MemoryManager.get_stats()` (never implemented)
- `src/demo_memory.py` used wrong return keys from `delete_all_data()`
- `src/demo_memory.py` called `get_ticket()` after `end_session()`
  (session-scoped method, always returned None)
- `src/demo_memory.py` lacked a `RESULT: SUCCESS` marker expected by
  `test_demo_passes`
- `src/rag/pipeline.py` had no `if __name__ == "__main__"` block —
  `python -m rag.pipeline` was a silent no-op
- `src/rag/pipeline.py` crashed with a Chroma traceback when the corpus
  was empty; now raises a clear `RuntimeError`

### Known limitations
- Task completion (0.662) and groundedness (0.676) are below Week 7
  targets. Root cause: RAG index empty for the v1.0.0 evaluation run.
  Fix scheduled for Week 9.
- RAG indexing at the free-tier Gemini embedding rate limit takes ~6
  hours for the full corpus (235 batches × 90s pause). Mitigations
  under consideration: larger chunk size, larger batch size, paid tier.
- Output validator uses heuristic checks; false positives are mitigated
  with a safe-phrases allowlist, not eliminated.
- 30-day log retention is a deployment concern (logrotate/cron),
  documented but not enforced in application code.
- Memory is assistive only; current session always overrides prior memory.

## [0.x.x] — prior weeks

See team weekly reports for Weeks 1–6. Week 7 was the first release-
candidate cycle; v1.0.0 is the first tagged release.