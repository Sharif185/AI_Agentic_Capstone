# Week 3 RAG Retrieval & Grounding Failures

**Project:** University Student-Support Case Agent  
**Author:** Imaan (Quality/Security Lead)  
**Date:** 17th September 2026  
**Purpose:** Document the 3 most significant retrieval and grounding failures observed during the Week 3 RAG evaluation, with root cause analysis and verified fixes.

---

## Summary

| Failure | Type | Question | Fixed? |
|---------|------|----------|--------|
| F1 | Wrong document retrieved | "What are the requirements for graduation?" | ✅ Yes |
| F2 | Information split across chunks | "What is the procedure for applying for study leave?" | ✅ Yes |
| F3 | Hallucination despite context | "How many credits does BSE4104 have?" | ✅ Yes |

---

## Failure 1: Wrong Document Retrieved

### Description
The retriever returned the wrong source document, causing the model to produce an answer that was factually incorrect for the question asked.

### Details

| Field | Value |
|-------|-------|
| **Question** | What are the requirements for graduation? |
| **Test Case ID** | R11 |
| **Expected Source** | Course Handbook 2026/2027 |
| **Retrieved Source** | Fee Structure 2026/2027 |
| **Retrieval Score** | 0.71 (high — incorrectly confident) |

### Observed Behaviour
The model answered with fee payment requirements ("outstanding fees must be cleared before graduation clearance") because the Fee Structure document contained the phrase "graduation requirements" in the context of fee clearance. The model treated this as the primary answer to the question rather than flagging that the full graduation requirements were not present.

### Root Cause
The word "requirements" in the query matched the phrase "fee requirements" and "graduation clearance requirements" in the Fee Structure document. Because both documents contained overlapping vocabulary, the similarity score for the Fee Structure chunk was higher than the Course Handbook chunk. The chunker had also split the graduation requirements section of the Course Handbook across two chunks, reducing the relevance score of either chunk individually.

### Impact
- **Severity:** High
- The model gave a misleading partial answer (only the fee clearance condition) without indicating that credit completion and coursework requirements were missing.
- A student relying on this answer could believe they only need to clear fees to graduate.

### Fix Applied
1. **Metadata filtering** — Added `document_type` metadata tags to all corpus documents during indexing. Retrieval for academic-policy questions now filters to prefer documents tagged `type: academic_regulations` or `type: handbook` before falling back to general search.
2. **Chunking improvement** — Increased chunk overlap from 50 to 100 characters so that related paragraphs within the Course Handbook stay semantically connected across adjacent chunks.
3. **Top-K increase** — Increased retrieval from Top-3 to Top-5 so that even if one relevant chunk scores lower, it still enters the context window.

### Re-test Result
✅ The retriever now correctly returns the Course Handbook 2026/2027 as the primary source. The response covers credit unit requirements, core course completion, and the Final Year Project requirement.

---

## Failure 2: Information Split Across Chunks

### Description
The answer to the question existed in the corpus, but it was spread across multiple consecutive chunks. Only one chunk was retrieved, producing an incomplete answer.

### Details

| Field | Value |
|-------|-------|
| **Question** | What is the procedure for applying for study leave? |
| **Test Case ID** | R04 |
| **Expected Source** | Study Leave Policy |
| **Retrieved Source** | Study Leave Policy (correct) |
| **Chunks Retrieved** | 1 of 3 relevant chunks |

### Observed Behaviour
The model returned only steps 1 and 2 of the 7-step study leave procedure. Steps 3–7 were present in the corpus but in a separate chunk that was not retrieved because the similarity score of the second chunk (which began mid-procedure) was lower than unrelated chunks from other documents.

### Root Cause
The Study Leave Policy procedure was split at a natural sentence boundary that happened to fall between step 2 and step 3. The second chunk began with "3. Submit the completed form..." — starting mid-list without the introductory context that made it semantically similar to the query. Without the overlap text connecting it to the first chunk, the retriever did not recognise it as continuation content.

With the original settings (chunk size: 500, overlap: 50), the overlap was not wide enough to carry the procedural context across the boundary.

### Impact
- **Severity:** Medium
- The model gave an incomplete answer without indicating that the procedure continued beyond step 2.
- A student following these instructions would not know they still need to submit to the Dean and wait for written confirmation.

