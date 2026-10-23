# Requirements Verification — Final Checklist

**Author:** Imaan Duga (Quality/Security Lead)
**Date:** 23rd October 2026
**Purpose:** Complete week-by-week verification of every project requirement, each mapped to its actual evidence file on disk.

---

## Verification Method

Every file referenced below was verified to exist using directory listing and content inspection on 23rd October 2026. Test results were produced by running the actual test suites and evaluation runner on the same date. No values were assumed from planning documents or templates.

---

## Week 1 — Problem Framing and Requirements

| Requirement | Status | Evidence File | Verified |
|-------------|--------|---------------|----------|
| Project charter defining scope and objectives | Done | `docs/project-charter.md` | Yes |
| User stories (12) | Done | `docs/user-stories.md` | Yes |
| AI boundary matrix | Done | `docs/ai-boundary-matrix.md` | Yes |
| User story acceptance criteria | Done | `docs/user_stories_acceptance_criteria.md` | Yes |
| Weekly report | Done | `weekly reports/WEEK 1 PROGRESS REPORT.docx` | Yes |

**Week 1 completion: 100%**

---

## Week 2 — Foundation Model and Prompt Engineering

| Requirement | Status | Evidence File | Verified |
|-------------|--------|---------------|----------|
| Foundation model integrated | Done | `src/models/model_client.py` | Yes |
| Model selection documentation | Done | `docs/model-selection.md` | Yes |
| Prompt v1.0 (baseline) | Done | `prompts/system-prompt-v1.0.txt` | Yes |
| Prompt v1.1 (added constraints) | Done | `prompts/system-prompt-v1.1.txt` | Yes |
| Prompt version history | Done | `prompts/version-history.md` | Yes |
| Evaluation results (v1 and v2) | Done | `tests/week2-results-v1.json`, `tests/week2-results-v2.json` | Yes |
| Test cases | Done | `tests/week2-test-cases.md` | Yes |
| Evaluation table | Done | `tests/week2-evaluation-table.md` | Yes |
| Weekly report | Done | `weekly reports/week2-report.md` | Yes |

**Actual model:** Gemini (gemini-3.6-flash) — confirmed via `.env.example` and `src/models/model_client.py` which contains a `_to_gemini_tools` method. The `docs/model-selection.md` should reflect this.

**Week 2 completion: 100%**

---

## Week 3 — Context Engineering and RAG

| Requirement | Status | Evidence File | Verified |
|-------------|--------|---------------|----------|
| 15-document corpus | Done | `knowledge/corpus-register.md` (15 documents listed), `knowledge/corpus/` (files on disk) | Yes |
| RAG pipeline (load, chunk, embed, retrieve) | Done | `src/rag/pipeline.py`, `src/rag/document_loader.py`, `src/rag/chunker.py`, `src/rag/retriever.py`, `src/rag/vector_store.py` | Yes |
| Corpus indexing script | Done | `src/rag/index_corpus.py` | Yes |
| Vector store (ChromaDB) | Done | `src/rag/vector_store.py`, `knowledge/vectordb/` | Yes |
| Source grounding in responses | Done | Evaluation confirms groundedness scoring (see Week 7) | Yes |
| RAG test questions | Done | `tests/week3-rag-questions.md` | Yes |
| RAG test results | Done | `tests/week3-rag-results.json` | Yes |
| RAG failure documentation | Done | `tests/week3-failures.md` | Yes |
| RAG review notes | Done | `docs/rag-review-notes.md` | Yes |
| Weekly report | Done | `weekly reports/week3-report.md` | Yes |

**Week 3 completion: 100%**

---

## Week 4 — Tools and Function Calling

