# Week 2 Progress Report

**Group:** BSE4104 Capstone Team  
**Project:** University Student-Support Case Agent  
**Period:** 7th – 11th September 2026

## Work Completed Against Objectives

| Objective                        |  Status   | Evidence                                     |
| :------------------------------- | :-------: | :------------------------------------------- |
| Choose accessible model          | completed | `docs/model-selection.md`                    |
| Integrate model into application | completed | `src/models/model_client.py`, `src/main.py`  |
| Create Prompt Specification v1.0 | completed | `docs/prompt-specification-v1.md`            |
| Create 10 test cases             | completed | `tests/week2-test-cases.md`                  |
| Version two prompt iterations    | completed | `prompts/system-prompt-v1.0.txt`, `v1.1.txt` |
| Working baseline interaction     | completed | Terminal CLI demonstration                   |

## Key Engineering Decisions

- Selected **GPT-4o-mini** as primary model due to context handling, speed, and low operational cost (<$5/mo during dev).
- Established prompt iteration workflows prior to retrieval augmented generation (RAG) implementation to isolate baseline model behaviors.
- Upgraded system prompt from `v1.0` to `v1.1` to enforce security constraints against prompt injection and out-of-scope queries.

## Failures & Mitigations

- **Issue:** Model attempted to answer generic trivia (TC-003).  
  **Fix:** Added explicit domain restriction in `v1.1`.
- **Issue:** Partial compliance with jailbreak inputs (TC-009).  
  **Fix:** Enforced strict fallback instructions and explicit boundary conditions in system instructions.

## Individual Contributions

- **Sharif:** Prompt Specification v1.0, deliverable coordination (`docs/prompt-specification-v1.md`).
- **Mus:** Project workspace setup, API client implementation, CLI integration (`src/models/`, `src/main.py`).
- **Louis:** Model selection analysis, system prompt authoring & iteration (`docs/model-selection.md`, `prompts/`).
- **Imaan:** Test case suite creation, execution scripts, evaluation matrix (`tests/`).
- **Noah:** Prompt versioning records, iteration logs, and Week 2 progress reporting (`prompts/version-history.md`, `docs/prompt-iteration-log.md`, `weekly-reports/week2-report.md`).

## Next Steps (Week 3 Preparation)

- Build initial 10–50 document vector corpus.
- Set up document ingestion, chunking, and embedding retrieval pipelines.
- Expand test cases to evaluate context-retrieved response accuracy.
