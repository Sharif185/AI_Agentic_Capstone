# Prompt Version History

| Version  | Date        | Author | Changes                                                       | Reason                                                |
| :------- | :---------- | :----- | :------------------------------------------------------------ | :---------------------------------------------------- |
| **v1.0** | 7 Sept 2026 | Louis  | Initial prompt                                                | Baseline setup                                        |
| **v1.1** | 9 Sept 2026 | Louis  | Added scope constraints, tone guidance, and refusal templates | Fix out-of-scope leakages & injection vulnerabilities |
| **v2.0** | 15 Sept 2026 | Louis  | Added RAG context section, source citation requirement, "only use context" constraint, explicit failure behaviour for missing information | Integrating RAG pipeline requires prompt to use retrieved documents and cite sources |
| **v2.1** | 17 Sept 2026 | Louis  | Added critical constraint block forbidding use of training data; strengthened "no guessing" language after hallucination risk found in review | RAG review identified a hallucination risk when context lacked a direct answer (see docs/rag-review-notes.md) |

### Outcome

Prompt `v1.1` passed **9/10** test cases and is selected as the baseline prompt for Week 3 RAG integration.