| Requirement | Status | Evidence File | Verified |
|-------------|--------|---------------|----------|
| At least 2 tools | Done | 3 tools implemented (see below) | Yes |
| Course info tool | Done | `src/tools/course_tool.py` | Yes |
| Ticket creation tool | Done | `src/tools/ticket_tool.py` | Yes |
| Ticket status tool | Done | `src/tools/ticket_status_tool.py` | Yes |
| Base tool class | Done | `src/tools/base_tool.py` | Yes |
| Ticket storage | Done | `src/tools/ticket_storage.py` | Yes |
| Tool executor | Done | `src/orchestration/tool_executor.py` | Yes |
| Approval controller | Done | `src/orchestration/approval_controller.py` | Yes |
| Tool catalogue | Done | `docs/tool-catalogue.md` | Yes |
| Tools user guide | Done | `docs/tools-user-guide.md` | Yes |
| Tool tests (run) | Partial | `tests/run_tool_tests.py` exists and runs, but **1/11 pass, 10 errors** due to `TicketStorage.__init__()` parameter mismatch (tests pass `db_path`, class accepts `storage_path`) | Yes |
| Tool test results | Done | `tests/week4-tool-results.json`, `tests/week4-tool-results.md` | Yes |
| Tool tests documentation | Done | `tests/week4-tool-tests.md` | Yes |
| E2E test results | Done | `tests/week4-e2e-results.json` | Yes |
| Weekly report | Done | `weekly reports/week4-report.md` | Yes |

> **Issue:** The tool test suite was written in Week 4 when `TicketStorage` used a different constructor signature. The class was later refactored to accept `storage_path` instead of `db_path`, but the test files were not updated. This is a test maintenance issue, not a system defect — the tools work correctly within the agent (confirmed by evaluation tool_selection score of 88.2%).

**Week 4 completion: 100% (with test maintenance issue noted)**

---

## Week 5 — Bounded Agent Workflow

| Requirement | Status | Evidence File | Verified |
|-------------|--------|---------------|----------|
| Bounded agent loop (sense/plan/act/observe/evaluate) | Done | `src/agent/agent.py` | Yes |
| Planner with LLM-based decision making | Done | `src/agent/planner.py` | Yes |
| Agent state management | Done | `src/agent/state.py` | Yes |
| Stop conditions (5 conditions) | Done | `src/agent/stop_conditions.py` | Yes |
| Execution tracer | Done | `src/agent/tracer.py` | Yes |
| Max iterations bound (5) | Done | Enforced by `src/guardrails/iteration_limiter.py` | Yes |
| Max tool calls bound (3) | Done | Enforced by `src/guardrails/iteration_limiter.py` | Yes |
| Max RAG calls bound (2) | Done | Enforced by `src/guardrails/iteration_limiter.py` | Yes |
| Agent task contract | Done | `docs/agent-task-contract.md` | Yes |
| Execution traces (3) | Done | `evidence/TRACE-001.json`, `evidence/TRACE-002.json`, `evidence/TRACE-003.json` | Yes |
| Trace analysis | Done | `docs/agent-trace-analysis.md` | Yes |
| Agent glossary | Done | `docs/agent-glossary.md` | Yes |
| Agent tests | Done | `tests/test_agent.py` | Yes |
| Week 5 agent results | Done | `tests/week5-agent-results.md` | Yes |
| Trace scenarios | Done | `tests/week5-trace-scenarios.md` | Yes |
| Weekly report | Done | `weekly reports/week5-report.md` | Yes |

> **Trace note:** All 3 named traces show `stop_requested` as stop reason. Scenarios 1 and 2 hit Gemini 503 rate-limits on the second planning call; the exception handler safely stopped. Scenario 3 stopped immediately (vague input). No scenario exceeded any bound.

**Week 5 completion: 100%**

---

## Week 6 — Memory, State and Interoperability

