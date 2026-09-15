# knowledge/corpus/ — Source Documents

This is the document corpus for the Week 3 RAG (Retrieval-Augmented Generation) pipeline, per the project charter's Data Strategy (Section 6): "publicly available university handbooks, course outlines, academic guidelines, published timetables."

## Documents in this corpus

| File | Covers | Source |
|---|---|---|
| `academic-calendar.md` | Semester dates, exam periods, holidays, graduation weeks (2025/26 and 2026/27) | https://mak.ac.ug/students/academic-calendar |
| `grading-policy.md` | Marks-to-grade conversion, GPA, degree classification, retakes, appeals | https://mak.ac.ug/students/grading |
| `examinations-policy.md` | Exam eligibility, deferred exams, academic progress categories, misconduct | https://mak.ac.ug/students/examinations |
| `bsse-program-overview.md` | BSSE programme structure, duration, career paths, entry routes | https://cocis.mak.ac.ug/academics/academic-programs/undergraduate-programs/bachelor-of-science-in-software-engineering/ |

All four are **real, publicly available Makerere University documents**, retrieved and paraphrased (not copy-pasted) on **15 September 2026**. Each file carries its own source URL and retrieval date at the top.

## Known gaps

- **No per-course syllabi** (e.g. a specific outline for an individual numbered course unit). `bsse-program-overview.md` covers the BSSE *programme* only, not individual course content. If the RAG pipeline needs to answer course-specific questions accurately, add a real syllabus document here — don't let the agent guess.
- **No student handbook / code of conduct document yet** — most public copies found were for graduate students, not undergraduates. Worth searching again or checking with the Academic Registrar's office for an undergraduate-specific version if that content is needed.
- University web pages change over time — re-check the source URLs periodically (e.g. before the Week 7 evaluation) and update the retrieval date if content has shifted.

## Adding more documents

Keep the same format: a short header block (Source URL, Retrieval date, Use note) followed by paraphrased content, plus a "How to use this document" section telling the agent what it should and shouldn't answer from that file (especially where something needs to be routed to a human per the project's safety boundary).
