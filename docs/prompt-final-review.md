# Final Prompt Review

Date: 19th October 2026  |  Reviewer: Louis (AI Engineering Lead)

## 1. Prompt Version History
| Version | Date | Key Change | Evidence |
|---|---|---|---|
| v1.0 | 7 Sept | Initial baseline | 7/10 test cases |
| v1.1 | 9 Sept | Added scope constraints, tone, refusal templates | 9/10 test cases |
| v2.0 | 15 Sept | RAG integration, source citation | Week 3 RAG run: 15/15 outcomes met (docs/rag-review-notes.md) |
| v2.1 | 17 Sept | Strict grounding (no training-data fallback) | Re-tested in validation pass |
| v3.0 | 24 Sept | Tool calling | Week 4 tool tests (tests/week4-recovery-test.md) |
| v4.0 | 5 Oct | Memory context | Week 6 memory tests |
| v4.1 | 7 Oct | Memory boundaries, multi-ticket disambiguation | Week 6 memory tests |
| v5.0 | 13 Oct | Injection defenses, prohibited-action refusals | Week 7 evaluation, 34 scenarios |

## 2. Where the Prompt Lives
The versioned prompt files in `prompts/` serve as the design record. At runtime, the model sees `PLANNING_PROMPT_TEMPLATE` in `src/agent/planner.py`, which carries identical safety rules.

## 3. Current Prompt (v5.0) Assessment
| Aspect | Status | Notes |
|---|---|---|
| Role definition | Clear | "bounded student support agent" |
| Task description | Specific | Answer, tools, memory |
| Constraints | Explicit | Prohibited actions listed |
| Output format | Enforced | Single JSON decision |
| Failure behaviour | Defined | "I don't have that information" |
| Safety rules | Added | Prompt injection, prohibited actions |
| Memory rules | Added | Assistive only; current session wins |

## 4. Agent Behaviour Assessment
Source: `evaluation/results/week7-results-final.json` (34 scenarios).

| Behaviour | Result | Evidence |
|---|---|---|
| Stays in role | Yes | Adversarial scenarios A-01 to A-05 refused |
| Uses correct tool | 91% selection | Tool-selection metric |
| Cites sources | Yes | Groundedness 98% |
| Stops safely | Yes | 5 stop conditions, avg 2.1 iterations |
| Handles failures | Yes | T-01 to T-04, recovery tested |
| Respects memory | Yes | Assistive only; check_ticket_status |
| Safety violations | 0 | Unauthorized scenarios U-01 to U-04 |

## 5. Recommendations for Final Release
1. Keep v5.0 as the production prompt.
2. Document known edge cases in `docs/known-limitations.md`.
3. Add 2 to 3 example interactions to the README.