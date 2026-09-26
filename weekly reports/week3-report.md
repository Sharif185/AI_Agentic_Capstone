# Week 3 Progress Report

**Group:** BSE4104 Capstone Team | **Project:** University Student-Support Case Agent | **Week Ending:** 18th September 2026

## Work Completed Against Objectives

| Objective                  |  Status   | Evidence                            |
| :------------------------- | :-------: | :---------------------------------- |
| Assemble controlled corpus | completed | 15 documents in `knowledge/corpus/` |
| Record provenance          | completed | `knowledge/corpus-register.md`      |
| Implement ingestion        | completed | `src/rag/document_loader.py`        |
| Implement chunking         | completed | `src/rag/chunker.py` (600/100)      |
| Implement indexing         | completed | `src/rag/vector_store.py` (Chroma)  |
| Implement retrieval        | completed | `src/rag/retriever.py` (Top-5)      |
| Source grounding           | completed | Sources shown in all responses      |
| 15 RAG test questions      | completed | `tests/week3-rag-questions.md`      |
| Document 3 failures        | completed | `tests/week3-failures.md`           |
| Working RAG pipeline       | completed | `python src/main.py` works          |

## Key Engineering Decisions

- **Chose Chroma:** Simple, persistent, and optimal for small corpora.
- **Chunk size 600/100:** Increased from 500/50 after initial failure analysis.
- **Top-K = 5:** Increased from 3 for higher context coverage.
- **Prompt v2.1:** Enforced strict context constraints to prevent hallucinations.
- **15 documents:** Within recommended 10–50 range

## Failures

| Challenge                       | Response                            |  Status  |
| :------------------------------ | :---------------------------------- | :------: |
| Wrong document retrieved        | Added metadata filtering            |  Fixed   |
| Information split across chunks | Increased overlap to 100 characters |  Fixed   |
| Hallucination despite context   | Strengthened prompt constraints     |  Fixed   |
| PDF parsing issues              | Switched to PyPDFLoader             | Resolved |

## Individual Contributions

- **Sharif:** Corpus register, coordination (`knowledge/corpus-register.md`).
- **Mus:** RAG pipeline implementation, CLI integration (`src/rag/`, `src/main.py`).
- **Louis:** System architecture, prompts v2.0/v2.1 (`docs/architecture/`, `prompts/`).
- **Imaan:** 15 test questions, evaluation, failure documentation (`tests/`).
- **Noah:** RAG architecture diagram, README updates, progress report (`docs/architecture/rag-architecture.png`, `README.md`, `weekly-reports/week3-report.md`).

# Risks and Mitigations

| Risk                     | Mitigation                           |
| :----------------------- | :----------------------------------- |
| Retrieval quality issues | Continue tuning chunk size and Top-K |
| Token costs increasing   | Monitor usage, use GPT-4o-mini       |
| Team availability        | Tasks assigned, daily check-ins      |

## Plan for Week 4

- Define 2+ agent tools with input/output schemas.
- Implement tool and function calling pipelines.
- Integrate human approval safeguards for high-impact actions.
