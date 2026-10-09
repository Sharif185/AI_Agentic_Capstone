# Agent Trace Analysis

Date: 1st October 2026  |  Reviewer: Louis (AI Engineering Lead)

## Trace 1 Analysis
Goal: "I want to register for BSE4104. What do I need?"

- Agent correctly identified the goal and planned two complementary steps:
  rag_retrieve for the registration procedure, then get_course_info for
  the actual prerequisite list.
- Tool selection was appropriate — combined document knowledge (procedure)
  with structured data (prerequisites) rather than relying on just one.
- Stopped immediately after the goal was achieved (3 iterations, no
  wasted steps). stop_reason: goal_achieved.
- No improvements needed.

## Trace 2 Analysis
Goal: "What are the prerequisites for XYZ999?" (non-existent course)

- Agent handled a tool failure gracefully: get_course_info correctly
  returned "No course found with code 'XYZ999'" rather than erroring out.
- Recovery path worked as designed: tried rag_retrieve as a fallback
  before escalating (0 results — the course genuinely doesn't exist
  anywhere in the corpus), then created a support ticket.
- Approval gate functioned correctly — human_approvals recorded the
  ticket creation as explicitly approved before it was created.
- Improvement: minor only. For a course code this clearly invalid, the
  RAG fallback was always going to return 0 results — it added an
  iteration without changing the outcome. Not a bug, just a possible
  efficiency gain: skip the RAG step when the tool error indicates the
  course code doesn't exist at all (vs. a tool error that might be
  recoverable via document search).

## Trace 3 Analysis
Goal: "I have a problem." (vague, no specifics)

- Agent did NOT detect lack of progress on the first attempt. It issued
  the identical rag_retrieve query ("student problem general help")
  twice in a row (iterations 1 and 2), got the identical generic result
  both times, then stopped.
- This directly violates a rule stated in the agent's own system prompt:
  "Do NOT repeat an action you've already taken with the same
  arguments." The rule exists in the prompt but was not followed here —
  it is not enforced anywhere in code.
- The eventual outcome was reasonable (stopped after 2 iterations rather
  than running to the 5-iteration cap, and asked the student for more
  detail or a human handoff) — but it got there inefficiently, burning
  a full RAG call on a repeat query first.
- Improvement: ask for clarification immediately when the goal is vague
  (iteration 1), instead of attempting a search at all. Separately,
  enforce the no-repeat-action rule programmatically — this trace shows
  the model doesn't reliably self-police it from prompt text alone.

## Recommendations
1. **Add a clarification step.** When the goal is vague (short, no
   specifics — e.g. "I have a problem"), use `answer` to ask a
   clarifying question on iteration 1, rather than attempting
   rag_retrieve first.
2. **Enforce no-repeat-action at the code level.** Trace 3 shows the
   prompt-only rule isn't reliable. The Planner or orchestrator should
   check `state.history` for an identical `(action, arguments)` pair
   before calling the model, and skip/block the repeat rather than
   relying on the model to self-enforce it.
3. **Optional efficiency tweak:** for tool errors that clearly indicate
   a non-existent entity (e.g. "No course found with code X"), consider
   skipping the RAG fallback and escalating to a ticket directly. Not
   urgent — current behavior is correct, just slightly wasteful.

Implementation: items 1 and 2 will be added to prompt v3.1 and the
Planner's pre-flight check in Week 6.