# Model Selection Note

**Author:** Louis (AI Engineering Lead)
**Date:** 4th September 2026
**Status:** Week 1 Draft

## Purpose

Compare candidate foundation models for the University Student-Support Case Agent on cost, speed, and strengths, and recommend one for development.

## Models Compared

### 1. Gemini 1.5 Flash — CHOSEN
- **Strengths:** Fast, large context window (1M tokens — well beyond our planned 10–50 document corpus for Week 3 RAG), solid general-purpose reasoning
- **Cost:** Free tier available (generous request limits), low cost beyond that
- **Speed:** Average response time ~1–2 seconds
- **Access:** Free-tier API key from Google AI Studio — no course credits or payment needed to get started
- **Weakness:** Slightly less consistent reasoning on multi-constraint instructions (role + refusal + tone) than GPT-4o-mini in early testing — addressed via prompt iteration in Week 2 (v1.0 → v1.1)

Note: Gemini 1.5 Flash was selected as primary (not GPT-4o-mini) due to free-tier access with no course budget; this matches the model actually used in Week 2 testing (see tests/week2-evaluation-table.md).

### 2. GPT-4o-mini
- **Strengths:** Strong instruction-following and reasoning; good at structured output (JSON, tables); handles multi-turn conversation well; 128K context window
- **Cost:** $0.15 / 1M input tokens, $0.60 / 1M output tokens — estimated <$5/month during development
- **Speed:** Average response time 1–2 seconds
- **Role here:** Documented fallback if Gemini rate limits or availability become an issue

### 3. Claude 3.5 Haiku
- **Strengths:** Reliable instruction-following, strong safety behavior
- **Weakness:** Higher cost than GPT-4o-mini for this workload with no clear accuracy advantage for a support-agent task

### 4. Llama 3.1 (local, via Ollama)
- **Strengths:** Full data privacy — nothing leaves our machines
- **Weaknesses:** Requires 16GB+ RAM to run comfortably; slower inference (5–30s); adds deployment complexity for a live demo

## Recommendation

**Use Gemini 1.5 Flash as the primary model.** GPT-4o-mini is kept as a documented fallback option if Gemini rate limits or availability become an issue during evaluation. Llama 3.1 is kept as a documented local alternative in case data-privacy requirements tighten later, but is not needed for Week 1–2.

**Why:** Gemini 1.5 Flash has a generous free tier (useful for a student project with no budget), a large context window, and fast response times — a good fit for a support agent that needs to stay in role, refuse out-of-scope requests, and follow a strict output format. Its main tradeoff versus GPT-4o-mini is slightly less consistent handling of multi-constraint instructions, which is exactly what Week 2 prompt testing (v1.0 → v1.1) is designed to catch and fix.

## Next Steps

- Week 1: Confirm API key access and test connectivity (see `.env.example` and API test below)
- Week 2: Finalize this note with any adjustments from first prompt-testing results
