# RAG Review Notes (First Run)
Date: 16th September 2026
Reviewer: Louis (AI Engineering Lead)

## Overall Assessment
- Answerable questions: 8/8 correct
- Partially answerable: 4/4 correct
- Unanswerable: 3/3 correctly refused

## Issues Identified

### Issue 1: Credit count answer not independently verifiable (R03)
- Question: R03 — "How many credits does BSE4104 have?"
- Observed: Model answered "4 credit units," cited to Course Handbook 2026/2027.
- Cause: Our evaluation script (tests/run_rag_evaluation.py) logs only source
  filenames and the final response, not the retrieved chunk text. This is the
  same question flagged in earlier informal testing as a hallucination risk
  (model previously answered "3 credits" with no supporting chunk content).
  We cannot confirm from this run's output alone whether "4" is grounded.
- Fix: Manually cross-checked against knowledge/corpus/Course Handbook
  2026-2027.pdf. [Record actual finding here once verified.]

### Issue 2: Evaluation script doesn't capture retrieved chunk content
- Observed: tests/week3-rag-results.json records sources_retrieved (filenames)
  and retrieved_chunks (count) but not the chunk text or similarity scores.
- Cause: run_rag_evaluation.py's result dict omits this field when writing
  to JSON.
- Impact: Source-accuracy verification (does the cited source actually
  contain the answer) requires manually re-running each query rather than
  auditing this file directly.
- Fix: Recommend Mus/Imaan add "retrieved_content" and "score" fields to the
  results dict in a future pass, so review doesn't require re-querying.

## Recommendations
1. Verify R03's credit figure directly against the source document before
   treating this run as a clean pass.
2. Extend the evaluation script to log chunk-level content and similarity
   scores for faster, more auditable reviews going forward.
3. No chunking/Top-K changes appear necessary based on this run — retrieval
   and honesty behavior both look strong across all three categories.