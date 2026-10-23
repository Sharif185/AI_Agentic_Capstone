# Known Limitations

| # | Limitation | Current | Impact | Future |
|---|---|---|---|---|
| 1 | Corpus size | 15 documents | Some questions are unanswerable | Expand to 50+ documents, add FAQs |
| 2 | No web UI | CLI only | Not friendly for non-technical users | Build a web UI (Flask/FastAPI) |
| 3 | Synthetic data only | No real student records | Cannot test with production data | Integrate with university systems, with approval |
| 4 | English only | English prompts and responses | Cannot serve non-English speakers | Add multi-language support |
| 5 | Single session | One user at a time | No concurrent users | Add session management and a queue |
| 6 | Latency variance | 2 to 8 seconds (avg 4.2s) | Slower for multi-step requests | Cache common queries |
| 7 | No real authentication | Session-based, no login | Cannot verify student identity | Integrate university SSO |
| 8 | Memory storage | Local SQLite, unencrypted | Data at rest is unencrypted | Add encryption and secure storage |
| 9 | Prompt files not loaded | Runtime prompt lives in planner.py | Prompt file and runtime can drift | Load prompts from `prompts/` |

## Edge Cases
- **Handled:** Tool failures (recovery tested), vague queries (bounded stop), prompt injection (refused), prohibited actions (refused), unanswerable questions.
- **Not handled:** Simultaneous requests, non-English queries, malicious file uploads, very long inputs (500-character limit enforced in `src/guardrails/`).