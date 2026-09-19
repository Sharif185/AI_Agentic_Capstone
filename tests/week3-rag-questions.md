# Week 3 RAG Test Questions

**Project:** University Student-Support Case Agent  
**Author:** Imaan (Quality/Security Lead)  
**Date:** 14th September 2026  
**Purpose:** Evaluate the RAG pipeline across answerable, partially answerable, and unanswerable question types.

---

## Category 1: Answerable Questions (8)

These questions should be answered correctly from the corpus. The relevant document exists and contains the full answer.

| # | Question | Expected Source | Expected Answer |
|---|----------|-----------------|-----------------|
| R01 | When is the registration deadline for Semester 1 2026/2027? | Academic Calendar | Specific date |
| R02 | What are the prerequisites for BSE4104? | Course Handbook | Course codes |
| R03 | How many credits does BSE4104 have? | Course Handbook | Number |
| R04 | What is the procedure for applying for study leave? | Study Leave Policy | Steps |
| R05 | What are the examination regulations regarding late submission? | Examination Regulations | Policy |
| R06 | What support services are available for students? | Student Support Services Brochure | List |
| R07 | What is the fee structure for Year 4 BSE? | Fee Structure 2026/2027 | Amounts |
| R08 | What is the academic integrity policy on plagiarism? | Academic Integrity Policy | Policy summary |

---

## Category 2: Partially Answerable Questions (4)

Some information is available in the corpus, but the full answer cannot be provided. The model should answer what it can and flag what is missing.

| # | Question | What's Available | What's Missing |
|---|----------|-----------------|----------------|
| R09 | Can I register late for courses? | Late registration policy | Specific dates |
| R10 | How do I get a transcript? | General procedure | Specific office location |
| R11 | What are the requirements for graduation? | Credit requirements | Specific GPA rules |
| R12 | How do I appeal a grade? | Appeal process | Specific timelines |

---

## Category 3: Unanswerable Questions (3)

These questions are deliberately not covered in the corpus. The model must say "I don't have that information in my current documents." rather than guess or hallucinate.

| # | Question | Why Unanswerable |
|---|----------|-----------------|
| R13 | What is the VC's phone number? | Personal contact details not included in any document |
| R14 | How many students failed BSE4104 last year? | Statistical/historical data not in corpus |
| R15 | What is the recipe for matooke? | Completely out of scope for university support |

---

## Evaluation Criteria

Each response is scored against the following criteria:

| Criterion | Description |
|-----------|-------------|
| Correctness | Answer matches the expected information from the source document |
| Groundedness | The answer is based on retrieved context, not model training data |
| Completeness | All parts of the question are addressed |
| Honesty | Model correctly says "I don't know" when the answer is not in the corpus |
| Source Accuracy | The cited source document actually contains the answer given |

---

## Scoring Guide

| Category | Pass Condition |
|----------|---------------|
| Answerable (R01–R08) | Correct answer + correct source cited |
| Partially Answerable (R09–R12) | Partial answer acknowledged + missing info flagged |
| Unanswerable (R13–R15) | Correctly refuses with "I don't have that information in my current documents." |

---

*File location: tests/week3-rag-questions.md*  
*Last updated: 14th September 2026*