### Fix Applied
1. **Increased chunk overlap** — Overlap increased from 50 to 100 characters. This ensures that the beginning of each chunk contains enough context from the previous chunk for the retriever to recognise it as a continuation.
2. **Increased Top-K** — Retrieval increased from Top-3 to Top-5, giving the second and third chunks of the procedure a chance to enter the context even if their individual scores are lower.
3. **Chunk merging for sequential content** — For documents where section headers (e.g., numbered steps) are detected, adjacent chunks from the same section are merged before being passed to the context builder.

### Re-test Result
✅ All 7 steps of the study leave procedure are now returned in the response. The retriever correctly pulls three consecutive chunks from the Study Leave Policy document.

---

## Failure 3: Hallucination Despite Context

### Description
The retrieved context did not contain the answer to the question, but instead of refusing, the model used its training data to generate a plausible-sounding but unverified answer.

### Details

| Field | Value |
|-------|-------|
| **Question** | How many credits does BSE4104 have? |
| **Test Case ID** | R03 |
| **Expected Source** | Course Handbook 2026/2027 |
| **Retrieved Source** | Course Handbook 2026/2027 (correct document, wrong section) |
| **Model Response** | "BSE4104 carries 3 credits." |
| **Actual Context** | Course description text with no credit number |

### Observed Behaviour
The retriever returned the correct document (Course Handbook) but retrieved the section containing the course description and learning outcomes — not the credit unit table. The credit unit table was in a separate part of the handbook that was not retrieved.

Rather than saying "I don't have that information in my current documents," the model produced "BSE4104 carries 3 credits." This number was not present anywhere in the retrieved context. The model drew on its general training knowledge of university credit systems to fill the gap.

### Root Cause
The system prompt v2.0 instructed the model to "ONLY use information from the provided context documents" but did not explicitly prohibit using training data as a fallback. When the retrieved context was topically relevant (it was about BSE4104) but missing the specific detail, the model treated the partial context as sufficient permission to complete the answer from memory.

This is a **grounding failure** — the model was not sufficiently constrained to refuse when the specific fact was absent.

### Impact
- **Severity:** High
- **Correctness risk:** The model stated a specific number with no basis in the retrieved context.
- A student relying on this answer could make incorrect course planning decisions.
- This type of failure is particularly dangerous because it produces a confident, specific, wrong answer rather than an obvious error.

### Fix Applied
1. **Strengthened system prompt** — Updated to system prompt v2.1, which adds:
   ```
   CRITICAL CONSTRAINT:
   - If the context does NOT contain the answer, you MUST say:
     "I don't have that information in my current documents."
   - NEVER use your training data to answer questions
   - NEVER guess or infer information not explicitly in the context
   ```
2. **Explicit absence check** — The prompt now instructs the model to check whether the specific fact (not just the topic) is present in the context before answering.
3. **Post-generation validation** — A lightweight check was added in the pipeline to flag responses that contain specific numbers, dates, or named entities that do not appear verbatim in the retrieved context chunks. Flagged responses are reviewed before being returned to the user.

### Re-test Result
✅ With system prompt v2.1, the model now correctly responds: "I don't have that information in my current documents. The retrieved section covers the course description for BSE4104 but does not include the credit unit count. Would you like me to create a support ticket?"

---

## Lessons Learned

| Lesson | Detail |
|--------|--------|
| Chunk size and overlap matter significantly | Too little overlap breaks procedural content that spans chunk boundaries |
| Top-K should be tuned per query type | Simple factual queries work well at K=3; multi-step procedures need K=5 |
| Correct document ≠ correct answer | Retrieving the right document but the wrong section still produces failures |
| Prompt must explicitly forbid training data | "Only use context" is not strong enough — the model needs an explicit prohibition on inference from training knowledge |
| Post-generation validation catches hallucinations | Comparing response entities against retrieved text is a practical safety net |
| Vocabulary overlap causes cross-document confusion | Common words like "requirements" and "regulations" pull in irrelevant documents; metadata filtering reduces this noise |

---

*File location: tests/week3-failures.md*  
*Last updated: 17th September 2026*
