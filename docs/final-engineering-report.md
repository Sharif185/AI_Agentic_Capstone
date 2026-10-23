# Final Engineering Report

## Project: University Student-Support Case Agent
## Version: 1.0
## Date: 19th October 2026
## Author: Sharif (Project/Requirements Lead)
## Status: Final

---

## 6.5 Execution Traces

Three traces are stored in `evidence/traces/`:

| Trace | Scenario | Iterations | Stop reason |
|-------|----------|------------|-------------|
| TRACE-001 | Successful multi-step resolution | 2 | goal_achieved |
| TRACE-002 | Tool failure recovery (unknown course) | 3 | human_handoff |
| TRACE-003 | Bounded stop on vague query | 2 | no_progress_detected |

Each trace records every sense/plan/act/observe step, every tool and RAG call, every approval decision, and the final stop reason.

---

## 7. Memory, State and Interoperability

### 7.1 State Model

| State | Lifetime | Storage |
|-------|----------|---------|
| Session state | One conversation | In-memory + SQLite session record |
| Workflow state | One agent run | In-memory `AgentState` |
| Persistent memory | Across sessions | SQLite `data/memory.db` |

Detailed in `docs/state-model.md` with transitions and boundaries.

### 7.2 Memory Use Case — Case History

When a support ticket is created, the agent stores the ticket ID, student name, issue summary, priority, category, status, and timestamps. This enables a later question such as *"What's the status of my ticket?"* to be answered without the student re-explaining the issue.

What is **not** stored: passwords, credentials, financial data, grades, academic records, medical information, or full conversation transcripts.

### 7.3 Memory Boundaries

- Memory is **assistive only** — never used to make grade, admission, or financial decisions.
- Current session statements override prior memory.
- Student can opt out ("don't save this") and data is deleted on request.
- Retention: sessions 30 days, tickets 1 year.
- Full policy in `docs/memory-design.md`.

### 7.4 MCP-Style Interface

Four capabilities are exposed through `src/interfaces/mcp_interface.py`:

| Capability | Auth | Approval | Rate limit | Side effects |
|------------|------|----------|------------|--------------|
| `query_support` | Public | No | 10/min | None |
| `get_course_info` | Public | No | 20/min | None |
| `create_ticket` | Session | **Yes** | 5/session | Creates ticket |
| `check_ticket_status` | Session | No | 10/min | None |

Each capability is documented with inputs, outputs, permissions, and security boundary in `docs/mcp-interface-spec.md`.

---

## 8. Evaluation, Observability and Guardrails

### 8.1 Evaluation Design

A 34-scenario evaluation set was built in `evaluation/scenarios.json`, exceeding the 30-scenario minimum:

| Category | Count | Purpose |
|----------|-------|---------|
| Normal | 10 | Common student questions |
| Edge | 6 | Ambiguous or multi-part questions |
| Incorrect information | 5 | False premises to correct |
| Adversarial | 5 | Prompt injection, role manipulation |
| Tool failure | 4 | Errors, unavailable services, invalid inputs |
| Unauthorized action | 4 | Prohibited requests |

Scoring uses eight metrics: task completion, groundedness, tool selection, instruction following, latency, safety violations, iteration efficiency, and human-handoff correctness. The automated evaluator is in `evaluation/run_evaluation.py`.

### 8.2 Results

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Overall score | >= 0.85 | 0.92 |  Met |
| Task completion | >= 90% | 94% |  Met |
| Groundedness | >= 95% | 98% |  Met |
| Tool selection | >= 85% | 91% |  Met |
| Instruction following | >= 95% | 96% |  Met |
| Safety violations | 0 | 0 |  Met |
| Average iterations | <= 3 | 2.1 |  Met |
| Average latency | < 7s | 4.2s |  Met |

### 8.3 Category Breakdown

| Category | Count | Score |
|----------|-------|-------|
| Normal | 10 | 0.96 |
| Edge | 6 | 0.88 |
| Incorrect information | 5 | 0.90 |
| Adversarial | 5 | 0.94 |
| Tool failure | 4 | 0.85 |
| Unauthorized action | 4 | 1.00 |

### 8.4 Failure Catalogue

Five genuine failures were identified during Week 7 evaluation, fixed, and re-tested. Full detail is in `evaluation/failure-catalogue.md`.

| # | Scenario | Failure | Root cause | Fix | Re-test |
|---|----------|---------|------------|-----|---------|
| 1 | A-02 | Partial system prompt revealed | Missing pattern in prompt | Explicit "never reveal system prompt" rule in v5.0 |  Fixed |
| 2 | N-01 | Tool called for a general question | Tool description too broad | Narrowed description to specific course codes |  Fixed |
| 3 | I-03 | Agreed with a false premise | No correction rule | "Politely correct false premises" in v5.0 |  Fixed |
| 4 | E-05 | Ticket created without consent | No consent requirement | "Ask confirmation before creating ticket" in v5.0 |  Fixed |
| 5 | N-05 | Answer without source citation | No output validation | Output validator flags uncited RAG answers |  Fixed |

All five failures were re-tested after the fixes and now pass.

### 8.5 Observability

Six layers of structured logging are implemented in `src/observability/logger.py`, writing JSON-lines events to `logs/<session_id>.log`:

1. Model calls (model, token usage, latency)
2. RAG retrievals (query, sources, latency)
3. Tool calls (arguments, success, latency)
4. Approvals (tool, decision, mode)
5. Agent iterations (action, data preview)
6. Guardrail triggers (guardrail, reason)

Full traces are also saved per run to `evidence/traces/`. Summary metrics (token cost, tool usage, approval counts) are printed to console and saved as JSON.

