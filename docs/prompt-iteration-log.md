# Prompt Iteration Log

## Iteration 1: v1.0 -> v1.1

Date: 8-9 September 2026
Author: Louis (AI Engineering Lead)

Trigger: First round of 10 test cases revealed:

1. Out-of-scope questions (TC-003) were sometimes answered
2. Grade-change requests (TC-004) were not firmly refused
3. Prompt injection (TC-009) partially succeeded
4. Tone was inconsistent

Changes Made:

- Added "ONLY discuss university-related topics" constraint
- Added explicit redirect script for out-of-scope questions
- Added specific refusal template for grade/record requests
- Added tone guidance section
- Added output format examples

Expected Impact:

- 100% refusal of out-of-scope questions
- 100% refusal of grade-change requests
- Consistent professional tone

Verification: Re-ran all 10 test cases with v1.1

- TC-003: Now redirects correctly
- TC-004: Now refuses clearly
- TC-009: Now stays in role

Next Steps:

- Use v1.1 for Week 3 RAG integration
- Test again when documents are added

### Outcome

Prompt `v1.1` passed **9/10** test cases and is selected as the baseline prompt for Week 3 RAG integration.
