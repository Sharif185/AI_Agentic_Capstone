## Presentation Slides Outline

| Slide                             | Time      | Content                                                                                                                                                             |
| :-------------------------------- | :-------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **1. Title**                      | 30s       | Project name, team, course, date                                                                                                                                    |
| **2. Problem**                    | 1–2m      | What students struggle with; our solution; why AI                                                                                                                   |
| **3. Architecture**               | 2m        | Architecture diagram, key components, progression Model➔RAG➔Tools➔Agent➔Evaluation                                                                                  |
| **4. Live Demo**                  | 4m        | RAG question, tool call, multi-step + approval, memory, adversarial refusal, prohibited-action refusal                                                              |
| **5. Engineering Evidence**       | 2m        | A retrieval, tool, or agent-decision trace; “every decision is logged and inspectable”                                                                              |
| **6. Evaluation Results**         | 1m        | 94% completion, 98% groundedness, 91% tool selection, 0 safety violations, 4.2s latency; 34 scenarios                                                               |
| **7. Failure & Recovery**         | 2m        | Real failure A-02 (prompt injection), root cause, fix, re-test — “every rule must be explicit”                                                                      |
| **8. Guardrails & Human Control** | 1–2m      | 4 guardrails table; human control points (approval, prohibited refusals, bounded iterations, full traces)                                                           |
| **9. What We Learned**            | 1m        | Bounded autonomy works; evaluation is essential; prompts are code; guardrails are layered; memory must be justified                                                 |
| **10. Limitations & Future Work** | 1m        | 15 docs, CLI only, English only, synthetic data ➔ expand corpus, web UI, authentication, real integration                                                           |
| **11. Conclusion**                | 30s       | 94% completion, 0 safety violations, full observability, honest documentation; “build the smallest useful agentic system you can test, explain, and safely control” |
| **12. Questions**                 | remaining | Backup slides: architecture detail, prompt history, evaluation detail, failure catalogue, memory design                                                             |

## Team Speaking Assignment

| Member     | Time  | Slides | Topic                 |
| :--------- | :---- | :----- | :-------------------- |
| **Sharif** | 2 min | 1–2    | Problem + Solution    |
| **Mus**    | 3 min | 3      | Architecture          |
| **Mus**    | 4 min | 4      | Live Demo             |
| **Imaan**  | 2 min | 5–6    | Evidence + Evaluation |
| **Louis**  | 2 min | 7–8    | Failure + Guardrails  |
| **Noah**   | 2 min | 9–10   | Lessons + Limitations |
| **Sharif** | 1 min | 11     | Conclusion            |
