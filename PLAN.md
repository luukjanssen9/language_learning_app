# PLAN.md

Living project plan and status log. Read at the start of every session; update Current Status before ending one.

## Phase checklist

- [x] **Phase 0 — Setup & planning**: clarifying questions, repo scaffolding,
  `PLAN.md` created, Docker Compose skeleton.
- [x] **Phase 1 — Data model & backend foundation**: language-agnostic schema
  (proposed for review first), FastAPI + Postgres + SQLAlchemy + Alembic
  wired up, basic CRUD endpoints. (No auth — v1 is single-user.) Code
  complete and verified end-to-end against a live Postgres instance.
- [x] **Phase 2 — Spaced repetition engine**: FSRS scheduling implemented
  (official `fsrs` package), review endpoint + due-card queue logic, unit
  and integration tests for scheduling edge cases. Code complete and
  verified end-to-end against a live Postgres instance.
- [x] **Phase 3 — Frontend foundation**: Next.js + TypeScript + Tailwind
  scaffold (mobile-first), deck/card management UI, review session UI (flip
  card, rate recall, keyboard shortcuts). Visual style ("Quiet Focus") and
  layout ("Unified Dashboard") proposed and approved before build. Code
  complete and verified end-to-end in a real browser against the live API.
- [ ] **Phase 4 — Structured lessons**: lesson/skill data model, seed starter
  English→Spanish course content, exercise UI (multiple choice, translation,
  fill-in-blank). Minimal gamification only (progress/mastery tracking, no
  streak/XP UI in v1). Also planned: a dedicated conjugation-practice mode
  (drilling verb forms across tenses/moods) plus Spanish subjunctive practice
  specifically — both conjugation *and* when to use it — as a deliberate
  differentiator from Duolingo, which doesn't teach subjunctive well. Real
  design questions to resolve before building this — see the Known Issues /
  Follow-ups note below, added 2026-08-13.
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

**2026-08-13 — Visual style chosen: "Quiet Focus."** Calm/warm/editorial —
Fraunces (display) + Hanken Grotesk (body/UI), a soft putty background with a
single deep-sage accent, no bright gamified palette. Picked over two other
proposed directions ("Bright Momentum" — energetic, Duolingo-adjacent
colorful; "Quiet Precision" — dark-mode, technical) specifically because it's
the one that actually matches the 2026-08-11 minimal-gamification decision —
the other two either fought that choice (Bright Momentum) or read as
portfolio-flex-first rather than daily-study-first (Quiet Precision).

