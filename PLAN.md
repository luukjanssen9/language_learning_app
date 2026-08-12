# PLAN.md

Living project plan and status log. Read at the start of every session; update Current Status before ending one.

## Phase checklist

- [~] **Phase 0 — Setup & planning**: clarifying questions, repo scaffolding,
  `PLAN.md` created, Docker Compose skeleton.
- [ ] **Phase 1 — Data model & backend foundation**: language-agnostic schema
  (proposed for review first), FastAPI + Postgres + SQLAlchemy + Alembic
  wired up, basic CRUD endpoints. (No auth — v1 is single-user.)
- [ ] **Phase 2 — Spaced repetition engine**: FSRS scheduling implemented,
  review endpoint + due-card queue logic, unit tests for scheduling edge
  cases.
- [ ] **Phase 3 — Frontend foundation**: Next.js + TypeScript + Tailwind
  scaffold (mobile-first), deck/card management UI, review session UI (flip
  card, rate recall, keyboard shortcuts). Visual style options proposed
  before build.
- [ ] **Phase 4 — Structured lessons**: lesson/skill data model, seed starter
  English→Spanish course content, exercise UI (multiple choice, translation,
  fill-in-blank). Minimal gamification only (progress/mastery tracking, no
  streak/XP UI in v1).
- [ ] **Phase 5 — Core AI/NLP features**: LLM service layer (provider-agnostic,
  Gemini default), example generation, free-text grading, auto-card-generation,
  mnemonics, adaptive weak-point targeting.
- [ ] **Phase 6 — Conversational practice partner**: chat UI, roleplay
  scenarios constrained to known vocabulary, in-context correction.
- [ ] **Phase 7 — Speech (stretch goal)**: Whisper integration, pronunciation
  comparison/feedback.
- [ ] **Phase 8 — Scalability check, polish & deploy**: add a second
  language's config to prove the architecture generalizes; performance/cost
  review; tests; deployment; final README with setup, architecture overview,
  screenshots/demo.

## Decisions Log

**2026-08-11 — Auth: single-user for v1, defer real multi-user auth.**
Chose fastest path to working core features (FSRS, lessons, AI) over building
login infra before any product exists. `User` table exists from Phase 1 so
adding real auth (JWT) later is additive, not a rewrite.

**2026-08-11 — LLM provider: Google Gemini (free tier) as default, behind a
provider-agnostic service layer.** No Anthropic API key on hand yet, and
Gemini's free tier (Google AI Studio) requires no billing setup, unlike
Anthropic. Two-tier split: `gemini-3.1-flash-lite` for high-volume/low-
complexity calls, `gemini-3.5-flash` for higher-reasoning calls (mirrors the
originally-planned Haiku/Sonnet split). Interface is swappable via
`LLM_PROVIDER` env var so Claude (or another provider) can be dropped in
later without a rewrite. Verified 2026-08-11 via ai.google.dev: Pro models
were removed from the free tier in April 2026, so only Flash-family models
are free — re-verify model names/limits before Phase 5, they shift.

**2026-08-11 — Gamification: minimal in v1.** Per-skill mastery/progress
tracking only; no streak or XP UI. Keeps Phase 4 scope on lesson content and
exercise types rather than engagement mechanics; schema can reserve fields
for streak/XP later without a migration rewrite.

**2026-08-11 — UI: mobile-first.** Both Anki and Duolingo are heavily used on
mobile; building mobile-first from Phase 3 avoids a bolted-on responsive pass
at the end.

**2026-08-11 — Deployment target (tentative, finalized in Phase 8): Vercel
(frontend) + Railway or Fly.io (backend + Postgres).** The initial recommendation,
accepted — low ops overhead, resume-legible stack.

**2026-08-11 — Visual style: propose options before building.** Before Phase 3
UI work, present 2-3 direction options (palette/tone) for approval rather than
picking unilaterally.

**2026-08-11 — Working cadence: checkpoint at end of each phase.** Summarize,
update this file, and wait for go-ahead before starting the next phase.

**2026-08-11 — SRS algorithm: FSRS**, per original brief — modern,
better-validated successor to SM-2. Implement from the published spec
(`open-spaced-repetition` GitHub org) or a well-maintained Python package if
one fits cleanly; decide concretely in Phase 2.

## Current Status

**As of 2026-08-11:**

- Done: clarifying questions answered (see Decisions Log); repo scaffolded —
  `.gitignore`, `.env.example`, `LICENSE` (MIT), `README.md`,
  `PLAN.md`, `docker-compose.yml` (Postgres service live; backend/frontend
  services stubbed/commented until their Dockerfiles exist).
- In progress: finishing Phase 0 — still need `git init` + first commit, and
  the concrete data model proposal for Phase 1 (to be shown for review before
  implementation starts).
- Next: propose concrete data model (User, Language, Deck, Card/CardType,
  ReviewLog, LessonUnit/Skill, LessonExercise, UserProgress) → once approved,
  start Phase 1 (FastAPI + SQLAlchemy + Alembic + Postgres wiring, CRUD
  endpoints).
- Open questions: none blocking. LICENSE copyright line uses a placeholder
  name ("language_app project author") — replace with the user's actual name
  whenever they want it personalized.

## Known Issues / Follow-ups

- Gemini free-tier rate limits are tight (~10-15 req/min depending on model,
  as of 2026-08) — revisit caching strategy seriously in Phase 5, especially
  for the conversational practice partner (Phase 6), which will burn requests
  fastest.
- No Anthropic key yet — if/when one is added, confirm the provider-agnostic
  LLM layer actually swaps cleanly (this is a real test of that abstraction,
  not just a nice-to-have).
- LICENSE placeholder name needs personalizing before this becomes public-facing.