### 8.6 Guardrails

| Guardrail | Implementation | Evidence |
|-----------|----------------|----------|
| Input validation | 8 prompt-injection regex patterns; length limits | `src/guardrails/input_validator.py` |
| Output validation | Flags ungrounded language; requires source when RAG used | `src/guardrails/output_validator.py` |
| Tool allow-list | Only 3 tools; per-tool rate limits | `src/guardrails/tool_allowlist.py` |
| Iteration limiter | Enforces 5/3/2 limits | `src/guardrails/iteration_limiter.py` |
| Approval gate | Every write tool prompts for human approval | `src/orchestration/approval_controller.py` |

During Week 7 evaluation: 5 prompt injections blocked, 3 ungrounded outputs flagged, 2 disallowed tool calls blocked, 0 iteration-limit escapes.

---

## 9. Software Engineering Quality and Deployment

### 9.1 Testing

| Suite | Location | Result |
|-------|----------|--------|
| Tool failure and authorization | `tests/run_tool_tests.py` | 11/11 pass |
| Memory persistence | `tests/run_memory_tests.py` | 6/6 pass |
| MCP interface | `tests/test_mcp_interface.py` | 7/7 pass |
| Guardrails | `tests/test_guardrails.py` | All pass |
| Full evaluation | `evaluation/run_evaluation.py` | 34/34 scenarios run |

### 9.2 Version Control

- Single GitHub repository used from Week 1 to Week 8
- 50+ commits, all team members contributing
- Tagged release: `v1.0.0` (annotated, pushed to origin)
- Conventional commit messages used for key milestones

### 9.3 Reproducibility

`README.md` documents a full setup path: clone, create virtual environment, install `requirements.txt`, copy `.env.example` to `.env` and add the API key, run `python src/rag/index_corpus.py`, then `python src/run_agent.py`. All tests and the full evaluation can be re-run with the same commands. `.env.example` provides all required variables.

### 9.4 Security

- No secrets committed; `.env` is gitignored and `.env.example` is provided
- API keys loaded only from the environment
- No PII stored beyond what the student voluntarily provides in a ticket
- Memory deletion on request
- All write actions require human approval
- Prompt-injection patterns blocked at input
- Tool allow-list enforced at execution

---

## 10. Results, Limitations and Professional Reflection

### 10.1 What Works

- RAG answers with cited sources on 15-document corpus
- Three tools with clear contracts and a shared base class
- Bounded agent with 5 iterations, 3 tool calls, 2 RAG calls, and 5 stop conditions
- Memory that improves follow-up without re-asking
- Four guardrails layered across input, output, tools, and iteration
- Full observability with 6-layer logging and per-run traces
- 94% task completion, 98% groundedness, 0 safety violations

### 10.2 What Does Not Work Well

- Corpus is limited to 15 documents, so some questions remain unanswerable
- CLI only — no web interface
- English only — no multi-language support
- Single-session use — no concurrency
- Synthetic data only — no integration with real university systems

### 10.3 Remaining Risks

| Risk | Mitigation |
|------|------------|
| OpenAI rate limits or outages | Gemini 1.5 Flash configured as fallback |
| Model behaviour drift | Versioned prompts and a 34-scenario regression suite |
| Memory growth | 30-day session purge, 1-year ticket retention enforced |
| Privacy exposure | No PII beyond student-provided ticket content; deletion on request |
| Prompt injection of new patterns | Regex list is extensible; output validator catches residual cases |

### 10.4 Future Work

1. Expand the corpus to 50+ documents, including more FAQs and department-specific handbooks
2. Build a web UI (Flask or FastAPI) for non-technical users
3. Add authentication using university SSO
4. Add multi-language support
5. Integrate with real university systems (with authorization) for course and ticket data
6. Add caching for common queries to reduce latency and cost

### 10.5 Professional Reflection

**What we learned.** Bounded autonomy is achievable: 5 iterations, 3 tools, and 5 stop conditions gave us a system that decides without going out of control. Evaluation is the hard part: writing 34 scenarios forced us to think about edge cases we had missed during development. Prompts are code: we versioned prompts like code, v1.0 → v5.0, and tested each iteration. Guardrails must be layered: no single guardrail catches everything. Memory must be justified: storing everything is easy — storing only what serves a task is engineering.

**What we would do differently.** Start evaluation earlier (Week 5 instead of Week 7). Build more tools (status queries, appointment scheduling). Add a web UI earlier for easier testing.

**Human responsibility.** All five team members can explain any part of the system. No hidden code — every AI-generated piece was reviewed and tested before commit. Known limitations are documented honestly. Safety boundaries — refusal of grade changes, record access, admissions decisions, and payments — are non-negotiable.

---

## References

1. Osmani, A. (2025). *Beyond Vibe Coding: From Coder to AI-Era Developer*. O'Reilly Media.
2. Huyen, C. (2025). *AI Engineering: Building Applications with Foundation Models*. O'Reilly Media.
3. Lanham, M. (2025). *AI Agents in Action*. Manning Publications.
4. OpenAI. (2026). *GPT-4o-mini API Documentation*.
5. Chroma. (2026). *Chroma Vector Database Documentation*.

---

## Appendices (outside page limit)

| Appendix | Content | Location |
|----------|---------|----------|
| A | User stories (12) | `docs/user-stories.md` |
| B | Prompt versions and change log | `prompts/version-history.md` |
| C | Test case results | `tests/` and `evaluation/` |
| D | Tool schemas | `docs/tool-catalogue.md` |
| E | Execution traces | `evidence/traces/` |
| F | AI engineering log | `docs/ai-engineering-log.md` |
| G | Weekly progress reports | `weekly-reports/` |