**2026-08-13 — Home-screen layout chosen: "Unified Dashboard."** Due-count
and the deck list live on one screen together, decks get inline progress
bars — rather than a single dominant "start review" CTA with decks
secondary ("Study First"), or decks-as-the-home-screen with no separate due
summary ("Deck Browser," closest to Anki's own layout). Picked specifically
because it's the only one of the three with an obvious place for Phase 4's
lesson path to slot into later (another section on the same dashboard)
without a home-screen redesign. The review session itself (flip card, rate,
keyboard shortcuts) doesn't vary by this choice — it's minimal by design,
already fully specified by this phase's own scope.

**2026-08-13 — After finishing any frontend section, ask specific review
questions** (what to change, or confirm it's right) rather than a generic
"let me know what you think" — point at the actual judgment calls made
while building it.

**2026-08-13 — Single-user/course bootstrap is silent, client-side, and
idempotent** (`frontend/src/lib/bootstrap.ts`). No auth in v1 means nothing
creates the one `User`/two `Language`s/one `Course` row everything else
foreign-keys against — on app load, the frontend checks via the list
endpoints and creates only whichever are missing, caching the result in
`localStorage`. Matches "single-user, assumed" literally: no signup/setup
screen ever shown. One `GET /users/{id}` revalidates the cache on every
load before trusting it — a direct response to this project's own history
(the dev Postgres volume gets reset/wiped across sessions; a stale cached
`userId` would otherwise 409 every deck/card creation for a confusing
reason). Verified live: reused the pre-existing `en` Language and the
pre-existing dev-testing user, created `es` and the `en-es` Course fresh,
zero duplicates on reload.

**2026-08-13 — Frontend dev workflow is native (`npm run dev`), not
Docker**, despite `docker compose` being the norm for the backend. Two
concrete reasons from this project's own history: Docker Desktop/WSL2
instability earlier this session (disk-full, backend crashes), and
Windows' well-known slow bind-mount performance for `node_modules`/hot
reload. `frontend/Dockerfile` and a `frontend` service in root
`docker-compose.yml` still exist for parity/completeness (config validated
via `docker compose config`), but aren't the verified day-to-day path.

**2026-08-13 — Deck progress bars use a proxy metric** (share of a deck's
cards not in `"new"` state), computed client-side, not real mastery
scoring — no `UserProgress`/mastery data exists for decks yet (that table
is `Skill`-scoped, Phase 4 territory), and this doesn't factor in FSRS's
own stability-based recall-strength signal. Revisit with a real metric
once Phase 4 or a backend aggregate makes one available.

**2026-08-13 — `dueCards` and `cards` are sibling TanStack Query keys, not
nested.** `["decks", id, "due-cards"]`, not `["decks", id, "cards", "due"]`.
TanStack Query's `invalidateQueries` matches by key *prefix* — nesting
would mean invalidating `cards` after a review (to refresh card-management
and dashboard progress bars) also silently refetches the due-queue a
review session is actively iterating over, reshuffling or dropping cards
mid-session as ratings reschedule them server-side. The due queue is
fetched once per session (`staleTime: Infinity`) and advanced through with
local state instead.

**2026-08-13 — `GET /api/cards` gained an optional `deck_id` filter**
(backward compatible — omitted, it still returns everything). Phase 1
never needed "all cards in one deck" as its own query; Phase 3's
card-management page does. Small additive backend change alongside the
CORS middleware Phase 3 also required (`app/config.py`'s new
`frontend_origin` setting, `allow_credentials=False` since there's no
auth/cookies to protect).

**2026-08-13 — `next dev`/Next.js 16 auto-generates `AGENTS.md` inside
`frontend/`, regenerated on every dev-server start** — framework-specific
guidance for AI coding assistants, not project documentation. Gitignored
(a bare filename entry under "Editors / OS" in `.gitignore`, no
explanatory comment) rather than deleted, since deleting would just have
it silently reappear on the next `npm run dev`.

**2026-08-13 — Frontend toolchain has three version-compatibility pins,
each hit and fixed live, not preemptively guessed:** `vite` pinned to `^7`
(Vite 8 defaults to the Rolldown bundler, which needs a native binding this
machine's Node 20.13 — below Rolldown's ^20.19 floor — can't load);
`@vitejs/plugin-react` pinned to `4.7.0` specifically (the first version
with a Vite 7 peer range; the version npm resolved by default only
supported Vite 8); `jsdom` pinned to `25` (jsdom 30's dependency chain pulls
in an ESM-only package that fails to load under this same Node version).
`vitest.config.ts` also had to become `vitest.config.mts` (forces ESM
loading for that one file regardless of the rest of the project's CommonJS
default) so `@vitejs/plugin-react` — itself ESM-only — could load at all.
None of this affects the actual app (Next.js's own Turbopack pipeline was
unaffected throughout) — purely a `vitest`/`vite` toolchain issue. Revisit
these pins if the dev machine's Node version is ever upgraded past 20.19.

**2026-08-11 — Working cadence: checkpoint at end of each phase.** Summarize,
update this file, and wait for go-ahead before starting the next phase.

**2026-08-11 — SRS algorithm: FSRS**, per original brief — modern,
better-validated successor to SM-2. Implement from the published spec
(`open-spaced-repetition` GitHub org) or a well-maintained Python package if
one fits cleanly; decide concretely in Phase 2.

**2026-08-12 — Phase 2 decided: use the official `fsrs` PyPI package
(`fsrs>=6.3,<7`)** rather than hand-implementing the FSRS memory-model math.
MIT-licensed, maintained by the `open-spaced-repetition` GitHub org itself,
currently FSRS-6. Verified directly against the library's source (not just
its docs) before committing to this: its `State` enum has only
Learning/Review/Relearning — no equivalent to our own `CardState.NEW`, which
stays a purely app-level "never reviewed" marker with no library counterpart.
Upper-bounded below FSRS-7 deliberately: unlike this project's other
open-ended pins, a future major version would carry different scoring-model
semantics, not just an API change — an unpinned upgrade could silently
reschedule every card differently.

**2026-08-12 — First business-logic module: `backend/app/services/`,
starting with `fsrs_engine.py`.** Until Phase 2 the codebase only had
`api/`/`models`/`schemas` plus one CRUD helper — this establishes the
service-layer pattern Phase 5's planned LLM layer will likely follow too.
It's the only module that imports the `fsrs` package directly; routers never
touch the library's types. `Card.step` (the library's same-day
learning-step counter) was added to the schema so this round-trips the
library's full card state faithfully rather than losing precision between
requests.

**2026-08-12 — `cards`' standalone `deck_id` index replaced with a composite
`(deck_id, due_at)` index**, resolving the "no composite index yet" Known
Issue from Phase 1. The due-card queue's actual query shape filters both
together; the composite still serves plain `deck_id`-only lookups as a
leading-column prefix, so keeping the old single-column index alongside it
would only add write overhead for no query-planning benefit.

**2026-08-12 — `POST /cards/{id}/review` accepts an optional client-supplied
`reviewed_at`**, not just "now". Justified beyond test convenience (though it
is what makes the default 1-/10-minute learning steps testable without
real-time sleeps in CI): the FSRS scheduler itself already treats the review
timestamp as a public parameter, and backdating a review has a real product
shape too (logging a review done offline/on paper). Guarded against misuse
given no auth exists yet: rejected if in the future or before the card's
previous review.

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

**As of 2026-08-13:**

- Done: **Phase 3 frontend is complete and verified end-to-end, in a real
  browser against the live API** (not just type-checked/unit-tested).
  Next.js 16 (App Router, TypeScript, Turbopack) + Tailwind v4, scaffolded
  natively. "Quiet Focus" visual identity (Fraunces + Hanken Grotesk fonts
  via `next/font/google`, tokens as Tailwind v4 `@theme inline` custom
  properties) and "Unified Dashboard" layout, both proposed as 2-3 options
  and approved before building — see the decision log. Three real pages:
  the dashboard (due/new totals, per-deck progress bars, inline deck
  creation), deck detail (add/edit/delete cards, `front_override`/
  `back_override`/`direction`, no `VocabularyItem` required), and the
  review session (real 3D card flip via Tailwind v4's native transform
  utilities, keyboard shortcuts 1-4 + space, frozen due-queue advanced by
  local state, optimistic rating submission). A silent client-side
  bootstrap (`lib/bootstrap.ts`) handles the no-auth single-user/course
  problem. Verified live end-to-end via browser automation: created a
  deck, added two cards, ran a full review session (flip, rate via
  keyboard, both mouse and key paths), then confirmed in Postgres directly
  that FSRS state actually updated correctly (`hablar` rated Good →
  `learning`/step 1; `gato` rated Easy → graduated straight to `review`,
  11-day interval) and the dashboard's due/progress numbers updated after
  leaving the session. 12/12 frontend tests pass (Vitest + RTL), all 35
  backend tests still pass, `tsc --noEmit`/`eslint`/`ruff` all clean.
  Required two small backend additions alongside: CORS middleware and a
  `deck_id` filter on `GET /api/cards` (see decision log for both).
- Done: **Phase 2 backend is complete and verified end-to-end.** FSRS
  scheduling via the official `fsrs` package (`app/services/fsrs_engine.py`),
  `POST /api/cards/{id}/review` (runs one FSRS review, updates the card,
  writes a `ReviewLog` row, returns both), `GET /api/cards/due` (due-card
  queue: overdue cards ordered most-overdue-first, then a capped batch of
  NEW cards). New migration adds `cards.step` and the composite
  `(deck_id, due_at)` index. 33/33 tests pass (9 new pure unit tests against
  the service layer with no DB, 14 new integration tests through the live
  API, plus all of Phase 1's suite still green) against a live Postgres
  instance; ruff clean; manually smoke-tested through the running API too
  (create card → review it → confirm it's correctly excluded from the due
  queue until actually due). One pre-existing Phase 1 test
  (`test_create_and_get_language`) was fixed in passing — it hardcoded
  `"en"`, which collided with leftover data from earlier manual Swagger UI
  testing sitting in the dev DB; not a Phase 2 regression, just surfaced by
  it.
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
- Blocked: nothing.
- Next: proceed to Phase 4 (structured lessons) — remember to ask detailed
  clarifying questions before designing the conjugation/subjunctive feature,
  per the Known Issues note below and the standing instruction to do so.
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
- The dev Postgres volume (`pgdata`) accumulates manual-testing debris across
  sessions (e.g. rows created via the `/docs` Swagger UI, or now via the
  frontend's own bootstrap) since it's never wiped — caused one pre-existing
  test to fail in Phase 2 (see that Current Status entry at the time), and
  in Phase 3 meant the bootstrap silently adopted a leftover
  `sanity-p2@example.com` test user as "the" user rather than creating a
  fresh one (harmless — single-user bootstrap is correctly not supposed to
  care whether a user is "real" — but worth a rename or a
  `docker compose down -v` some session; the auto-mode safety classifier
  blocked an attempted `down -v` this session as too destructive to run
  without explicit confirmation, which is the right call). Also caused a
  *second* test collision in Phase 3 verification — `test_languages.py`'s
  `test_list_languages_includes_created` hardcoded `"es"`, which by then
  collided with a real Spanish `Language` row the frontend bootstrap had
  created live; fixed the same way as the earlier `"en"` collision
  (`"es-t"` instead). Worth treating this as a pattern now, not two
  one-offs: any test hardcoding a plausible-sounding `Language.code` is at
  risk here, not just the two that have actually broken so far.
- Frontend toolchain needed three version pins below their defaults (`vite`,
  `@vitejs/plugin-react`, `jsdom`) because this machine's Node (20.13) is
  below 20.19 — see the 2026-08-13 decision log entry. Revisit/remove the
  pins if Node ever gets upgraded.
- The due-card queue's NEW-card query (`deck_id + state = 'new' ORDER BY
  created_at`) has no dedicated index beyond the composite's leading
  `deck_id` column — fine at portfolio scale, revisit with a
  `(deck_id, state, created_at)` index if it ever matters.
- FSRS scheduling uses the library's default weights/parameters (not tuned
  to any real user's review history) — `fsrs-optimizer` exists for that but
  needs substantial review history per user to be worthwhile; revisit well
  after there's real usage data, not before.

- **Conjugation practice + Spanish subjunctive (requested 2026-08-13, planned
  for Phase 4)** — a dedicated mode for drilling verb conjugation across
  tenses/moods, plus Spanish subjunctive specifically: both conjugation and
  *when to use it*, called out as a deliberate Duolingo gap and something the
  user wants as a genuinely Spanish-specific section, not a generic feature
  Spanish happens to populate. Corrected framing (2026-08-13): an earlier
  draft of this note leaned toward treating it as purely generic "mood/tense
  drilling driven by data," to stay safely inside the language-agnostic
  principle — user pushed back. The principle isn't "every language gets
  identical features"; it's "language-specific depth is fine and expected,
  but it must be pluggable/config-driven per language, never a hardcoded
  `if language == "spanish"` branch scattered through generic code." User's
  own second example of the same pattern: a hypothetical future Mandarin
  addition would need its own section on reading characters — "fundamentally
  different than a latin or germanic language" — which is exactly the same
  shape of problem (a real per-language specialty section, architected so it
  doesn't require rewriting the rest of the app). **Before this gets
  designed or built, ask the user detailed clarifying questions about what
  they actually want** — they explicitly said they don't want a generic
  Duolingo clone and want to be asked, not have a generic version assumed.
  Known open questions so far, to bring into that conversation rather than
  resolve unilaterally:
  - How much of a language's mood/tense/specialty-section structure lives in
    `Language.grammar_config` (already built for per-language grammar rules)
    vs. needs a dedicated table/registry for "specialty modules" a language
    can declare (e.g. Spanish declares a subjunctive-mastery module, a future
    Mandarin config declares a character-reading module).
  - How conjugated forms get produced: rule-based generation (regular-verb
    endings in config + an irregular-verb override table) vs. fully
    pre-stored per-verb conjugation data.
  - Whether this needs a new `ExerciseType.CONJUGATION` (typed-answer
    production, matching this project's stated preference for retrieval over
    multiple-choice) vs. reusing `FILL_IN_BLANK`.
  - Subjunctive *usage* practice (recognizing trigger phrases/clauses that
    require it) reuses existing exercise types with curated content — the
    differentiation from Duolingo there is content curation, not new
    mechanics — but confirm this framing still fits whatever fuller vision
    the user has once asked.
  - Whether individual conjugated forms should also become spaced-repetition
    items (Phase 2's FSRS engine), not just Duolingo-style lesson exercises.

- **Native-language vocabulary builder (requested 2026-08-13, not yet
  scheduled)** — a separate, lower-priority idea: an Anki-like tool for
  building vocabulary in the user's *native* language (e.g. advanced/"big"
  English words), not L2 acquisition. User suggested this as possibly its
  own distinct section of the site, "maybe at the end." Not yet added as a
  numbered phase — ask the user whether this becomes its own Phase 9+ or
  stays a loose idea when it's actually time to consider it.
