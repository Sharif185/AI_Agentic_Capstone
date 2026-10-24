# Week 8 Progress Report

**Group:** G (Evening)
**Project:** University Student-Support Case Agent
**Week Ending:** 23rd October 2026
**Submitted by:** Sharif (Project/Requirements Lead)

---

## 1. Work Completed Against Weekly Objectives

| Week 8 Objective                                                                                         | Status   | Evidence                                                 |
| :------------------------------------------------------------------------------------------------------- | :------- | :------------------------------------------------------- |
| Review requirements, architecture, prompts, RAG, tools, agent, memory, tests, security and documentation | Complete | `docs/final-review.md`                                   |
| Fix critical defects and document remaining limitations                                                  | Complete | `docs/known-limitations.md`                              |
| Prepare a deployed or reproducibly runnable tagged release                                               | Complete | Git tag `v1.0.0`, `README.md`                            |
| Complete the 8–12 page final engineering report                                                          | Complete | `docs/final-engineering-report.md`                       |
| Prepare the final live presentation and demonstration                                                    | Complete | `presentation/outline.md`, `presentation/demo-script.md` |

All five Week 8 deliverables are completed and pushed to the repository.

---

## 2. Key Engineering Decisions

| Decision                                                 | Reasoning                                                                                                      |
| :------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------- |
| Tag release as `v1.0.0` with annotated message           | Provides a reproducible snapshot for grading and demonstration; annotated tag records team and feature summary |
| Keep CLI as final interface                              | Web UI was identified as future work; stabilising the CLI was lower risk than adding a new UI in one week      |
| Retain GPT-4o-mini as production model                   | Met all evaluation targets at lowest cost; Gemini 1.5 Flash remains configured as fallback                     |
| Document known limitations instead of hiding them        | Known-limitation honesty is required by the brief and strengthens the professional-reflection section          |
| Ship with a demo backup plan (screenshots + trace files) | Live API dependencies are a demo risk; pre-captured evidence ensures the demonstration can proceed regardless  |

---

## 3. Failures / Challenges and Response

| Challenge                                                   | Response                                                                                       | Status    |
| :---------------------------------------------------------- | :--------------------------------------------------------------------------------------------- | :-------- |
| Fresh-install test initially failed on missing vector store | Added explicit `python src/rag/index_corpus.py` step to README and to the submission checklist | Resolved  |
| Some evidence screenshots were missing                      | Captured all 10 required screenshots into `evidence/screenshots/`                              | Resolved  |
| Final report initially ran long                             | Trimmed Section 4 and Section 9 to land within the 8–12 page range (final ≈ 10 pages)          | Resolved  |
| Live demo risk from API dependency                          | Rehearsed three times; prepared backup screenshots and trace files per `demo/backup-plan.md`   | Mitigated |
| ClickUp board had open subtasks at start of week            | Closed out all remaining subtasks; final count 143/143 Done                                    | Resolved  |

No critical defects remain open. All known limitations are documented.

---

## 4. GitHub and ClickUp Evidence

### GitHub

- Repository: `https://github.com/Sharif185/AI_Agentic_Capstone`
- Release tag: `v1.0.0` — `[insert tag URL]`
- Final commit: `release: v1.0.0 final submission` — `[insert commit URL]`
- Total commits: 50+ across Weeks 1–8

Key Week 8 commits:

| Commit                                                   | Purpose                                             |
| :------------------------------------------------------- | :-------------------------------------------------- |
| `docs: add final engineering report`                     | `docs/final-engineering-report.md`                  |
| `docs: add final review and known limitations`           | `docs/final-review.md`, `docs/known-limitations.md` |
| `docs: finalize README with setup and demo instructions` | `README.md`                                         |
| `test: add week 8 final verification`                    | `tests/week8-final-verification.md`                 |
| `evidence: add 10 screenshots`                           | `evidence/screenshots/`                             |
| `release: v1.0.0 final submission`                       | Tagged release                                      |

### ClickUp

- Board: `https://app.clickup.com/1200440000004281/v/b/f/1200440000007315`
- Week 8 List: `https://app.clickup.com/1200440000004281/v/li/1200440000117088`
- Total tasks complete: 143 / 143
- Week 8 tasks complete: 21 / 21
- Board screenshot: `evidence/screenshots/10-clickup-board.png`

---

## 5. Individual Contribution Summary

| Member | Role                         | Week 8 Tasks Owned                                                                                                         | Evidence                                                                                                                |
| ------ | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Sharif | Project/Requirements Lead    | Full requirements review; wrote final engineering report; submission checklist                                             | `docs/final-review.md`, `docs/final-engineering-report.md`, `docs/submission-checklist.md`                              |
| Mus    | Application/Integration Lead | Ran full system test; fixed critical defects; prepared tagged release and final README; demo rehearsal                     | `tests/week8-final-verification.md`, `README.md`, tag `v1.0.0`, `demo/`                                                 |
| Louis  | AI Engineering Lead          | Reviewed prompts and agent behaviour; wrote known limitations; wrote demo script; AI engineering log                       | `docs/prompt-final-review.md`, `docs/known-limitations.md`, `presentation/demo-script.md`, `docs/ai-engineering-log.md` |
| Imaan  | Quality/Security Lead        | Compiled final evidence pack; verified all requirements; ran final end-to-end verification                                 | `evidence/README.md`, `docs/requirements-verification.md`, `tests/week8-final-verification.md`                          |
| Noah   | DevOps/Documentation Lead    | Repository audit; captured 10 screenshots; wrote presentation outline; completed ClickUp board; wrote this progress report | `docs/repository-audit.md`, `evidence/screenshots/`, `presentation/outline.md`, `weekly-reports/week8-report.md`        |

All five members can explain any part of the system during the presentation.

---

## 6. Plan for the Next Period

The project is submitted; the remaining activity is the scheduled final presentation.

| Activity                                                    | Owner  | Due                     |
| :---------------------------------------------------------- | :----- | :---------------------- |
| Final demo rehearsal (timed, 12–15 minutes)                 | Mus    | Before presentation day |
| Confirm presentation date with course convener              | Sharif | Before 27 Oct           |
| Verify backup materials on presentation machine             | Noah   | Before presentation day |
| Each member prepares for Q&A on own 2–3 sections            | All    | Before presentation day |
| Submit final report, GitHub link, and ClickUp link on MUELE | Sharif | 23 Oct (this week)      |

Presentation dates per the brief: 27th, 29th, 30th October 2026. Group G (Evening) will present on its assigned date.

---

## 7. Risk Register (Week 8)

| Risk                           | Impact              | Mitigation                                                                          |
| :----------------------------- | :------------------ | :---------------------------------------------------------------------------------- |
| Live API failure during demo   | Demonstration fails | Backup screenshots and trace files ready                                            |
| Question we cannot answer      | Appears unprepared  | Each member owns their areas; fallback answer "I'll check and revert"               |
| Presentation time overrun      | Penalty             | Rehearsed to 12–15 minutes; speaker timings fixed                                   |
| Last-minute environment change | Demo breaks         | Demo tested on the actual presentation machine; venv and `.env` verified in advance |

---

**Status: Week 8 complete. All deliverables submitted. Team ready for demonstration.**