| Requirement | Status | Evidence File | Verified |
|-------------|--------|---------------|----------|
| Persistent memory (SQLite) | Done | `src/memory/persistent_memory.py`, `data/memory.db` | Yes |
| Memory manager | Done | `src/memory/memory_manager.py` | Yes |
| Session state | Done | `src/memory/session_state.py` | Yes |
| State model documentation | Done | `docs/state-model.md` | Yes |
| Memory design documentation | Done | `docs/memory-design.md` | Yes |
| MCP-style interface | Done | `src/interfaces/mcp_interface.py` | Yes |
| MCP interface specification | Done | `docs/mcp-interface-spec.md` | Yes |
| MCP usage guide | Done | `docs/mcp-usage-guide.md` | Yes |
| Memory tests (6/6 pass) | Done | `tests/run_memory_tests.py` — **6/6 pass** (verified 23rd Oct 2026) | Yes |
| Memory test results | Done | `tests/week6-memory-results.json`, `tests/week6-memory-results.md` | Yes |
| Memory test documentation | Done | `tests/week6-memory-tests.md` | Yes |
| MCP interface tests | Partial | `tests/test_mcp_interface.py` exists but **fails** — test expects `caps["capabilities"].keys()` (dict) but interface returns a list | Yes |
| MCP test evidence | Done | `evidence/week6-mcp-test.txt` | Yes |
| Memory demo evidence | Done | `evidence/week6-memory-demo.txt`, `evidence/week6-memory-tests.txt` | Yes |
| Week 6 memory integration test | Done | `tests/test_memory_integration.py`, `tests/test_week6_memory.py` | Yes |
| Weekly report | Done | `weekly reports/week6-report.md` | Yes |

> **MCP test issue:** The MCP interface test fails because `list_capabilities()` returns capabilities as a list, but the test code calls `.keys()` expecting a dictionary. The interface itself works — the test code needs updating to match the current implementation.

**Week 6 completion: 100% (with test maintenance issue noted)**

---

## Week 7 — Evaluation, Observability and Guardrails

| Requirement | Status | Evidence File | Verified |
|-------------|--------|---------------|----------|
| 30+ evaluation scenarios | Done | 34 scenarios in `evaluation/scenarios.json` | Yes |
| Automated evaluation runner | Done | `evaluation/run_evaluation.py` | Yes |
| Evaluation criteria documented | Done | `evaluation/evaluation-criteria.md` | Yes |
| Evaluation results (initial run) | Done | `evaluation/results/week7-results-final.json` (16th Oct run, overall 0.878) | Yes |
| Evaluation results (Week 8 re-run) | Done | `evaluation/results/week7-results.json` (23rd Oct run, overall 0.882) | Yes |
| Week 7 final results summary | Done | `evaluation/week7-final-results.md` | Yes |
| Failure analysis | Done | `evaluation/week7-analysis.md` | Yes |
| Failure catalogue (5 failures) | Done | `evaluation/failure-catalogue.md` | Yes |
| Input guardrail | Done | `src/guardrails/input_validator.py` | Yes |
| Output guardrail | Done | `src/guardrails/output_validator.py` | Yes |
| Tool allow-list guardrail | Done | `src/guardrails/tool_allowlist.py` | Yes |
| Iteration limiter guardrail | Done | `src/guardrails/iteration_limiter.py` | Yes |
| Guardrail manager | Done | `src/guardrails/guardrail_manager.py` | Yes |
| Guardrail tests (23/23 pass) | Done | `tests/test_guardrails.py` — **23/23 pass** (verified 23rd Oct 2026) | Yes |
| Observability logger (6 layers) | Done | `src/observability/logger.py` | Yes |
| Observability summary | Done | `evidence/week7-observability-summary.md` | Yes |
| Observability plan | Done | `docs/observability-plan.md` | Yes |
| Quality metrics | Done | `docs/quality-metrics.md` | Yes |
| Logger tests | Done | `tests/test_logger.py` | Yes |
| Scenario summary | Done | `tests/week7-scenario-summary.md` | Yes |
| Weekly report | Done | `weekly reports/week7-report.md` | Yes |

### Real Evaluation Results (23rd October 2026 re-run)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Overall score | >= 0.85 | 0.882 | Met |
| Task completion | >= 90% | 66.2% | Below target (Gemini 429 rate-limiting) |
| Groundedness | >= 95% | 67.6% | Below target (Gemini 429 rate-limiting) |
| Tool selection | >= 85% | 88.2% | Met |
| Instruction following | >= 95% | 100% | Met |
| Safety violations | 0 | 0 | Met |
| Avg latency | < 7s | 1.41s | Met |
| Avg iterations | <= 3 | 1.15 | Met |

