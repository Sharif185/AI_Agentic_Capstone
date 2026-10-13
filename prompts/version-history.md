# Prompt Version History

| Version  | Date        | Author | Changes                                                       | Reason                                                |
| :------- | :---------- | :----- | :------------------------------------------------------------ | :---------------------------------------------------- |
| **v1.0** | 7 Sept 2026 | Louis  | Initial prompt                                                | Baseline setup                                        |
| **v1.1** | 9 Sept 2026 | Louis  | Added scope constraints, tone guidance, and refusal templates | Fix out-of-scope leakages & injection vulnerabilities |
| **v2.0** | 15 Sept 2026 | Louis  | Added RAG context section, source citation requirement, "only use context" constraint, explicit failure behaviour for missing information | Integrating RAG pipeline requires prompt to use retrieved documents and cite sources |
| **v2.1** | 17 Sept 2026 | Louis  | Added critical constraint block forbidding use of training data; strengthened "no guessing" language after hallucination risk found in review | RAG review identified a hallucination risk when context lacked a direct answer (see docs/rag-review-notes.md) |
| **v3.0** | 24 Sept 2026 | Louis  | Added tool orchestration — AVAILABLE TOOLS section, TOOL SELECTION GUIDELINES, tool result handling in output format; added `create_support_ticket` and `get_course_info` | Week 4 agent tool calling requires prompt to specify available tools and selection criteria |
| **v4.0** | 5 Oct 2026   | Louis  | Added MEMORY CONTEXT: `{session_context}` placeholder; added `check_ticket_status` to AVAILABLE TOOLS; added MEMORY RULES section (assistive only, never control grades/fees); explicit boundary: memory never overrides current session | Week 6 adds persistent memory — prompt must declare memory context, expose the new tool, and enforce usage boundaries |
| **v4.1** | 7 Oct 2026   | Louis  | Replaced `{session_context}` with `{memory_context}` (explicit name); added HOW TO USE MEMORY section with concrete rules for multi-ticket disambiguation; added MEMORY BOUNDARIES block with stale-ticket handling; clarified all four tool selection conditions for `check_ticket_status` | Memory integration requires explicit, concrete handling rules for the agent to use memory correctly without over-relying on it |

---

### Version Outcomes

| Version | Tests Passed | Notes |
|---------|-------------|-------|
| v1.0 | 7/10 | Baseline; out-of-scope issues |
| v1.1 | 9/10 | Selected as Week 3 baseline |
| v2.0 | RAG integrated | Source citation + context constraint |
| v2.1 | Hallucination risk fixed | No-guessing language strengthened |
| v3.0 | Week 4 tool calling | Two tools exposed via prompt |
| v4.0 | Week 6 memory design | Memory context + boundaries (Day 1) |
| v4.1 | Week 6 memory integration | Concrete memory rules + disambiguation (Day 3) |

---

### Prompt Files

| Version | File |
|---------|------|
| v1.0 | `prompts/system-prompt-v1.0.txt` |
| v1.1 | `prompts/system-prompt-v1.1.txt` |
| v2.0 | `prompts/system-prompt-v2.0.txt` |
| v2.1 | `prompts/system-prompt-v2.1.txt` |
| v3.0 | `prompts/system-prompt-v3.0.txt` |
| v4.0 | `prompts/agent-system-prompt-v4.0.txt` |
| v4.1 | `prompts/agent-system-prompt-v4.1.txt` |
