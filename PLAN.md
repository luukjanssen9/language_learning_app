# PLAN.md

Living project plan and status log. Read at the start of every session; update Current Status before ending one.

## Phase checklist

- [x] **Phase 0 — Setup & planning**: clarifying questions, repo scaffolding,
  `PLAN.md` created, Docker Compose skeleton.
- [x] **Phase 1 — Data model & backend foundation**: language-agnostic schema
  (proposed for review first), FastAPI + Postgres + SQLAlchemy + Alembic
  wired up, basic CRUD endpoints. (No auth — v1 is single-user.) Code
  complete and verified end-to-end against a live Postgres instance.
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

**2026-08-12 — Data model finalized (13 tables), implemented as SQLAlchemy
2.0 models in `backend/app/models/`.** Core entities: `Language`, `Course`
(base/target language pairing), `User`, `UserCourse` (enrollment), `Deck`,
`VocabularyItem` (shared dictionary entry between flashcards and lessons),
`Card` (FSRS scheduling state lives on the row), `ReviewLog` (append-only
history), `Skill`, `LessonExercise` (+ `LessonExerciseVocabulary` join),
`UserProgress`, `UserExerciseAttempt`. Matches the proposal approved in
conversation; see model docstrings for per-entity rationale.

**2026-08-12 — Primary keys: client-generated UUIDv4 (Python `uuid.uuid4`),
not a Postgres extension.** Avoids depending on `pgcrypto`/`uuid-ossp` just
to get `gen_random_uuid()`; IDs are known before insert, which is convenient
for tests and for building relations in a single request.

**2026-08-12 — Enum columns stored as plain VARCHAR (`native_enum=False`),
not Postgres native enum types**, via a shared `pg_enum()` helper in
`app/models/enums.py`. Adding a new enum member later is then a normal
migration, not an `ALTER TYPE ... ADD VALUE` (which has its own transactional
restrictions in Postgres). The helper also forces `values_callable` so the
DB stores the enum's lowercase `.value` (e.g. `"target_to_base"`) rather than
SQLAlchemy's default of the uppercase `.name` — worth knowing if a future
migration is autogenerated and the diff looks unexpected.

**2026-08-12 — Migrations are applied manually (`alembic upgrade head`), not
run automatically on container startup.** Keeps the backend container's job
to just "serve the API"; avoids surprise concurrent migration runs if the
service ever scales beyond one instance (relevant once Phase 8 picks a real
host). Documented as a manual step in this project's "How to run" notes.

**2026-08-12 — pytest suite shares a single session-scoped asyncio event
loop (`asyncio_default_fixture_loop_scope` / `asyncio_default_test_loop_scope
= "session"` in `backend/pyproject.toml`), rather than pytest-asyncio's
default of one loop per test.** First live-DB run of the suite failed 6/8
tests with `asyncpg.exceptions.InterfaceError: cannot perform operation:
another operation is in progress`. Root cause: `app/database.py`'s `engine`
is a module-level singleton whose connection pool is created once, but
pytest-asyncio's default per-test event loop meant a pooled asyncpg
connection opened under one test's loop was later checked out and reused
under a *different* test's (new) loop — asyncpg connections aren't valid
across event loops. Sharing one event loop for the whole session keeps the
pool's connections valid throughout; `db_session` itself stays
function-scoped (fresh transaction/SAVEPOINT per test), so test isolation is
unaffected. Standard fix for this exact SQLAlchemy-async-engine + pytest-
asyncio combination.

## Current Status

**As of 2026-08-12:**

- Done: Phase 0 fully wrapped (LICENSE personalized, repo committed). Data
  model proposal approved and implemented — **Phase 1 backend is complete
  and verified end-to-end**: Docker Desktop installed (WSL2 backend),
  `docker compose up -d postgres` → `--build backend` →
  `alembic upgrade head` all ran clean against a live Postgres instance, and
  the full pytest suite (8/8) passes against it. (Fixed one real bug
  surfaced by this first live run — see the 2026-08-12 pytest event-loop-
  scope decision log entry.) Earlier code-complete work:
  - `backend/` scaffolded (`pyproject.toml`, `Dockerfile`, Python 3.12).
  - 13 SQLAlchemy 2.0 async models across `app/models/`, all indexed on FK
    columns, mappers verified to configure cleanly.
  - Alembic wired for async migrations (`alembic/env.py` reads
    `DATABASE_URL` from `app.config.settings`); initial migration
    (`1d5df3c16c8d_initial_schema.py`) written and verified via
    `alembic upgrade head --sql` / `alembic downgrade ... --sql` (offline
    mode — compiles real Postgres DDL without needing a live connection),
    cross-checked against DDL generated directly from the model metadata.
  - Pydantic schemas + CRUD routers for 9 resources (full CRUD on 8; Create
    +List+Get+Delete on `UserCourse`) plus read-only list/get on 3 resources
    whose rows are written by later-phase domain logic (`ReviewLog`,
    `UserProgress`, `UserExerciseAttempt`) — 25 routes total, confirmed via
    the generated OpenAPI schema.
  - `docker-compose.yml` backend service wired (with a `DATABASE_URL`
    override so the container reaches Postgres via the `postgres` service
    name rather than `localhost`).
  - pytest suite (health check + CRUD + a full cross-entity integration
    flow + FK-conflict/409 cases). Verified as far as possible without a
    live DB: the health test passes end-to-end; the DB-dependent tests fail
    at exactly the expected connection point, confirming the fixtures and
    dependency-override wiring are correct.
  - ruff clean across the whole backend (`ruff check .`).
- Blocked: nothing — the prior Docker blocker is resolved (see Decisions Log).
- Next: proceed to Phase 2 (FSRS scheduling engine).
- Open questions: none blocking.

## Known Issues / Follow-ups

- Gemini free-tier rate limits are tight (~10-15 req/min depending on model,
  as of 2026-08) — revisit caching strategy seriously in Phase 5, especially
  for the conversational practice partner (Phase 6), which will burn requests
  fastest.
- No Anthropic key yet — if/when one is added, confirm the provider-agnostic
  LLM layer actually swaps cleanly (this is a real test of that abstraction,
  not just a nice-to-have).
- The pytest suite doesn't use a separate test database — each test wraps in
  a transaction/SAVEPOINT that's rolled back afterward (see
  `backend/tests/conftest.py`), so it's safe to run against the same
  `DATABASE_URL` as dev. Revisit if that ever becomes a problem (e.g. tests
  needing to run concurrently with manual dev work against the same DB).
- No CORS middleware on the backend yet — deferred until Phase 3 actually
  stands up the Next.js frontend and its dev-server origin/port are known.
- `Card.due_at` has an index (due-card queries will filter on it), but no
  composite index yet — revisit once Phase 2 defines the actual due-card
  query shape (likely `deck_id` + `due_at` together).
