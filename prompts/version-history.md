# Prompt Version History

| Version  | Date        | Author | Changes                                                       | Reason                                                |
| :------- | :---------- | :----- | :------------------------------------------------------------ | :---------------------------------------------------- |
| **v1.0** | 7 Sept 2026 | Louis  | Initial prompt                                                | Baseline setup                                        |
| **v1.1** | 9 Sept 2026 | Louis  | Added scope constraints, tone guidance, and refusal templates | Fix out-of-scope leakages & injection vulnerabilities |
| **v2.0** | 15 Sept 2026 | Louis  | Added RAG context section, source citation requirement, "only use context" constraint, explicit failure behaviour for missing information | Integrating RAG pipeline requires prompt to use retrieved documents and cite sources |
| **v2.1** | 17 Sept 2026 | Louis  | Added critical constraint block forbidding use of training data; strengthened "no guessing" language after hallucination risk found in review | RAG review identified a hallucination risk when context lacked a direct answer (see docs/rag-review-notes.md) |
| **v4.0** | 5 Oct 2026 | Louis | Added memory context section, check_ticket_status action, and memory rules (assistive only) | Week 6 adds persistent memory; prompt must respect boundaries |
| **v4.1** | 7 Oct 2026 | Louis | Added memory_context placeholder, "how to use memory" section, memory boundaries (assistive only), check_ticket_status in available actions | Memory integration requires explicit handling rules |

### Outcome

Prompt `v1.1` passed **9/10** test cases and is selected as the baseline prompt for Week 3 RAG integration.