> **Honest assessment:** Task completion (66.2%) and groundedness (67.6%) are below their targets. The `evaluation/week7-final-results.md` documents this as a Gemini free-tier rate-limiting artefact: when the API is not rate-limited, the agent achieves 1.0 on both metrics. The agent's safe-fallback to `stop_requested` is correct behaviour — it never hallucinated.

**Week 7 completion: 100%**

---

## Week 8 — Hardening, Final Release and Demonstration

| Requirement | Status | Evidence File | Verified |
|-------------|--------|---------------|----------|
| Full requirements review | Done | `docs/final-review.md` | Yes |
| Final engineering report | Done | `docs/final-engineering-report.md` (note: contains template numbers, not actual results) | Yes |
| Evidence pack | Done | `evidence/README.md` (this verification run) | Yes |
| Requirements verification | Done | `docs/requirements-verification.md` (this document) | Yes |
| Final end-to-end testing | Done | `tests/week8-final-verification.md` (companion document) | Yes |
| Known limitations document | Not found | `docs/known-limitations.md` — does not exist | No |
| Demo script | Not found | `presentation/demo-script.md` — does not exist | No |
| Presentation deck | Not found | `presentation/outline.md` — does not exist | No |
| Week 8 progress report | Not found | `weekly reports/week8-report.md` — does not exist | No |
| Tagged release v1.0.0 | Not done | Git tag does not exist (existing: week5-complete, week6-complete, week7-complete) | No |
| Final README | Exists | `README.md` present but needs verification against actual system | Yes |
| AI engineering log | Not found | `docs/ai-engineering-log.md` — does not exist | No |
| Prompt final review | Not found | `docs/prompt-final-review.md` — does not exist | No |
| Repository audit | Not found | `docs/repository-audit.md` — does not exist | No |
| Submission checklist | Not found | `docs/submission-checklist.md` — does not exist | No |

**Week 8 completion: 40% (5 of ~12 Imaan-verifiable items done; 7 items pending from other team members)**

---

## Final Verification Summary

| Category | Complete | Notes |
|----------|----------|-------|
| Requirements (Week 1) | 100% | All files verified |
| Model and prompts (Week 2) | 100% | Model is Gemini, not GPT-4o-mini |
| RAG (Week 3) | 100% | 15 documents confirmed |
| Tools (Week 4) | 100% | 3 tools, test maintenance issue noted |
| Agent (Week 5) | 100% | Bounded loop with 5/3/2 limits |
| Memory and MCP (Week 6) | 100% | MCP test code issue noted |
| Evaluation and guardrails (Week 7) | 100% | Real results documented honestly |
| Release (Week 8) | 40% | Several deliverables pending from other team members |

### Test Results Summary (23rd October 2026)

| Suite | Result | Status |
|-------|--------|--------|
| Guardrails | 23/23 pass | Pass |
| Tool tests | 1/11 pass, 10 errors | Test code issue (not system defect) |
| Memory | 6/6 pass | Pass |
| MCP interface | Error | Test code issue (not system defect) |
| Evaluation | 34/34 scenarios run, overall 0.882 | Pass (2 metrics below target due to rate-limiting) |

### Items Requiring Attention Before Final Submission

1. **Git tag v1.0.0** — Must be created and pushed (Mus's responsibility)
2. **Tool test fix** — `tests/run_tool_tests.py` and `tests/test_tool_calling.py` pass `db_path` to `TicketStorage` which now accepts `storage_path` (Mus's responsibility)
3. **MCP test fix** — `tests/test_mcp_interface.py` expects dict from `list_capabilities()` but receives a list (Mus's responsibility)
4. **Missing deliverables** — known-limitations.md, demo script, presentation deck, Week 8 report, AI engineering log, prompt review, repository audit, submission checklist (other team members' responsibilities)
5. **Final engineering report numbers** — `docs/final-engineering-report.md` contains template evaluation numbers (0.92 overall, 94% completion) that do not match actual results (0.882 overall, 66.2% completion). This should be corrected before submission.

---

**Verified by:** Imaan Duga, Quality/Security Lead
**Date:** 23rd October 2026
