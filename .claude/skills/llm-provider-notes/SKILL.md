---
name: llm-provider-notes
description: Reference for this project's LLM provider setup (Gemini default, model-tier split, rate limits, caching strategy). Load before working on Phase 5 (core AI/NLP features) or any Gemini/LLM-integration code.
---

# LLM provider notes

- Default provider is **Gemini** (free tier, no billing setup required).
  Anthropic Claude remains a supported provider behind the same interface —
  swap via the `LLM_PROVIDER` env var, not code changes, if a paid key is
  added later.
- Two-tier model split (mirrors Claude's Haiku/Sonnet split):
  - **Fast/cheap** (`gemini-3.1-flash-lite`): example sentences, short-answer
    grading, mnemonics — high-volume, low-complexity calls.
  - **Reasoning** (`gemini-3.5-flash`): conversational practice partner,
    nuanced grading with explanations — longer-context/higher-reasoning calls.
  - Model names above are current as of 2026-08; re-check
    `ai.google.dev/gemini-api/docs/pricing` before relying on them, they shift.
- Free-tier rate limits are tight (roughly 10-15 requests/min depending on
  model as of 2026-08 — verify at `ai.google.dev/gemini-api/docs/rate-limits`
  before building Phase 5). Cache generated content (e.g. example sentences
  for a given word/level) and be deliberate about call frequency.
- Free-tier prompts/responses may be used by Google to improve their
  products (paid tier opts out). Noted in the README as a known trade-off.
- Use structured output / tool-use for anything the app parses programmatically
  (grading results, extracted vocabulary lists) — never parse free text.
