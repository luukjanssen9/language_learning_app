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
- [x] **Phase 4 — Structured lessons**: lesson/skill data model (mostly
  already in place from Phase 1 — `Skill`, `LessonExercise`,
  `UserProgress`), seed starter English→Spanish course content, exercise
  UI (multiple choice, translation, fill-in-blank), a submit/grade
  endpoint. Minimal gamification only (progress/mastery tracking, no
  streak/XP UI in v1). Also built, design resolved 2026-08-13 (see
  Decisions Log): a new `ExerciseType.CONJUGATION` drilling all verb
  forms across tenses/moods, plus a distinct subjunctive-usage
  ("spot the trigger") practice section covering three trigger
  categories — doubt, desire/wish, emotion — as a deliberate
  differentiator from Duolingo, which doesn't teach subjunctive well.
  Course navigation reworked after use (separate decks/course pages,
  general course switcher, data-driven practice categories, no progress
  locking, Verb Conjugation rebuilt as a tense-picker → conjugate-all-
  6-persons drill covering 15 irregular verbs + present perfect). Code
  complete and verified end-to-end in a real browser against the live
  API.
- [x] **Phase 5 — Core AI/NLP features**: LLM service layer (provider-agnostic,
  Gemini default), example generation + mnemonics, free-text grading, journal
  correction + auto vocab extraction, known-vocabulary system, reading
  passage generation, paste-in content with unknown-word flagging,
  coverage-gap analysis vs. a CEFR/HSK-style list, adaptive weak-point
  targeting — all slices built. Generic auto-card-generation dropped as
  its own slice (journal correction/paste-in flagging cover it with real
  context attached). Also: the Vocabulary course category
  (Greetings/Family) was retired in favor of a Reading category — see the
  2026-08-14 decision log entry.
- [x] **Phase 6 — Conversational practice partner**: chat UI, roleplay
  scenarios constrained to known vocabulary, in-context correction —
  complete and verified end-to-end, built as one MVP slice rather than
  split further (see the 2026-08-15 decision log entry).
- [ ] **Phase 7 — Speech (stretch goal)**: Whisper integration, pronunciation
  comparison/feedback.
- [ ] **Phase 8 — Scalability check, polish & deploy**: ~~add a second
  language's config to prove the architecture generalizes~~ — done early,
  2026-08-14 (v1 Dutch course, see Decisions Log). Real multi-user auth
  (Google Sign-In) added to this phase's scope 2026-08-15, per the user's
  explicit ask — ~~sliced like Phase 4/5/6 into 4 slices (backend
  foundation + `/login`; personal-data `user_id` scoping; route ownership
  hardening; full frontend integration + session-derived identity)~~ —
  **all 4 slices done and verified end-to-end, 2026-08-16.**
  ~~Performance/cost review~~ — done, 2026-08-16 (rate limiting added,
  one real N+1 fixed, see Decisions Log). ~~Final test pass~~ — done,
  2026-08-16 (coverage-gap audit, 31 new tests, see Decisions Log). Still
  remaining: deployment; final README with setup, architecture overview,
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

**2026-08-13 — Review session's "Session complete" and "nothing due" states
gained a link back to the deck.** Neither had any navigation at all when
Phase 3 first shipped — a real dead end, reachable only via the browser's
own back button. Found by using the live app, not by testing. Fixed by
linking both terminal states to `/decks/[deckId]` rather than the
dashboard, so the destination is always "the deck you were just reviewing,"
not a level higher.

**2026-08-13 — Deck editing (rename, description, delete) added; wasn't
part of Phase 3's original scope, which only covered card management and
review.** The backend's `PATCH`/`DELETE /decks/{id}` already existed
(Phase 1) and simply weren't wired to anything on the frontend. Added
`DeckForm` (mirrors `CardForm`'s pattern) and exposed it two ways: inline
on each dashboard row via an "Edit" button next to "Study" (no navigation
required, matching the request to make it a one-click action instead of
click-through-to-detail-page), and on the deck detail page itself. Delete
asks for confirmation and redirects to the dashboard on success.

**2026-08-13 — Phase 4 navigation sketched before building anything, on
request, so routing decisions aren't redone mid-phase.** Dashboard gains a
second sibling section, "Your course" — the slot the "Unified Dashboard"
layout decision above specifically reserved for this — showing an ordered
`Skill` path, mastery bars driven by `UserProgress.mastery_level`, nodes
locked/unlocked via `prerequisite_skill_id`. A new session route,
`/skills/[skillId]/lesson`, mirrors `/decks/[deckId]/review`'s shape: frozen
exercise queue, progress indicator, interleaved exercise types (per this
doc's own convention against blocking one type at a time), and a "Session
complete" screen with its back-to-source link built in from the start —
unlike the review session, which shipped without one and needed a follow-up
fix. No separate skill-detail page: tapping a node starts the lesson
directly, since exercise content isn't user-edited in v1 the way cards are.
One fork deliberately left open, not decided here: whether conjugation/
subjunctive practice hangs off a `Skill` (fits the path above) or becomes
its own third top-level dashboard section — left for when that feature is
actually designed, per the standing clarifying-questions rule.

**2026-08-13 — Conjugation/subjunctive feature design resolved**, closing
out the open questions the 2026-08-13 "Conjugation practice + Spanish
subjunctive" note (below) deliberately left for a clarifying-questions
conversation. Resolves the fork above too: it hangs off `Skill`, not a
third dashboard section.
- **Schema**: no new tables. A nullable specialty-module slug on `Skill`
  (and `LessonExercise`) tags content as belonging to a named module (e.g.
  `spanish-subjunctive`); `Language.grammar_config` keeps holding the raw
  grammar data — regular-verb endings and an irregular-verb override table
  — that generation logic reads.
- **Conjugated forms are generated, not hand-seeded**: rule-based, from
  the config above plus a base verb list, so adding a verb doesn't mean
  hand-authoring every tense/mood form for it.
- **New `ExerciseType.CONJUGATION`**: typed-answer production, covering
  *all* conjugations (present, past, future, subjunctive, etc.) — not
  subjunctive-only. Kept distinct from `FILL_IN_BLANK` so later analytics
  (Phase 5 weak-point targeting) can tell "conjugate this verb" apart from
  a generic fill-in-blank.
- **Subjunctive *usage* practice ("spot the trigger") is a distinct
  practice section, not conjugation with different content** — corrects
  this note's own earlier framing, which treated it as just curated
  content on an existing type. Mechanically it reuses `MULTIPLE_CHOICE`
  (a sentence with a blank; answer choices are the same verb across
  different moods/tenses, e.g. "Espero que tú ___" → *vienes / vengas /
  vendrás*), tagged via the same specialty-module slug. Each trigger-
  category `Skill` leads with a short, ungraded teaching screen
  (explanation + example sentences, e.g. "doubt triggers the
  subjunctive") shown once before that skill's practice queue — not a new
  exercise type, just content on the `Skill` itself.
- **v1 scope: three trigger-category skills** — doubt, desire/wish,
  emotion — the most common, foundational triggers, enough to prove the
  pattern repeats across multiple skills rather than reading as a single
  special case. Impersonal expressions and denial are deliberately
  deferred: adding either later is just another `Skill` row, no schema
  change.
- **Lesson-only for now**: conjugated forms don't automatically become
  FSRS `Card` rows this phase. Promoting them to spaced-repetition items
  is a clean later addition, not a rewrite, if wanted.

**2026-08-13 — Phase 4 Stage A (generic core + conjugation) built and
verified end-to-end; Stage B (subjunctive triggers) deliberately not
started yet — stopping here for a review checkpoint per the approved
plan.** Migration adds `skills.specialty_module`, `skills.intro_content`,
`lesson_exercises.specialty_module`; `ExerciseType.CONJUGATION` needed no
migration (the column has no CHECK constraint). New
`app/services/conjugation.py` (rule-based generation from
`Language.grammar_config`, irregular-verb overrides falling back to the
regular rule per-tense) and `app/services/exercise_grading.py`
(per-exercise-type grading), wired into a new `POST
/lesson-exercises/{id}/attempt` endpoint that upserts `UserProgress`
(mastery = plain accuracy ratio). Hit the same class of bug
`test_fsrs_engine.py` already flagged for `Card.reps`/`lapses`: a new
`UserProgress`'s `times_attempted`/`times_correct` `default=0` only
applies at INSERT time, not on construction, so incrementing before
flush needs them set explicitly. New idempotent `app/seed.py`
(`python -m app.seed`) seeds real, hand-verified Spanish conjugation
data (regular endings for `-ar/-er/-ir` × present/preterite/imperfect/
future + present subjunctive; 8 irregular verbs' present indicative) plus
two vocab skills and the "Verb Conjugation" skill (20 exercises). 9 new
backend tests (51 total), all passing; ruff/tsc/eslint clean. Frontend:
`skillPath.ts` (pure lock/unlock logic, mirrors `deckStats.ts`'s
proxy-metric pattern), dashboard "Your course" section, and
`/skills/[skillId]/lesson` mirroring the review session's shape —
including a back-to-course link on both terminal states from the start,
learning from the review session's own gap found and fixed earlier this
session. Verified live: full vocab-skill session (multiple-choice,
translation, fill-in-blank, including a deliberate wrong answer and a
case-insensitive correct one), a real seeded `CONJUGATION` exercise
graded correctly through the actual API, and the dashboard's mastery bar
+ lock/unlock state updating correctly after leaving a session.

**2026-08-13 — Phase 4 Stage B (subjunctive-trigger skills) built and
verified end-to-end; Phase 4 now fully complete.** All four review
questions asked at the Stage A checkpoint were answered "keep as built"
(strict accent-sensitive grading, wrong answers stay hidden rather than
revealing the correct one, attempt-only unlock gate, click-to-submit
multiple choice) — no code changes from that checkpoint, just confirmation
to proceed. Extended `app/seed.py` with three trigger-category skills
(Doubt, Desire/Wish, Emotion), chained linearly after Verb Conjugation;
each has `intro_content` (explanation + 2 example sentences) and 3
`MULTIPLE_CHOICE` exercises whose option strings are hand-authored, not
computed via `conjugate()` — multiple-choice grading only compares a
selected index, so these don't depend on `grammar_config`'s coverage the
way `CONJUGATION` exercises do. **Found and fixed a real gap while
verifying live, not by code review**: `SkillRead`/`LessonExerciseRead`
(`app/schemas/skill.py`, `app/schemas/lesson_exercise.py`) were never
updated when `specialty_module`/`intro_content` were added to the ORM
models in Stage A — Pydantic silently drops undeclared fields, so the API
was serving every skill with `intro_content` missing entirely. Invisible
in Stage A because none of those skills had intro content to lose;
surfaced the moment a trigger skill's intro screen silently failed to
render. Fixed by adding both fields to the schemas (full CRUD symmetry,
matching how the rest of `Skill`/`LessonExercise` is exposed, not a
read-only carve-out). 51 backend tests still green after the fix; no new
tests added specifically for the schema fields since the existing
attempt/filter tests already round-trip full `SkillRead`/
`LessonExerciseRead` objects through the API. Verified live end-to-end:
intro screen renders once before practice on "Doubt," multiple-choice
grading correct, and the dashboard shows independent mastery per
trigger-category skill (Doubt 3/3 correct, Desire/Wish unlocked and
untouched, Emotion still locked) alongside Greetings/Verb Conjugation's
own independent progress.

**2026-08-13 — Phase 4 course navigation reworked, after using the
built version.** Decks and course split onto separate pages (`/` and
`/course`, new `Nav.tsx`) instead of one dashboard; a course switcher
(`CourseProvider`/`CourseSwitcher`) built generally against the real
`Course`/`Language` tables even though only one course exists yet;
skills regrouped into practice categories (Vocabulary, Verb Conjugation,
Subjunctive) read from a new `Language.grammar_config.practice_categories`
array rather than hardcoded per-language names in component logic;
progress locking removed entirely (`lib/skillPath.ts` deleted, `SkillNode`
lost its `unlocked` prop). Verb Conjugation became a genuinely different
flow: `/course/category/verb-conjugation` (tense picker, tenses derived
from the exercises actually present) → `/course/category/verb-conjugation/
[tenseKey]` (one random verb, all 6 persons on one screen — yo/tú/usted/
nosotros/vosotros/ustedes display labels over the existing internal
yo/tú/él/nosotros/vosotros/ellos keys, no data change). "Check all" fires
the existing single-answer attempt endpoint 6 times via `Promise.all`
rather than adding a batch endpoint.

Backend content expansion to support it: `irregular_verbs` grew from 8
verbs/present-indicative-only to 15 verbs (added venir, poner, salir,
saber, dar, ver, haber) each covering every tense/mood it's actually
irregular in, not just present; added `irregular_participles` +
`conjugate()`'s `tense="present_perfect"` branch (haber + participle,
composed via a recursive `conjugate()` call); `_seed_conjugation_skill`
replaced its 20 hand-listed tuples with a generator over 17 verbs × 6
tense/mood combos × 6 pronouns (612 exercises) — every combination
verified to resolve via a standalone script before seeding. Also fixed a
real idempotency bug the generator would have hit immediately: the seed
script's "skip if this skill already has exercises" check meant a content
change would never reach an already-seeded dev DB — replaced with
delete-then-recreate per skill (also deleting any `UserExerciseAttempt`
rows referencing the deleted exercises, to satisfy the FK — acceptable
for dev seed content per the existing "dev DB accumulates test debris"
note, not real user data).

**Three real bugs found live, not by review**, all in the new
`[tenseKey]` drill page — the first two caught during my own
verification, the third reported by the user immediately afterward
(every tense showing "No verbs for this tense yet" when reached the
normal way, via the category picker page): (1) `option` was recomputed
via a fresh `.find()` over a freshly-built array every render, cascading
into an unmemoized `groups` value that a render-time state adjustment was
comparing by reference — every render looked like a "real" change,
producing an infinite re-render loop the instant the page loaded; fixed
by memoizing the intermediate `options` list too, so `.find()` on a
stable array reference returns a stable element reference. (2) A second,
subtler instance of the same class of bug: `const { data: exercises = []
}` creates a brand-new empty array every render while the query is still
loading — harmless everywhere else this pattern's used in the app (just
rendering an empty list), but fatal here since this page is the first
place comparing exercises-derived values by reference; fixed with a
module-level `EMPTY_EXERCISES` singleton instead of a fresh per-render
default. (3) After fixing (1) and (2), the initial verb pick still never
fired when `exercises` was *already cached* on mount (the normal path —
the picker page fetches the same query first): the "did `groups` change"
comparison's own baseline (`groupsAtLastPick`) was initialized from that
same already-correct first render, so the comparison started true-equal
and never detected a "change" to pick from. `tsc`/eslint/my own live
click-through all missed it because I always tested by navigating
directly to a `[tenseKey]` URL, which hits the empty-then-populated
transition case (2) actually catches; clicking through from the picker
page — the real user path — hits neither transition. Fixed by seeding
the initial `group` from a lazy `useState` initializer (reads `groups` as
of the very first render, correct in both the cached and not-yet-loaded
cases) instead of relying solely on the change-detection comparison for
the first pick. Worth remembering as a pattern beyond this one page: any
state derived from query data via reference comparison needs a stable
empty default *and* its own correct value on mount, not just on change —
and testing such a page only by direct URL navigation isn't equivalent to
testing the actual click-through path.

**2026-08-14 — Grading made accent-insensitive; conjugation drill mistakes
now reveal the correct answer and allow fixing just the wrong field,
rather than forcing a new verb.** Both from real usage feedback, reversing
the Stage A checkpoint's "keep grading strict" and "keep wrong answers
hidden" defaults for this specific case — deliberately, not by oversight.
Accent-insensitivity: typing Spanish accents on a non-Spanish keyboard is
real, unavoidable friction, distinct from the general typo-tolerance this
project still defers to Phase 5's LLM grading — `exercise_grading._normalize`
now strips accents via Unicode NFKD decomposition (drop combining marks)
before comparing, applied uniformly to translation/fill-in-blank/
conjugation since it's the same function; underlying conjugation *data*
is untouched (still stores real accents — only the comparison is
forgiving). New `get_correct_answer()` factored out of `grade_attempt`
(same logic, now reusable) and returned unconditionally on
`POST /lesson-exercises/{id}/attempt` as `correct_answer` — null for
MULTIPLE_CHOICE/FREE_TEXT, not persisted on `UserExerciseAttempt` (derived
fresh each time so it can't go stale if grammar_config is later revised).
`ConjugationDrill.tsx`: wrong fields now show "Correct: <answer>" and stay
editable (correct fields lock); a "Recheck" button re-submits all 6
(harmless for already-correct ones) until every field passes or the
learner chooses "Try another verb." No retry cap — the reveal already
limits how many blind guesses are useful. 13 new backend tests (68
total): a new `test_exercise_grading.py` (pure unit tests, no DB, same
convention as `test_conjugation_service.py`) plus accent/`correct_answer`
coverage added to the existing integration tests. Verified live: a
missing-accent answer ("decis" for "decís") graded correct, a genuine
mistake revealed "Correct: dice" while staying editable, fixing it and
clicking Recheck brought the verb to 6/6 and the button correctly
disappeared once nothing was left to fix.

**2026-08-14 — v1 Dutch course added, ahead of the Phase 8 slot originally
planned for it** — the point was to actually test this project's core
"language-agnostic by design" principle, not defer it. Worth doing now
rather than after Phase 8 stacks more Spanish-only assumptions on top.
No Subjunctive category for Dutch (its subjunctive is archaic/non-productive
in modern usage), on request.

Found and fixed **three real places Spanish specifics had leaked into
code instead of `grammar_config` data**: (1) `ConjugationDrill.tsx`'s
pronoun labels were a hardcoded Spanish array — moved into
`grammar_config.conjugation.pronoun_labels` per language (the six
internal slot keys stay literal Spanish words as opaque identifiers,
deliberately not renamed — touching all 612 already-seeded Spanish
exercises for a purely cosmetic gain wasn't worth it, documented inline).
(2) `conjugate()`'s present-perfect branch hardcoded `"haber"` as the
auxiliary — Dutch splits by verb (most take `hebben`, motion/change-of-
state verbs like `gaan`/`komen` take `zijn`), so this became a per-
language default (`grammar_config.conjugation.perfect_auxiliary`) with a
per-verb override (`irregular_verbs[verb].perfect_auxiliary`); Spanish's
config now declares `perfect_auxiliary: "haber"` explicitly instead of
relying on a Python-level default (which stays only for old test
fixtures). (3) `_participle()`'s regular-formation fallback (stem +
"ado"/"ido") is Spanish's own suffix rule, not generalized — Dutch
participles are prefix *and* suffix (`ge-` + stem + `-d`/`-t`, with real
spelling rules governing both the suffix choice and several stems'
vowel length) and building a genuinely pluggable formation-rule system
for two data points was judged premature; every Dutch verb instead
provides its participle via `irregular_participles` explicitly (a
legitimate use of the same override table Spanish already has 4 entries
in, not a workaround) — flagged in a comment for revisiting if a third
language also can't use the fallback.

**Content**: new `nl`/English→Dutch `Language`/`Course` rows. 8 verbs
(zijn, hebben, gaan, komen, werken, maken, wonen, spelen), each fully
hand-specified in `irregular_verbs` — deliberately not routed through the
regular-endings fallback at all, since Dutch's real vowel-length spelling
rules (e.g. "wonen" → stem "woon", not "won") would make a naive
infinitive-minus-two-letters stem wrong for several of them; a best-
effort `regular_endings.en` rule exists for architectural completeness
but isn't exercised by any seeded exercise. Three tenses, not Spanish's
six: present, one simple past (Dutch doesn't split preterite/imperfect
the way Spanish does), and present perfect — no periphrastic future
("zullen" + infinitive is a different compound shape than auxiliary +
participle, out of scope for now). 8 × 3 × 6 = 144 conjugation exercises,
generated the same loop pattern as Spanish's 612, seeded via new parallel
`_seed_dutch_*` functions alongside the Spanish ones rather than a shared
parameterized framework (two languages don't justify that abstraction
yet — a third would be the right trigger). Two vocab skills (Greetings,
Family) mirroring the Spanish ones' exact exercise shape.

Verified: a standalone resolution-check script confirmed all 144
(verb, tense, pronoun) combinations resolve before seeding, plus hand-
verified spot checks (`zijn`/present_perfect/yo → "ben geweest",
`gaan`/present_perfect/yo → "ben gegaan", `werken`/present_perfect/yo →
"heb gewerkt" — confirming the hebben/zijn split actually works). Live
end to end: switching the course dropdown to Dutch lands on `/course`
showing only Vocabulary and Verb Conjugation (no Subjunctive card);
completed a Dutch vocab exercise; the conjugation drill correctly showed
ik/jij/hij/wij/jullie/zij instead of Spanish's labels; `werken` graded
6/6 correct through the UI; `gaan`'s hebben/zijn split confirmed through
the live API directly ("ben gegaan" correct, "heb gegaan" — the
plausible-looking wrong-auxiliary mistake — correctly graded wrong).
Switched back to Spanish and confirmed nothing there changed: still 3
categories including Subjunctive, still usted/ustedes labels. 70 backend
tests pass (2 new), 12 frontend tests, `tsc`/eslint/ruff all clean.

**2026-08-13 — Phase 5 started; slice 1 (LLM service layer + example-sentence
generation) code-complete and test-verified; live verification blocked on a
Gemini key.** Phase 5 bundles six sub-features (service layer, example
generation, free-text grading, auto-card-gen, mnemonics, adaptive
weak-point targeting) — too much for one pass, so it's being built one
slice at a time with a checkpoint between each, same split as Phase 4's
Stage A/B. This slice was chosen first because it exercises every piece
the layer needs (templated prompts, structured-output parsing,
per-language content) with the least extra product design, and because
it's naturally cacheable — closing the standing "Gemini free-tier rate
limits are tight" Known Issue immediately rather than deferring it again.

**LLM layer**: new `app/services/llm/` package — `base.py` defines the
`LLMProvider` Protocol (one method, `generate_structured(prompt,
response_model, model_tier)`, always returning a parsed Pydantic
instance — reused by every future Phase 5 sub-feature, not just this
one) and `LLMError`; `gemini.py`'s `GeminiProvider` wraps the
`google-genai` SDK's async client, using `response_mime_type`/
`response_schema` for structured output; `__init__.py`'s
`get_llm_provider()` is an `lru_cache` singleton reading
`settings.llm_provider` (only "gemini" implemented — no Anthropic key
yet), exposed as a FastAPI dependency so tests can override it with a
fake, same mechanism as `get_db`. `LLMError` gets a global 502 handler in
`main.py`, mirroring the existing `IntegrityError` → 409 handler. Model
names re-verified via web search before building: `gemini-3.1-flash-lite`/
`gemini-3.5-flash` are both still current, free-tier models — no config
change needed from Phase 0's scaffolding.

**Example-sentence feature**: new `VocabularyExample` table (cache —
`vocabulary_item_id`, `target_text`, `base_text`); new
`app/services/sentence_generation.py` (pure function, no DB access, same
convention as `conjugation.py`/`exercise_grading.py`) builds a prompt
entirely from arguments (target/base language name, word, part of
speech — never hardcoded); new `GET /vocabulary-items/{id}/examples`
get-or-generate endpoint: serves cached rows if any exist (a DB read, no
LLM call), otherwise generates via the service, persists, and returns —
so a vocabulary item only ever costs one real Gemini call across its
whole lifetime.

**Frontend gap found while planning**: cards created via the Phase 3 UI
never link to a `VocabularyItem` (only `front_override`/`back_override`
text), and the backend's existing `/vocabulary-items` CRUD API had never
been wired to the frontend at all. Decided (user confirmed) not to force
the feature onto the review flip card or deck card list, which have no
path to real vocabulary content yet — instead built a new, minimal,
read-only `/vocabulary` page (own `CourseProvider`-wrapped layout,
mirroring `course/layout.tsx`'s exact pattern — course switcher works
the same way there), listing a course's `VocabularyItem`s with a
"Generate examples" button per row that lazily fetches
(`useVocabularyExamples(id, enabled)`) only once expanded. This finally
gives the vocabulary CRUD API its first real frontend use.

**Verified**: 7 new backend tests (77 total) — pure unit tests for
`sentence_generation.py` against a fake `LLMProvider` (including one
proving the prompt is templated from arguments, not hardcoded, by
asserting "Spanish" never appears in a Dutch-word prompt), plus
integration tests for the endpoint via the same `app.dependency_overrides`
mechanism used for `get_db`, covering first-request generation, cached
second-request (asserting the fake's call count stays at 1), and 404 for
a missing item. `ruff`/`pytest` clean without touching real Gemini quota.
Frontend: `tsc`/`eslint`/`npm run test` (12/12) all clean.

**Verified live against the real Gemini API**, once the user added a
`GEMINI_API_KEY` to `backend/.env`. One deployment snag first: a plain
`docker compose restart backend` does *not* reload `env_file` values for
an already-created container (env vars are fixed at container-creation
time) — the first attempt failed with `ValueError: No API key was
provided`. Fixed with `docker compose up -d --force-recreate backend`,
which actually recreates the container against the current `.env`.

With a real key: generating examples for "hola" (Spanish) produced real,
natural Spanish sentences with correct English glosses within a few
seconds; reloading the page and re-expanding served the identical three
sentences near-instantly, confirmed via a direct Postgres query showing
exactly 3 `vocabulary_examples` rows for it (one generation batch, ever
— the caching path works, not a fresh call per view). Switching to the
Dutch course and generating for "hallo" produced genuinely Dutch
sentences ("Hallo, hoe gaat het?", "Hallo, ik ben Sarah," etc. — not
Spanish content), confirming the prompt's language-name templating
actually drives generation rather than defaulting to whatever was built
first.

**One real transient failure, found live**: the first Dutch request took
~24s and came back as a 502 (the `LLMError` handler firing on some
Gemini-side hiccup — exact cause not captured, since the handler
intentionally doesn't log the underlying exception, only returns it in
the response body). A direct retry via `curl` succeeded normally and
fast. Not treated as a bug to fix in this slice (no retry/timeout UX was
in scope, and the free-tier's occasional flakiness is already an
accepted, documented trade-off) — but worth remembering for later Phase
5 slices that call the LLM synchronously in the request path: a slow
provider call can block a request for 20+ seconds before failing, and
this slice's plain "Generating examples…" text gives the user no sense
of that, just an indefinite wait. Revisit if a future slice's feature
makes that UX gap actually matter (e.g. free-text grading, which is
also on the request's critical path).

**A second real bug, found live by the user right after this**:
`CourseSwitcher.tsx`'s `handleChange` unconditionally `router.push`ed to
`/course` on every switch, regardless of which page the switcher was
being used from — harmless while `/course` was the switcher's only
consumer, but the new `/vocabulary` page reuses the same component, and
switching courses there was bouncing back to `/course` instead of
staying put. Fixed by reading the current top-level section from
`usePathname()` and pushing to *that* section's root instead of a
hardcoded one — generalizes correctly for any future section that also
embeds `CourseSwitcher`. Re-verified live: switching courses on
`/vocabulary` now stays on `/vocabulary` and shows the new course's
words; switching on `/course/category/vocabulary` (a deep link that
doesn't survive a course change) still correctly bounces back to
`/course`'s own root, so the original fix that line existed for still
works. `tsc`/`eslint` re-run clean after the change.

**2026-08-14 — Anki-style vocab decks built: real-input notes, dual-
direction cards, quick-add, Chinese as a third language.** The user did
outside research on how they want their Anki-style vocab decks to work
(sourced from real shadowing/reading input, not generic pre-made lists)
and asked for it before continuing Phase 5. Clarified up front: real
content for both Spanish and Chinese now (not just architecture); the
note's own real, sourced example sentence is a distinct concept from
Phase 5's LLM-generated `VocabularyExample` (both coexist); build real
production-card gating now, not a stub; quick-add is global, reachable
from any page.

**Data model**: `VocabularyItem` gains four universal columns —
`source`, `example_sentence`, `example_sentence_translation`, `tags`
(JSONB list) — kept as plain columns since every language needs them,
unlike Chinese-only pinyin data, which goes in the existing `attributes`
JSONB bag under a *generic* key (`transliteration`, not `pinyin` —
caught before committing: hardcoding a Chinese-specific key name in
frontend code would have been exactly the kind of per-language branching
this project's own principle forbids; a future Japanese/Korean
transliteration would need a different key otherwise).
`Language.grammar_config` gains a `vocab_deck` sub-key
(`dual_direction_cards`, `needs_transliteration`,
`transliteration_label`, `production_gate`) — Spanish/Dutch set
`dual_direction_cards: false`, Chinese sets it `true`, same per-language-
data-not-code-branch pattern as the Dutch course's
`perfect_auxiliary`/`pronoun_labels`. New `CardState.SUSPENDED` (plain
migration, no `ALTER TYPE`, per the existing enum-storage convention) —
a dual-direction note's production card starts here instead of `NEW`,
invisible to the due-queue and the new-card cap until its production
gate is met. New `Card.vocabulary_item` relationship + `CardRead`
nesting it (via `selectinload`, avoiding an N+1 for a due-queue that can
hold 100+ cards) — closes the "Card → VocabularyItem never resolved
anywhere" gap Phase 5 planning had found and left open. New
`Deck.daily_new_card_cap` (nullable — `None` means "use the 15 default").

**Backend**: new `app/services/note_cards.py` (`build_cards_for_note`,
pure, same convention as `conjugation.py`) — one card for a single-
direction language, two (recognition `NEW` + production `SUSPENDED`)
for a dual-direction one. New `POST /cards/quick-add`: one round trip,
creates the `VocabularyItem` note and its `Card`(s) together — the whole
point of "capture a word mid-shadowing-session." `GET /cards/due` gained
two pieces of real logic: (1) a production-gate unlock check — a
`SUSPENDED` card flips to `NEW` once its sibling recognition card has
either ≥N successful reviews or the note is ≥M days old, whichever comes
first; (2) genuine daily-new-card-cap enforcement, computed from
`ReviewLog` rows where `state_before == NEW` and `reviewed_at` falls in
today's UTC calendar day — no new counter table, reusing data the FSRS
engine already records. `new_limit` stays available as an explicit
per-request override (existing tests/frontend calls depend on it) but
now defaults to the deck's own cap instead of a flat 20.

**Two real bugs found live, both fixed**: (1) `QuickAddDialog`'s native
`<dialog>` rendered pinned to the top-left corner instead of centered —
Tailwind's preflight reset strips the browser's default `margin: auto`
centering; fixed with explicit `fixed inset-0 m-auto`. (2) The
production-gate unlock (`card.state = CardState.NEW`) was never
committed in `list_due_cards` — a GET request's DB session (see
`app/database.py`'s `get_db`) closes without auto-committing, so the
flip was only visible for the rest of *that* request and silently
reverted on the next `/due` call. The test suite's session-per-test
fixture convention (one shared session across every request in a test)
couldn't catch this class of bug — it was found only via real,
independent `curl` calls against the live API, each a genuinely separate
request the way the real frontend behaves. Fixed with an explicit
`await db.commit()` right after the unlock check.

**Content**: 3 real Spanish notes (single card each) and 3 real Chinese
notes (recognition + suspended production each), seeded through the
actual `build_cards_for_note` path via new `_seed_note`/
`_get_or_create_user`/`_get_or_create_deck` helpers in `seed.py` — the
seeded user converges on the same single user `bootstrap.ts` creates
(same email/display-name literals), so seed.py and the frontend never
create two different "the" users. Chinese pinyin uses diacritic tone
marks (nǐ hǎo), not numerals, per the user's spec — flagged in a code
comment that tone-mark accuracy, unlike this project's Spanish grammar
rules, can't be cross-checked by running code and is worth a human
sanity check before extending.

**Verified**: 88 backend tests (16 new — `note_cards.py` unit tests plus
`test_quick_add_and_gating.py`'s integration coverage of quick-add,
single/dual-direction generation, suspended-card review rejection, both
gate types, and the daily cap including a day-boundary case), `ruff`
clean. Frontend: 15 tests (3 new `Flashcard` cases for recognition/
production/no-transliteration rendering), `tsc`/`eslint` clean. Live:
quick-added a real Chinese word from the dashboard (not a deck page),
confirmed via a direct Postgres query it produced exactly the
recognition-`new`/production-`suspended` pair; drove that note's
recognition card through 5 real reviews via the API and confirmed the
production card actually unlocked and *stayed* unlocked on a fresh
request after the commit fix; set a deck's cap to 1 and confirmed the
due-queue correctly reported zero remaining new cards for the rest of
the day. Existing `test_due_queue_appends_new_cards_oldest_first_capped_at_new_limit`
needed a one-line update (new_limit 2→3): a due card's own first review
now legitimately counts toward the daily cap the same as any other, so
the test's own setup consumed one of its requested slots — a real
behavior change, not a bug.

**2026-08-14 — Five real issues found using the vocab-deck feature live,
all fixed.** The user tried the built feature and reported three things
in one message; investigating them surfaced two more along the way.

1. **Quick-add showed on every page**, including Course and Vocabulary,
   where it doesn't apply (it creates flashcard notes, not lesson
   content). `Nav.tsx` now only renders it on `/` and `/decks/*`.
2. **Deck detail page showed vocabulary-backed cards as blank text with
   just the arrow separator.** `CardListItem.tsx` (unlike `Flashcard.tsx`,
   already fixed in the Anki-decks entry above) was never updated to
   read `card.vocabulary_item` — it only ever read `front_override`/
   `back_override`, both null for note-backed cards. Fixed the same way,
   plus added a "Recognition"/"Production" label so a dual-direction
   note's two rows (same words, same deck) read as distinct rather than
   duplicates. Also hid the "Edit" button for vocabulary-backed cards
   entirely, rather than ship it broken: `CardForm` only edits
   `front_override`/`back_override`, which `Flashcard.tsx` ignores
   whenever `vocabulary_item` is present, so "editing" one would save
   successfully with zero visible effect. A real note editor is a
   separate, not-yet-built feature.
3. **"Hard"/"Again" ratings never came back within the same session,**
   unlike Anki. Root cause wasn't wrong scheduling -- FSRS correctly
   scheduled a short same-day follow-up (its normal minutes-scale
   learning steps) -- the review session just never re-checked whether
   an earlier card became due again, since `useDueCards`' frozen queue
   (`staleTime: Infinity`, a deliberate Phase 3 decision to stop a
   rating's rescheduling from reshuffling cards not yet reached) only
   ever gets iterated forward. Fixed by promoting the queue to local,
   mutable state (hydrated once from the fetch, same render-time
   "adjust state" pattern used for the conjugation drill page's
   analogous problem) and, on each review response, re-inserting the
   card a fixed few positions later if it's still `learning`/
   `relearning` (i.e. FSRS didn't graduate it to `review` yet). A ref
   (synced via effect, since refs can't be written during render) tracks
   the *current* index so a slow-arriving response can't insert behind
   where the session has already moved past. Verified live through a
   real Again → Good → Easy sequence on one card: requeued twice (each
   rating short of graduating), then correctly stopped requeuing and let
   the session complete once Easy graduated it to `review`.
4. **Dashboard said "0 due" while Study still worked, found live by the
   user on a second deck right after the first fix.** The dashboard's
   due/new counts come from `useDeckStatsList`, a plain fetch-once query
   (30s `staleTime`) -- nothing re-renders it just because real time
   passes and a short learning-step card's `due_at` slips into the past,
   so it can go stale purely by sitting open, even though a fresh
   `/cards/due` fetch (what Study triggers) reflects it immediately.
   Fixed with `refetchInterval: 30_000` on that query -- polling is a
   deliberately simple fix for a single-user, local-scale app; revisit
   if this ever needs to scale beyond that.
5. **`CardState.SUSPENDED` cards showed as "New" in the deck list**,
   found while fixing #2: `formatCardStatus` treated `due_at === null`
   as sufficient for "New", but a locked production card also has a null
   `due_at` (never scheduled). Added an explicit `suspended` check ahead
   of that fallback, returning "Locked". Writing a test for this
   surfaced a second, unrelated, pre-existing bug in the same function:
   `Math.ceil`-ing a sub-day duration into a day count *before* checking
   `< 1` can never produce a value under 1, so the "N minutes" branch was
   dead code -- a card due in 5 minutes displayed "Due in 1 day". Fixed
   by comparing the raw millisecond duration against one day directly.

Verified: 20 frontend tests (5 new -- `format.test.ts`, covering New/
Locked/Due-now/minutes/days), `tsc`/`eslint` clean. All fixes confirmed
live in the browser, not just by test coverage: vocab-backed cards now
show real text with status + direction labels and no broken Edit
button on both the Spanish and Chinese decks; Quick-add absent from
Course/Vocabulary, present on Decks; a real Again-rated card visibly
reappeared later in the same session and the session still terminated
correctly once it graduated; the dashboard's due count matched
`/cards/due` without needing a manual reload.

**2026-08-14 — "Duplicate cards" reported after practicing the Chinese
deck; investigated and found to be a UX clarity gap, not a data bug —
fixed the display, not the data.** Queried Postgres directly (both the
Chinese course specifically and a `HAVING count(*) > 2` sweep across
every vocabulary item in the database) — no vocabulary item anywhere
has more than its intended 1 or 2 cards, and `reps` matches
`review_logs` count exactly per card, so reviewing (including the new
same-session requeue) isn't duplicating review submissions either. The
real cause: Chinese notes have always produced 2 real cards
(recognition + production, by design), but the previous round's fix for
"cards show blank text" made both suddenly show identical target/base
text for the first time — two rows reading "你好 → hello" with only a
small gray suffix distinguishing them looks exactly like an accidental
duplicate. Fixed by replacing that inline suffix with a visible pill
badge next to the word ("Recognition"/"Production"). Also added the
user-requested total-card count (`DeckStats.totalCards` already
existed, just wasn't displayed) to both the dashboard's per-deck rows
and its aggregate header. Verified live: Chinese Vocab's 8 rows (4
words × 2 practice modes) now read unambiguously as pairs, not
duplicates, and the dashboard shows "8 total" matching the direct
Postgres count exactly.

**2026-08-14 — Deck detail page gained a sort control** ("Recently
added" — the prior implicit order, by `created_at` — or "Alphabetical"),
requested right after the "duplicate cards" investigation above:
the recognition/production pairs read as less confusing sorted next to
each other in a stable, chosen order than in creation order. New pure
`lib/sortCards.ts` (tested, same convention as `deckStats.ts`/
`format.ts`) groups a dual-direction note's two cards together
(recognition before production) under both orders. Alphabetical sorts
by `attributes.transliteration` when a note has one rather than the
raw target text — sorting hanzi by Unicode code point doesn't read as
alphabetical the way sorting by its pinyin does. This is a generic
attribute-key check, not a Chinese-specific branch: any future language
populating the same `transliteration` key gets the same benefit for
free. Verified live: Chinese Vocab sorts 慢慢来/你好/谢谢/再见 as
màn → nǐ → xiè → zài (real pinyin order, not code-point order, which
would have put 谢谢 before 你好); Spanish Vocab sorts its three notes
alphabetically by the plain Latin text, unaffected by the
transliteration fallback since it has none.

**2026-08-14 — Second vocab-seed batch: 15 more Spanish notes, 12 more
Chinese notes.** User-authored (not this session's own content, unlike
the first three-per-language batch), provided as two JSON arrays with
field names checked against the real `VocabularyItemBase` schema
(`backend/app/schemas/vocabulary.py`) before importing — matched
exactly (`target_text`, `base_text`, `source`, `example_sentence`,
`example_sentence_translation`, `tags`, `attributes.transliteration`),
no field-name drift to reconcile. Imported by appending to the existing
`SPANISH_VOCAB_NOTES`/`CHINESE_VOCAB_NOTES` lists in `seed.py` — one
canonical list per language, not a second parallel constant, same as
every other content addition in this file — so `_seed_spanish_vocab_
notes`/`_seed_chinese_vocab_notes` and their shared `_seed_note` →
`build_cards_for_note` path needed zero changes. Chinese batch
deliberately excludes the four already-seeded words, confirmed no
overlap before importing.

Verified: re-ran the seed script twice, confirming idempotency (no
duplicate rows on the second run) — 18 Spanish notes × 1 card = 18
Spanish cards, 16 Chinese notes × 2 cards = 32 Chinese cards, both
counts confirmed directly in Postgres. `ruff`/`pytest` (88, unchanged —
seed content isn't itself test-covered) clean. Live in the browser: all
16 Chinese words show correctly with the new production cards starting
"Locked" (not "New") and recognition cards "New", confirming
`build_cards_for_note`'s dual-direction generation fired correctly for
every new note; the alphabetical sort correctly orders all 16 by pinyin
including the new entries (dìfang → duōshǎo → háishi → ... → zàijiàn);
all 18 Spanish notes show as single Recognition-only cards, alphabetical
by the plain Latin text.

**Also flagged (not started): TTS audio for vocab cards**, mainly for
Chinese tones. Proposed to mirror the `VocabularyExample` get-or-generate
cache pattern (an `audio_url` field or small cache table, generated once
via a TTS provider, served from cache after) — worth checking whether
Gemini's audio-out capability covers this before adding a separate TTS
API, so it could reuse the existing `LLMProvider` plumbing from Phase 5
slice 1 rather than a parallel integration. To be designed together
before building, same as the vocab-deck feature and the Phase 4
conjugation feature were.

**2026-08-14 — TTS audio for vocab cards, complete and verified end-to-end.**
Designed together first (plan mode), same pattern as the vocab-deck and
conjugation features. Landed on **Google Cloud Text-to-Speech**, not
Gemini's own TTS: Gemini's audio *output* isn't free-tier (input is;
output is $10-20/1M tokens) and the models are still preview-status,
while Google Cloud TTS has a genuine, generous free tier (1M chars/month
WaveNet, 4M/month Standard) that comfortably covers this app's lifetime
usage given the caching design. The real cost of this choice was setup
complexity, not money: a GCP project + service-account JSON keyfile,
more involved than every other credential in this project. New
`VocabularyAudio` cache table (one row per word, `unique=True` FK, unlike
`VocabularyExample`'s one-to-many), `app/services/tts.py` (owns
`google.cloud.texttospeech` the same way `fsrs_engine.py`/`llm/gemini.py`
own their libraries — deliberately *not* built as a swappable-provider
abstraction, matching this project's precedent of not adding
pluggability until a second real provider exists), and a new
`GET /vocabulary-items/{id}/audio` endpoint — the app's first binary
(non-JSON) response. `Language.grammar_config.tts` gates the feature
per-language (`{"language_code": ..., "voice_name": ...}`); Spanish and
Chinese have it, Dutch deliberately doesn't (out of the stated "mainly
for Chinese tones" scope). Frontend: `PlayAudioButton` (lazy `Audio()`
construction on first click, not on mount), wired into both
`VocabularyItemRow.tsx` and — the primary surface — `Flashcard.tsx`,
shown as a sibling overlay next to (not inside) the flip button, gated
to whichever face currently shows target-language text.

GCP setup was its own saga: no IAM role scoped narrowly to
Text-to-Speech reliably surfaces in the console's role picker (unlike
Speech-to-Text, which has several, confusingly-named-similarly roles) —
two specific guesses ("Cloud Text-to-Speech User", "Vertex AI User")
both failed to appear for the user's account even with the correct API
enabled. Settled on **Editor** as a deliberate, documented trade-off
(broader than ideal, but this is a dedicated single-purpose GCP project
and the credentials never leave the machine) — see `.env.example`.

**One real bug found once real credentials were live** (invisible with
the placeholder credentials/fakes, since it only manifests when a real
`TextToSpeechAsyncClient` is actually constructed): `get_tts_client` was
a sync function decorated with `@lru_cache`, so FastAPI's dependency
resolver ran it in a worker thread pool — but the client's grpc.aio
transport requires a running event loop *in the thread that constructs
it*, which anyio worker threads don't have (`RuntimeError: There is no
current event loop in thread`). Fixed by making it `async def` with a
manual module-level singleton instead of `@lru_cache` (FastAPI awaits
async dependencies directly on the real event loop, sidestepping the
thread pool entirely) — see `app/services/tts.py`.

Verified live end-to-end: ran `list_voices()` against the real API to
get actual Spanish/Chinese voice names (the plan's placeholder guesses,
e.g. `es-ES-Standard-A`, didn't exist — `es-ES`'s Standard tier starts
at `-E`); settled on WaveNet tier for both (best quality within the
confirmed free tier — Chirp/Studio voices are newer/premium, not
reliably free) and seeded them into `grammar_config.tts` for both
languages. Confirmed via direct API calls: real MP3 bytes returned
(valid MPEG frame headers) for both a Spanish and a Chinese word;
replaying returns byte-identical audio; Postgres holds exactly one
`vocabulary_audio` row per word even after repeated requests. Confirmed
in the browser: play buttons appear only for Chinese (not Dutch, which
has no `tts` config), and correctly only on whichever `Flashcard.tsx`
face shows target-language text (verified on a production card, no
button on the front, button appears on the back after flipping to the
target-text face). Actually *hearing* the output and clicking play
end-to-end in a real interactive browser was left to the user — the
automated browser-testing session had no audio output device, which
made `HTMLMediaElement.play()` hang indefinitely (matches every
"renderer frozen" symptom hit while trying); a direct `fetch()` to the
exact URL the button constructs, run from the page's own JS context,
confirmed the full round trip (new-word generation + persistence) works
correctly, isolating the audio-hardware gap as an artifact of the test
environment, not the app.

**2026-08-14 — Free-text grading (Phase 5, slice 2), complete and
verified end-to-end.** Closed a gap that had existed since Phase 1:
`ExerciseType.FREE_TEXT` and `UserExerciseAttempt.llm_feedback` were
already in the schema ("not graded here... Phase 5's LLM territory"),
but nothing had ever populated them — no FREE_TEXT exercise was seeded,
and the frontend fell through to "This exercise type isn't supported
yet." User decision: support two prompt sub-kinds under one FREE_TEXT
type, distinguished by which prompt field is present — flexible
sentence translation (`source_text`, any natural phrasing accepted,
unlike `TRANSLATION`'s exact-match) and open-ended short answer
(`question_text`, tests production, not just translation). New
`app/services/free_text_grading.py` (mirrors `sentence_generation.py`'s
shape), wired into `submit_lesson_exercise_attempt` alongside the
existing `CONJUGATION` branch. First real caller of the LLM provider's
`"reasoning"` tier (every other call site so far used `"fast"`) —
judging correctness fits the stronger model better than generating
example sentences did; flagged against PLAN.md's known tight
Gemini-free-tier-rate-limit issue since grading isn't cacheable the way
example generation is, but not a problem in practice at this app's
scale. Two sample exercises seeded into the Spanish Greetings skill (one
of each sub-kind). Frontend: `ExerciseCard.tsx` gained a `free_text` case
rendering a `<textarea>` instead of the single-line `<input>` every
other typed exercise gets, and a "Grading…" button label while the LLM
call is in flight; the lesson session page's feedback state — which had
carried only "correct"/"incorrect" since Phase 4, despite the response
schema having had `llm_feedback` available all along — now surfaces the
LLM's actual feedback text under the headline.

Verified live against the real Gemini API (not just fakes): submitted a
correct and an incorrect answer to both seeded exercises through actual
HTTP requests, confirming accurate grading and genuinely useful,
specific feedback text both ways (e.g. correctly identifying a wrong
answer as meaning "It is sunny today" instead of introducing yourself,
and naming the right phrase to use instead). Chased down what looked
like a UTF-8 mojibake bug in one response (`¡` rendering as two garbled
characters) — traced it to `python -m json.tool`'s stdin decoding on
this Windows/Git-Bash setup, not the app; confirmed by reading the same
response's raw bytes directly and checking the persisted value straight
from Postgres, both correct. Full session played through in the browser
end to end (multiple-choice → translation → fill-in-blank → both new
FREE_TEXT exercises), confirming the textarea, "Grading…" label, and
feedback text all render correctly and `UserProgress.mastery_level`
updates accurately for every exercise type in one queue. 99 backend
tests (9 new) and 36 frontend tests (5 new) pass; `ruff`/`tsc`/`eslint`
all clean.

**2026-08-14 — Vocabulary → Reading, known-vocabulary system, and
revised Phase 5 slice order (design decided, nothing built yet).** User
observation that prompted this: the Vocabulary course category
(Greetings/Family skills) already duplicated the Anki vocab decks with a
weaker mechanism (no spaced repetition), and got strictly worse once
free-text exercises landed on it — those exercises test recall of words
never taught within the lesson itself, testing without teaching. Not an
exercise-design problem; a wrong-content-slot problem.

**Vocabulary category retired, replaced with Reading.** `practice_categories`
(per-language config in `grammar_config`, rendered by
`frontend/src/app/course/category/[categoryKey]/page.tsx`, dispatching
entirely on a `kind` field — `"skill_list"` and `"conjugation_drill"`
today) already supports genuinely different UI shapes per category, so a
third `kind` for reading passages is a clean extension of an existing
mechanism, not new architecture. What Reading actually needs underneath
is not, though: every category today is pre-authored static
`LessonExercise` content, but reading passages are meant to be generated
on demand from the user's known vocabulary (i+1: known words plus a few
new ones) — structurally closer to `VocabularyExample`/`VocabularyAudio`'s
get-or-generate-and-cache pattern than to `Skill`/`LessonExercise`. That
data model (a new cache table, e.g. `ReadingPassage`) is deferred to its
own design pass when that slice actually starts, not solved now.
Comprehension questions after a passage, however, are a clean, direct
reuse of `app/services/free_text_grading.py` as built — same
`LLMProvider` → structured-result shape, one more prompt branch.

Retirement itself is config-only, not a data migration: remove the
`{"slug": "vocabulary", ...}` entry from `SPANISH_GRAMMAR_CONFIG`'s
`practice_categories` in `seed.py`. No model in this schema declares
`ondelete=CASCADE` anywhere, so the underlying Greetings/Family `Skill`,
`LessonExercise`, `UserProgress`, and `UserExerciseAttempt` rows
(including today's live free-text attempts) are left completely alone —
just unreferenced by the UI, not deleted, fully reversible. Note for
later: that category currently matches via `key: None` (any skill with
no `specialty_module`), the fallback bucket, not "Greetings/Family" by
name specifically — a future untagged skill would need its own category
after this change.

**New known-vocabulary system** (prerequisite for reading passages,
paste-in flagging, and coverage-gap analysis — not for journal
correction, which has no dependency on it). Explicitly separate from
Anki decks: decks are active-recall commitments (FSRS-scheduled,
due-queue), known vocabulary is a passive inventory with no scheduling.
Three pieces:
- **New table, not a flag on `VocabularyItem`.** `VocabularyItem` is
  course-scoped, requires a real `base_text` translation, and every row
  in a course renders unfiltered on `/vocabulary`
  (`useVocabularyItems`/`VocabularyItemRow.tsx`) plus is wired into
  TTS/example-generation. Bulk-marking an estimated frequency band as
  "known" would mean either creating hundreds of untranslated
  `VocabularyItem` rows (breaks that page and everything hung off it) or
  paying for an LLM translation per word for content the user explicitly
  isn't choosing to study. A separate lightweight table (`course_id`,
  `target_text`, `source: "placement_check" | "manual" | "promoted"`)
  avoids both — no translation needed unless a word is later promoted.
  Promotion (a one-way "add to deck" button, never automatic the other
  direction) is the moment a real `VocabularyItem` + `Card` get created,
  fetching a translation then, one word at a time — `Card.vocabulary_item_id`
  is nullable but promoted words should go through the full
  dual-direction/TTS/examples path, not `front_override`/`back_override`.
- **Opt-in, adaptive placement check** — not gated behind onboarding
  (there's no natural first-launch moment given the no-auth
  single-user bootstrap, and auth isn't moving up from Phase 8 for this).
  A standalone action (e.g. dashboard button), frequency-banded,
  ~20-30 items, self-report recognized y/n, adapts which band to test
  next. Needs no backend/LLM logic for the check itself — runs entirely
  against a bundled per-language frequency-band dataset; only the final
  "bulk-save the estimated band" step needs an endpoint. A true beginner
  in a language just skips it (zero known vocab is already correct,
  matches current behavior).
- **Known-words page** — view/search/edit, separate from the deck pages,
  with the promotion button from above.

Content generation should blend both signals: the frequency-band
estimate as a starting assumption, real known-words/deck data as ground
truth that increasingly overrides it as usage accumulates — a query
preference, not a migration/cutover point.

Frequency-list sourcing (verify licensing at build time, not locked in
now): avoid anything derived from Mark Davies' *Frequency Dictionary of
Spanish* (commercial book, not freely redistributable as raw data) — the
hermitdave/FrequencyWords dataset (OpenSubtitles-derived, openly
licensed, covers both Spanish and Chinese) is the likely open option for
Spanish. For Chinese, HSK level word lists (official, freely published,
already banded 1-9) are a better fit than a raw frequency list —
avoids inventing tier cutoffs. Different banding mechanism per language
is a `grammar_config` data difference, not a code branch, consistent
with this project's existing per-language-config convention.

**Revised Phase 5 slice order** (see the Phase checklist entry above):
journal correction + auto vocab extraction next (builds directly on the
free-text-grading engine just shipped, no dependency on the
known-vocabulary work above) → the known-vocabulary system above → reading
passage generation → paste-in content with unknown-word flagging (shares
logic with reading passages) → coverage-gap analysis vs. a CEFR/HSK-style
list (shares the known-vocabulary prerequisite — "cheap" in effort, but
not schedulable before that work exists) → adaptive weak-point targeting
last, deliberately, since it needs real attempt data from every earlier
slice to have anything meaningful to target. Chinese handwriting/stroke-order
practice deferred to sit alongside Phase 7 (Whisper) as a stretch goal,
not core Phase 5 scope.

**2026-08-14 — Journal correction + auto vocab extraction (Phase 5,
slice 3), complete and verified end-to-end.** Next slice per the
revised order above — builds directly on `app/services/free_text_grading.py`'s
`LLMProvider` → structured-result shape, no dependency on the
known-vocabulary system from the same decision. User writes freely in
the target language; gets a full corrected rewrite, one overall note,
and an itemized list of specific fixes (`{original, corrected,
explanation}`); any vocabulary used *correctly* that looks
new/intermediate-worthy is suggested for one-click addition to a deck.
Confirmed via clarifying questions before building: entries are
**persisted** (new `JournalEntry` table — the correction result is a
one-time snapshot of what was submitted, stored directly rather than
re-derived, unlike `LessonExercise.prompt`); corrections are
**itemized**, not just a single rewritten paragraph; new vocab is
**suggested, one-click accept per word** (reuses the existing `POST
/cards/quick-add` directly — no new backend surface for that step),
never auto-inserted; **misused vocab stays feedback-only**, no deck
action — a conjugation slip on a known word isn't a new card, the
itemized correction already teaches the fix (enforced by the LLM
prompt: `vocabulary_suggestions` explicitly excludes anything flagged
in `corrections`). New `app/services/journal_correction.py` (mirrors
`sentence_generation.py`/`free_text_grading.py`'s pure,
DB-free-service shape), `model_tier="reasoning"` (same reasoning as
free-text grading — judging a full paragraph and producing itemized
diffs needs it more than a single-sentence check did). Frontend:
`JournalEntryCard`/`VocabSuggestionRow` built presentational/
callback-driven (`onAddToDeck` prop, not an internal `useQuickAddCard`
call) specifically so they're unit-testable the same way
`ExerciseCard.tsx` is, with the real hook wired up one level higher in
`/journal/page.tsx` — the page itself follows this project's established
split of leaving hook-wired page components to live-browser
verification rather than unit tests.

Verified live against the real Gemini API: submitted a Spanish entry
with three deliberate tense mistakes plus a subtler word-choice error
("cocinar" vs "hacer"/"hornear" for baking) — all four caught accurately
with correct explanations, and the corrected rewrite was fully natural.
`vocabulary_suggestions` correctly included the two correctly-used new
words ("la tarta," "el mercado") and correctly excluded "cocinar" (the
misused one), confirming the exclusion instruction works in practice,
not just in the prompt text. Accepted a suggestion through the real
browser UI — confirmed a real `VocabularyItem` + `Card` were created
with `source: "Journal entry"` and the right `example_sentence`, and
the button correctly flipped to a disabled "Added" state. 105 backend
tests (6 new) and 41 frontend tests (5 new) pass; `ruff`/`tsc`/`eslint`
all clean. One test-only wrinkle worth remembering: Postgres's
`now()`/`CURRENT_TIMESTAMP` is transaction-start-time-stable, and this
project's test fixtures wrap each test in one transaction (see
conftest.py) — two rows inserted via back-to-back requests in the same
test can get identical `created_at` values, making `ORDER BY
created_at DESC` untestable via HTTP alone. Not a production bug
(separate real requests get separate transactions there); worked
around by inserting test rows directly through the DB session with
explicit, distinct timestamps rather than through the API when a test
specifically needs to assert ordering.

**Same-day follow-up: real duplicate-vocab bug found by the user, fixed.**
Using the shipped journal feature, the user found "la tarta" listed
twice on `/vocabulary` after accepting the same suggestion on two
separate visits. Root cause: the "Added" state on a vocab suggestion was
local React state only, resetting to "offered" on every page
reload/revisit; `POST /cards/quick-add` had no duplicate-checking at
all, so clicking an already-accepted suggestion again created a second,
fully duplicate `VocabularyItem` + `Card`. User's fix direction: dedup
on the pair (target_text, base_text), not target_text alone, so
distinct senses of a homonym (e.g. Dutch "bank" → bank/couch/bench)
still get their own entry.

Fixed in two layers. **Backend**: `quick_add_card` (`app/api/routes/cards.py`)
is now idempotent, accent/case-insensitive, on (course, target_text,
base_text) — reuses an existing `VocabularyItem` and just adds a card if
this deck happens to be missing one for it, instead of creating a
duplicate; a different `base_text` for the same `target_text` still
creates a separate note. The accent/case-insensitive comparison
(`exercise_grading.py`'s private `_normalize`, originally built for
answer grading) got promoted to a shared `app/services/text_normalize.py`
once quick-add became a second real caller — `exercise_grading.py` now
imports it too, no behavior change there. **Frontend**: `JournalEntryCard`/
`VocabSuggestionRow` no longer track "added" as local-only state at
all — `added` is now derived every render from whether a matching item
(same accent/case-insensitive normalization) already exists in the
course's real vocabulary list (`useVocabularyItems`, already fetched on
`/vocabulary`), which the "add" mutation's existing cache invalidation
naturally keeps fresh. This closes the root cause, not just the
symptom: the button can no longer lie about whether a word was already
added, regardless of reloads or revisits.

Verified: 108 backend tests (3 new, covering idempotent reuse, the
homonym case staying separate, and reuse-across-decks) and 45 frontend
tests (4 new, covering the render-as-already-added case, accent/case-
insensitive matching, the homonym case NOT being flagged as a
duplicate, and the reactive re-render-as-Added-after-add path) pass;
`ruff`/`tsc`/`eslint` all clean. Cleaned up the one duplicate "la tarta"
row that had already been created in the dev DB. Confirmed live in the
browser: revisiting `/journal` now shows "Added" (disabled) immediately
for a previously-accepted suggestion, no click required.

**2026-08-14 — Known-vocabulary system (Phase 5, next slice per the revised
order), complete and verified end-to-end across all three languages.**
Designed together first (plan mode), building on the high-level shape
already decided earlier the same day (separate table, promotion
semantics, opt-in placement check, known-words page — see the
"Vocabulary → Reading, known-vocabulary system" entry above). Two things
that entry deliberately left open got resolved this session: real
frequency data (not a placeholder set), and Dutch in scope alongside
Spanish/Chinese from day one.

**Data sourcing**: Spanish/Dutch from hermitdave/FrequencyWords (2018
OpenSubtitles-derived, `content/2018/<lang>/<lang>_50k.txt`, MIT code +
CC-BY-SA-4.0 content, attributed in the bundled JSON) — top 4,000 words
per language, filtered to letters-only tokens, rank-split into 10 even
bands. Chinese from drkameleon/complete-hsk-vocabulary (MIT, HSK 3.0
*exclusive* per-level lists so bands represent genuinely new words, not
cumulative) — 7 bands, one per official level, with 7-9 combined into a
single "advanced" band rather than an invented 3-way split (HSK 3.0
itself doesn't split them further, and inventing tier cutoffs was
exactly the failure mode this data source was chosen to avoid — see the
Known Issues entry it resolves). Bands committed as static JSON
(`frontend/src/data/frequencyBands/{es,nl,zh}.json`) with a plain
lookup-by-`Language.code` loader — no per-language branching, no backend
involvement (the check itself needs no server/LLM logic, matching the
original design).

**Schema**: new `known_vocabulary_items` table (`course_id`,
`target_text` stored lowercased, `source` enum
`placement_check`/`manual`/`promoted`, `UniqueConstraint(course_id,
target_text)`). Deliberately a real DB constraint plus
`INSERT ... ON CONFLICT DO NOTHING`, not `VocabularyItem`'s app-level
accent/case-insensitive Python scan — justified by volume (a single
placement-check bulk-save can insert thousands of rows from a fixed,
already-lowercased dataset) rather than low-volume typed input.
`promoted` is a status a row transitions to in place, not a deletion or
a separate table — keeps a single persisted signal the known-words page
filters on directly without cross-referencing the full `VocabularyItem`
list every render.

**Backend**: new `app/services/word_translation.py` (pure, `LLMProvider`
→ single-word translation, `model_tier="fast"`) — the promote flow's own
LLM call, since known-vocabulary rows never store a translation. Real
DRY refactor: extracted `quick_add_card`'s inline "resolve-or-create
`VocabularyItem` + `Card`s" logic into
`app/services/note_cards.py::get_or_create_vocabulary_item_and_cards`,
so the new promote endpoint reuses the exact same dedup identity
(accent/case-insensitive on `target_text` + `base_text`) instead of
duplicating it — verified behavior-preserving by re-running the full
existing suite unchanged immediately after the refactor, before writing
any new code. New `app/api/routes/known_vocabulary.py`
(`GET`/`POST`/`POST /bulk`/`DELETE`/`POST /{id}/promote`), same
flat-router-plus-query-param convention as `/vocabulary-items` and
`/cards`. 9 new backend tests (117 total), `ruff` clean.

**Frontend**: `lib/placementCheck.ts` — a pure binary-search state
machine over the ordered bands (3 deterministically-sampled words per
band tested, not random, so the check is reproducible; a 30-item budget
as a safety cap, not a target — real runs converged in 9-13 items across
all three languages). New top-level `/known-vocabulary` section
(list/search/manual-add/promote/delete + `/placement-check` sub-route
mirroring the lesson session's one-item-at-a-time shape), `CourseSwitcher`
gained a `/known-vocabulary` branch (the same bug class already fixed
once for `/vocabulary`), `Nav` gained a link with quick-add kept hidden
here. 6 new `placementCheck.test.ts` cases (pure) + 5 new
`KnownVocabularyRow.test.tsx` cases (presentational, same
props-in/callbacks-mocked convention as `VocabSuggestionRow`) — 56
frontend tests total, `tsc`/`eslint` clean.

**Verified live end-to-end against the real Gemini API, all three
languages, not just fakes**: manual-add/search/delete on `/known-vocabulary`;
promoting "hola" (already a seeded `VocabularyItem`) correctly reused the
existing note rather than duplicating it — a real, unplanned exercise of
the dedup path against genuine pre-existing data; promoting "biblioteca"
(genuinely new) produced a real Gemini translation ("library", noun) and
a fresh `VocabularyItem` + `Card`, with the known-vocabulary row's badge
flipping to "Promoted" and its promote control disappearing. Took the
full placement check for Spanish (2,400-word estimate = 6 bands × 400,
converged in 12 questions), Chinese (2,209 = HSK 1+2+3 exactly, 9
questions), and Dutch (800 = 2 bands × 400, 9 questions) — every band
count confirmed directly against Postgres. Retaking the Spanish check
with an identical answer sequence reproduced the identical 2,400-word
estimate (confirming deterministic sampling) and inserted zero
additional rows (confirming `ON CONFLICT DO NOTHING` idempotency).
Confirmed switching courses on `/known-vocabulary` stays on
`/known-vocabulary` for all four courses in the dev DB, including a
leftover `Language`-code-collision test course from earlier Phase 3
verification (`Spanish P2`) — correctly showed no placement-check entry
point at all, since its language code doesn't match the bundled data's
lookup key, the intended graceful-degradation behavior rather than a bug.

**2026-08-14 — Reading passage generation (Phase 5), complete and verified
end-to-end across Spanish and Chinese.** The next slice per the revised
order, and the one that finally executes the other half of the same-day
"Vocabulary → Reading" decision: retiring the Vocabulary practice category
in favor of Reading. Designed together first (plan mode), same pattern as
every other Phase 4/5 feature.

**Known-vocabulary blending, implemented as designed**: new
`app/services/known_vocabulary_lookup.py::get_known_words_for_passage`
unions two signals — `Card`s graduated to `REVIEW` state (ground truth,
always included in full, no new tuned threshold) and a random sample of
`KnownVocabularyItem` rows (the placement-check/manual estimate, capped at
300 to keep prompt size reasonable and give regenerated passages variety
instead of always drawing the same common words).

**Schema**: new `reading_passages` (`course_id`, `target_text`, `base_text`,
`new_vocabulary` JSONB, `questions` JSONB — each question stores a
server-only `reference_answer` never sent to the client) and
`reading_passage_attempts` (field names deliberately mirror
`UserExerciseAttempt`'s `is_correct`/`llm_feedback`, for the later adaptive
weak-point-targeting slice). Confirmed via exploration that `Skill`/
`LessonExercise` are pre-authored, identical-for-every-user, course-shared
content — reading passages are per-course, LLM-generated, and accumulate
many-per-course over time, so they're structurally closer to `JournalEntry`
(`POST`-to-generate/`GET`-to-list) than to either the `Skill` shape or the
`VocabularyExample`/`VocabularyAudio` single-cached-resource GET pattern
(neither existing cache table's uniqueness constraint fits "many per
course, generated on demand").

**Comprehension questions are free-text, LLM-graded** (confirmed with the
user over multiple-choice or no-grading-this-slice alternatives) — matches
this project's stated retrieval-practice preference. New
`app/services/reading_passage_generation.py` (one `model_tier="reasoning"`
call producing the passage, its translation, self-reported new vocabulary,
and 3 questions with reference answers in one structured response, mirroring
`journal_correction.py`'s multi-field-with-nested-lists shape) and
`app/services/reading_comprehension_grading.py` (mirrors
`free_text_grading.py` field-for-field). New `app/api/routes/reading_passages.py`:
`POST ""` generates+persists, `GET ""` lists course-scoped/most-recent-first,
`POST "/{id}/attempt"` grades+persists (400 on an out-of-range
`question_index`).

**Content**: `seed.py`'s `practice_categories` — Spanish/Dutch's `"vocabulary"`
entry replaced with `{"slug": "reading", "kind": "reading_passage"}`; the old
Greetings/Family `Skill` rows left untouched (no `ondelete=CASCADE`
anywhere in this schema), just unreferenced by the UI, fully reversible.
**Chinese also gained a `practice_categories` key for the first time** —
just the one Reading entry, since reading passages need zero pre-authored
lesson content, a genuine test of "language-agnostic by design" for a
language that has literally no `Skill` rows in this app.

**Frontend**: `/course/category/[categoryKey]/page.tsx` gained a third
`kind` branch (`"reading_passage"`) — a generate button + a list of past
passages, no `Skill`/`useLessonExercises` involvement. The reading view
itself, `/reading-passages/[passageId]/page.tsx`, is a new **top-level**
route (not nested under `/course/category/...`) — Next.js can't have two
differently-named dynamic segments (`[tenseKey]` already exists at that
path position) at the same position, and the existing precedent for a
session-style leaf page (`/skills/[skillId]/lesson`) is already a
standalone top-level route reading `useBootstrapContext()` directly rather
than nesting under `/course`. New vocabulary → deck reuses the exact
`VocabSuggestionRow` pattern (`NewVocabularyRow.tsx`, `useQuickAddCard()`
wired one level up in the page) — same derive-"added"-from-the-real-
vocabulary-list approach the duplicate-vocab bug taught this project to use
instead of local-only state. Comprehension questions render independently
(not a sequential drilled queue like the lesson session) since they're
short-answer questions a reader tackles at their own pace.

**Verified**: 17 new backend tests (134 total: 4 known-vocabulary-lookup
integration, 8 generation/grading unit, 5 route integration — one hit and
fixed the same `now()`-is-transaction-start-time-stable ordering gotcha
`test_journal_entries.py` hit before, worked around the same way, inserting
rows directly via `db_session` with explicit distinct timestamps), `ruff`
clean. 62 frontend tests (6 new `NewVocabularyRow` cases), `tsc`/`eslint`
clean. **Live, against the real Gemini API, both Spanish and Chinese**:
generated a real, natural Spanish passage about a stranger in a park from
real known-vocabulary data, answered one comprehension question correctly
and one deliberately wrong — grading was accurate both ways, with the
wrong-answer feedback correctly quoting the passage's actual text back
("dice que el desconocido 'lleva ropa verde', no azul"); added a
new-vocabulary word to a deck and confirmed a real, immediately-"Added"
`VocabularyItem`+`Card` in Postgres; generated a genuinely natural Chinese
passage (market/restaurant story) using zero pre-authored `Skill` content
in that course, confirming the architecture claim for real, not just in
theory. **Hit real, transient Gemini 503 "high demand" errors on the
reasoning-tier model during testing** (both languages, resolved on retry
within roughly a minute) — confirmed not a bug by checking another
reasoning-tier endpoint (`journal-entries`) succeeded immediately in
between failed retries; consistent with this project's already-documented,
accepted free-tier flakiness trade-off, not something this slice needs to
handle specially.

**2026-08-14 — Paste-in content with unknown-word flagging (Phase 5),
complete and verified end-to-end across Spanish and Chinese.** The mirror
image of reading-passage generation: known-words → generated text there,
arbitrary user text → flagged unknown words here. Designed together first
(plan mode), same pattern as every Phase 4/5 feature. Confirmed with the
user up front: Chinese gets real word segmentation via `jieba` (new
backend dependency) rather than being excluded from this slice, since
naive splitting would flag individual characters instead of words. First
Phase 5 slice with **zero schema/migration changes** — deliberately
stateless (no reason to persist a verbatim copy of pasted, often
third-party text the way `JournalEntry`/`ReadingPassage` persist actually
generated content).

**Known-vocabulary lookup gained an uncapped variant.** The existing
`get_known_words_for_passage` (in `known_vocabulary_lookup.py`) samples
estimated words down to a 300-word prompt budget — wrong for flagging,
where under-counting known words would falsely flag things the user
actually knows. Refactored to share the two underlying queries (mastered
`Card`s in `REVIEW`; all `KnownVocabularyItem` rows) between that function
and a new `get_full_known_word_set` (uncapped, normalized via the same
`normalize_for_comparison` quick-add already uses, for exact membership
testing).

**Tokenizer — `app/services/paste_in_tokenizer.py`**: `tokenize(text,
grammar_config)` returns `(segment_text, is_word)` pairs that reconstruct
the input exactly when joined, so the frontend renders highlights without
re-deriving anything. Branches on `grammar_config.get("tokenization",
"whitespace")` — a config value, not a language-identity check, matching
`script_direction`/`vocab_deck`'s existing convention. Whitespace mode
(Spanish/Dutch default) is `re.split` on Unicode word-character runs
(accented letters work for free, purely numeric tokens excluded from
word-hood by construction). CJK mode (`Chinese` grammar_config now sets
`"tokenization": "cjk"`) uses `jieba.tokenize`, which — verified directly
against real Chinese text before committing to it — segments the *entire*
input including punctuation as its own tokens, so classifying a segment as
a word is just "does it contain a CJK ideograph."

**Batch translation extends `word_translation.py`** rather than adding a
parallel file — `translate_words(llm, ..., words: list[str])` — one LLM
call for however many unknown words a pasted article has, instead of one
call per word. New `BatchWordTranslation` carries its own `target_text`
per item (unlike the single-word `WordTranslation`) since a structured
list response isn't guaranteed to preserve positional order.

**A real bug, found live, not by review**: the first end-to-end test
showed every translation backwards — `target_text` held the English
translation, `base_text` held the original Spanish word, exactly reversed
from this project's actual convention. Root cause: the prompt named the
output fields (`target_text`/`base_text`) without ever saying which
language each one meant — Pydantic field names alone gave the model
nothing to infer that from, so it guessed "target" meant "the target of
the translation" (the output) rather than "text in the target language."
Fixed by making the prompt spell out the mapping explicitly (`target_text
is the original {target_language_name} word exactly as given ...
base_text is its {base_language_name} translation`); added a regression
test asserting that exact instruction is present in the prompt, and
manually deleted the one bad row the live test had already written before
re-verifying. Worth remembering as a general pattern: structured-output
field *names* are not self-documenting to the model just because they're
self-documenting to the humans reading this codebase's other services —
anywhere a field's meaning depends on which of two languages/directions is
which, the prompt needs to say so outright, not rely on the schema alone.

**A second, smaller gap found and fixed alongside it**: `CourseSwitcher`
already had two prior "a new top-level section forgot to add itself to
`handleChange`" incidents (`/vocabulary`, then `/known-vocabulary`) — while
adding `/paste-in`'s entry, found that `/journal` had the exact same gap
and had simply never been reported. Refactored the growing ternary chain
into a flat `SWITCHER_SECTIONS` list (`/vocabulary`, `/known-vocabulary`,
`/journal`, `/paste-in`) with a `.find()`, both fixing the latent
`/journal` bug and making the next section's entry a one-line addition
instead of another nested ternary branch.

**Shared component/schema promoted, not duplicated**: `NewVocabularyRow`
moved from `components/readingPassage/` to `components/vocabulary/` (zero
reading-passage-specific logic, and paste-in needed the exact same
word+translation+add-to-deck shape); `NewVocabularyWord` moved from
`schemas/reading_passage.py` to `schemas/vocabulary.py` for the same
reason on the backend.

**Verified**: 19 new backend tests (153 total: 7 tokenizer unit tests
against real `jieba` calls rather than a fake, since it's deterministic
and fast; 3 uncapped-lookup cases; 4 batch-translation cases including the
field-semantics regression test; 5 route integration tests), `ruff`
clean. 62 frontend tests unchanged in count (component
relocation, not new coverage), `tsc`/`eslint` clean. **Live, against the
real Gemini API, both Spanish and Chinese**: pasted Spanish text mixing
common words already in the 2,400-word known set (correctly left
unhighlighted: "amiga," "cómo," "estás") with three genuinely obscure ones
("bibliotecario," "esdrújula," "tranquilamente" — correctly highlighted
and translated); pasted Chinese text where `jieba` merged "很漂亮" into one
two-character segment and correctly flagged/translated it as a unit
("very beautiful"), not per-character, while correctly recognizing
"图书馆" (library) as already-known from the HSK-derived known-vocabulary
data. Add-to-deck confirmed correct (post-fix) in Postgres for both
scripts, with `target_text`/`base_text` in the right language each time.

**2026-08-14 — Paste-in follow-up, same day, from real usage: dictionary-form
translations + a "Mark as known" action, both verified live.** The user
tried the shipped feature and reported every conjugated surface form
("susurra", "susurraron", ...) was being recorded as its own separate
vocabulary word instead of one card for the verb.

**Dictionary-form fix**: `translate_words`' prompt (`word_translation.py`)
now explicitly asks for each word's dictionary/citation form — infinitive
for a conjugated verb, singular for a plural noun, masculine singular for
an inflected adjective — as `target_text`, translating *that* form rather
than echoing the literal inflected word encountered. No new dependency: the
same batch LLM call already being made just does more work per call.
Multiple distinct input words legitimately collapse to the same output
this way (e.g. "susurra" and "susurraron" both → "susurrar") — the
`/paste-in/translate-unknown-words` route now dedupes the result list by
normalized `target_text` before returning, so the glossary doesn't render
the same word twice. Quick-add's own pre-existing idempotency (dedup on
course + target_text + base_text) already makes a second add-to-deck click
for the same lemma a safe no-op, which is what makes "record the
infinitive if not already in the deck" work correctly for free once
`target_text` is consistently the lemma. Regression tests added for both
the dictionary-form instruction and the route-level dedup.

**"Mark as known" action**: `NewVocabularyRow` (shared by reading-passage
generation and paste-in) gained a second, independent action alongside
"Add to deck" — reuses the known-vocabulary system's existing manual-add
endpoint (`useAddKnownVocabulary`, `source: "manual"`), no new backend
surface needed. Its "already known" state derives from the real
known-vocabulary list the same way "Added" derives from the real
`VocabularyItem` list (not local-only state, per the duplicate-vocab bug
this project already fixed once) — wired into both pages that render the
component.

**Verified live**: pasted "Ella susurra un secreto. Ellos susurraron toda
la noche." — both conjugations highlighted correctly in the text, but the
glossary correctly showed one row, "susurrar → to whisper"; clicked "Mark
as known" (persisted to `known_vocabulary_items` with `source: "manual"`,
button correctly flipped to disabled "Known") and separately "+ Add to
deck" (persisted to `vocabulary_items` as `target_text: "susurrar"`, not
either conjugated surface form). 2 new backend tests (155 total), 4 new
frontend tests (66 total), all existing suites still green,
`ruff`/`tsc`/`eslint` clean.

**2026-08-14 — Coverage-gap analysis vs. a CEFR/HSK-style list (Phase 5), complete
and verified end-to-end.** Crosses the two existing known-vocabulary data
sources against the bundled frequency-band/HSK reference data: for each band,
how much of it the user actually knows, and which specific words are the
gaps. Deliberately reused more than it built: a new thin `GET
/known-vocabulary/full-set` endpoint is the only backend addition (returns
`get_full_known_word_set`'s existing union of mastered `Card`s +
`KnownVocabularyItem` rows, sorted, uncapped — the paste-in slice's lookup
already did the real work); the "close this gap" action doesn't add new
review UI at all, it sends the user into the already-built paste-in flow
(tokenize → flag → batch-translate → add-to-deck/mark-known), pre-filled with
that band's missing words via `/paste-in?text=...`, rather than a third
translate-and-review UI. New pure `lib/coverageAnalysis.ts`
(`computeCoverage`) and a presentational `CoveragePanel` (aggregate stat,
per-band progress bar, expand-to-see-gap-words, capped "Review these words"
link) wired into `/known-vocabulary`.

**A real, reproducible bug found and fixed live, not by review**: clicking
"Review these words" lands on `/paste-in?text=...`, which auto-runs analysis
on mount instead of making the user click Analyze again. The first version of
that auto-run (`useEffect` calling `analyze.mutateAsync` directly, guarded by
a `useRef` so React Strict Mode's dev-only double-invoke didn't fire it
twice) reproducibly got stuck showing "Analyzing…" forever — even though the
backend had already returned 200 OK. Root-caused by inspecting the
QueryClient's mutation cache directly (`getMutationCache().getAll()`): the
mutation had genuinely resolved to `"success"` in the cache, but the
component's own `analyze.isPending` never flipped, meaning the hook's
subscription didn't survive Strict Mode's synchronous mount → cleanup →
remount cycle intact. Confirmed dev-only by toggling `reactStrictMode: false`
in `next.config.ts`, which made the bug disappear entirely — production
builds never double-invoke, so real users could never hit this. Fixed
properly (Strict Mode left on) by deferring the `mutateAsync` call with
`setTimeout(..., 0)` inside the effect, with a cleanup that clears the timer;
the ref guarding "has this already run" isn't flipped until the timer
actually *fires*, so the phantom first invocation's timer gets cleared by its
own cleanup before it runs, and only the second, real, settled effect
instance's timer fires — landing the `mutateAsync` call safely after Strict
Mode's double-invoke dance has already finished. Re-verified 3x live after
the fix: direct URL navigation (twice, fresh tabs) and the real
`<CoveragePanel>` → `<Link>` click-through path, all landing cleanly with the
highlighted text and translated (correctly lemmatized) glossary rendered on
the first try.

**Verified**: 1 new backend test (156 total), `ruff` clean. 6 new
`coverageAnalysis.test.ts` tests + 7 new `CoveragePanel.test.tsx` tests (79
frontend tests total), `tsc`/`eslint` clean. Live: `/known-vocabulary` for
Spanish showed real per-band stats (2,439/4,000 words, 61% — fully known
through rank 2,400, then dropping to 2-3% beyond it, matching the known
dev-DB word counts from earlier sessions); expanded a bare band, confirmed
gap words and a capped "Review these words" link only appear when
`gapWords.length > 0`; clicked through into paste-in and confirmed every
flagged gap word matched what the coverage panel reported missing.

**2026-08-15 — Adaptive weak-point targeting (Phase 5, final slice), complete
and verified end-to-end.** Last remaining Phase 5 slice, deliberately saved for
last since it needs real attempt data from every earlier slice to have anything
meaningful to surface — that data now exists from this session's own extensive
testing. Confirmed with the user (AskUserQuestion) on three open design
questions before building: **surface** is a new section on the dashboard (`/`,
above the deck list) rather than a `/course` category or a new standalone
page/nav item; **signals** blend all three available sources (FSRS `Card`
lapses, per-word lesson-exercise accuracy, per-skill mastery) rather than
picking one; **action** is v1-scoped to a ranked list linking into existing
review/lesson flows, no new LLM generation this slice.

**Backend**: new `app/services/weak_points.py`, three independent queries —
`get_weak_cards` (`Card.lapses >= 1`, joined through `Deck` for
user/course scoping and the review link, cards with no `vocabulary_item_id`
excluded), `get_weak_lesson_words` (`UserExerciseAttempt` joined through
`LessonExerciseVocabulary` — the join table `lesson_exercise.py` already
flagged as built for exactly this — grouped by `(word, skill)`, not word
alone, so a word drilled in multiple skills surfaces once per skill), and
`get_weak_skills` (plain `UserProgress.mastery_level` — already exactly this
signal, needing no new computation, maintained incrementally by
`submit_lesson_exercise_attempt`). All three share `MIN_ATTEMPTS = 2` /
`MAX_ACCURACY = MAX_MASTERY = 0.7` thresholds so a single wrong answer never
reads as "weak." New `GET /weak-points?user_id=&course_id=` (both required)
bundles all three into one `WeakPointsResponse`. 5 new tests (161 total, all
passing on the first run), `ruff` clean.

**Frontend**: `WeakPointsPanel` (presentational) renders up to three
sub-sections — a sub-section with no items doesn't render, and the whole panel
doesn't render if all three are empty (a fresh course with no attempt history
shows nothing, not empty headers). Weak cards link to
`/decks/{deck_id}/review`; weak lesson words and weak skills both link to
`/skills/{skill_id}/lesson`. Wired into `frontend/src/app/page.tsx`.

**A real gap found and fixed live, not by review**: the dashboard (`/`) has
no `CourseProvider` in its tree — unlike every other top-level section
(`course/`, `journal/`, `known-vocabulary/`, `paste-in/`, `vocabulary/`, each
with their own `layout.tsx` instantiating one), because the dashboard's deck
list has always deliberately spanned every course, never needing course
scoping before. `useCourseContext()` threw immediately on load
("`useCourseContext` must be used within `CourseProvider`"). Fixed by
splitting `page.tsx` into an exported `DashboardPage` that wraps a new
`DashboardContent` in `<CourseProvider>` — same "re-instantiated per section,
not shared from the root layout" convention as the others, just living in
`page.tsx` itself since `/` has no dedicated route-segment folder to hang a
layout.tsx off of. Deliberately no `CourseSwitcher` added to the dashboard
(the deck list still isn't course-filtered; a switcher that only visibly
affects one panel would be confusing) — `selectedCourseId` falls back to the
bootstrap course by default, same as everywhere else.

**Verified live**: with the currently-selected course (Chinese) genuinely
having zero qualifying weak points, the panel correctly rendered nothing
(confirmed both via direct `curl` and the browser). Switched to Spanish (real
accumulated data): the panel showed "Desire / Wish — 67% mastery" under
Skills to revisit, correctly landing on that skill's lesson intro screen when
clicked. Submitted one real "Again" FSRS review live to produce a genuine
`lapses: 1` on an existing card, confirmed it then appeared under Struggling
flashcards and correctly linked to `/decks/{deck_id}/review` (landing on that
deck's live due-queue, not necessarily that exact card, since the queue is
due-only — a known, documented simplification, not a bug). `weak_lesson_words`
wasn't separately live-tested (no real data currently crosses its threshold)
but shares the identical link code path already confirmed for weak skills,
on top of its own dedicated backend and frontend tests. 6 new
`WeakPointsPanel.test.tsx` tests (85 frontend tests total), `tsc`/`eslint`
clean.

**2026-08-15 — Mnemonics gap closed, Phase 5 now fully checked off.** The
2026-08-13 Phase 5 kickoff decided mnemonics would fold into the existing
example-generation endpoint as an extra field rather than get its own slice,
but that field was never actually added -- found and flagged while closing
out the weak-point-targeting slice's PLAN.md updates. Small and well-scoped,
confirmed with the user before starting (fix now vs. defer alongside Phase 6
-- chose now).

One mnemonic per *word*, not per example sentence: `ExampleSentenceList`
(`app/services/sentence_generation.py`) gained a `mnemonic: str` field
alongside its existing `examples` list, generated in the same LLM call via
one added prompt clause ("a vivid mental image, a sound-alike, or a
word-association trick"). Persisted onto `VocabularyExample` (new nullable
`mnemonic` column, migration `d8e4f21a9c6b`) -- duplicated onto all 3
generated rows for a word rather than pulled into a separate envelope
object/table, since a mnemonic is conceptually one-per-word and this avoids
an API contract change to the existing `list[VocabularyExampleRead]`
response shape. Nullable, no backfill: pre-existing cached example rows
(generated before this field existed) simply show no mnemonic until
naturally regenerated -- `get_vocabulary_item_examples`'s get-or-generate
caching means that's effectively permanent for already-cached words, an
accepted tradeoff for a small addendum feature. Frontend shows it once
(from `examples[0].mnemonic`) above the example sentences in
`VocabularyItemRow`, not per-row.

**A real, unrelated bug hit live while verifying**: after editing the
backend model/schema/service/route, the running `uvicorn --reload` process
logged "WatchFiles detected changes... Reloading..." but the actual
worker kept serving with the *old* `VocabularyExample` mapping (confirmed by
inspecting the raw `INSERT` statement in the query log -- no `mnemonic`
column -- while a direct `information_schema.columns` query confirmed the
migration itself had applied correctly). A full kill of the process tree
(reloader + worker) and clean restart fixed it; root cause not fully
pinned down (Windows + `watchfiles` + multiprocessing spawn quirk, most
likely), but the underlying migration/model/code were never in question --
worth remembering that a "detected changes, reloading" log line isn't
proof the reload actually completed, if a subsequent request's behavior
looks stale.

**Verified**: 2 updated + 1 new test in `test_sentence_generation.py`, 1
updated test in `test_vocabulary_examples.py` (asserting the shared
mnemonic is duplicated across all persisted rows), one pre-existing test's
over-broad `"(" not in prompt` assertion tightened to check specifically
for the part-of-speech clause it was meant to test, now that the mnemonic
clause legitimately has its own parenthetical. 162 backend tests total,
`ruff` clean; frontend `tsc`/`eslint`/tests unaffected (no new frontend
tests needed -- straightforward type + rendering addition). Live: generated
examples for a never-before-cached word ("abajo") and confirmed the
mnemonic rendered correctly above the three example sentences, and that the
DB `INSERT` included the new column.

**2026-08-15 — Conversational practice partner (Phase 6), complete and verified
end-to-end.** Built as one MVP slice, not split further like Phase 5's
independent sub-features — a chat UI without scenarios has nothing to
roleplay, and scenarios without correction isn't "practice," so chat UI,
roleplay scenarios, and in-context correction shipped together. Confirmed
with the user (AskUserQuestion) up front: scenarios are a small pre-authored
list (same content-authoring pattern as `Skill`), not free-form topics; no
token-by-token streaming for v1 (plain request/response per turn, matching
every existing feature in this app).

**Real gap found during design exploration, before writing any code**:
`LLMProvider` (`app/services/llm/base.py`) was single-shot prompt-in/
structured-out only — no multi-turn message history. Every earlier Phase 5
feature could get away with that; a chat can't. Extended the Protocol with
`generate_chat_reply(system_prompt, history: list[ChatTurn], response_model,
model_tier)`, `GeminiProvider` implementing it via a real multi-turn
`contents` list (`types.Content` per turn) rather than concatenating
transcript into a single string. New `app/services/roleplay_chat.py` splits
into two functions rather than one: `start_conversation` (single-shot
`generate_structured` — no history yet, nothing to correct) and
`continue_conversation` (the new multi-turn path) — genuinely different
prompt framing, not an arbitrary split.

**Schema**: `RoleplayScenario` deliberately **not** course-scoped like
`Skill` — a situation like "order coffee" doesn't vary by target language,
only the language a given `Conversation` conducts it in does (avoids
seeding the same 6 scenarios once per course). `Conversation` accumulates
`ConversationMessage` rows over time per course, same "many rows, each a
persisted snapshot" shape as `ReadingPassage`/`JournalEntry`.
`ConversationMessage.corrections` is null (not `[]`) on assistant rows —
"no corrections" doesn't apply to them at all. `POST
/conversations/{id}/messages` persists the user's turn, replies via
`continue_conversation` (full prior history + this turn), and grades that
same turn in the same LLM call — the reply and the correction of what was
just said are one round trip, not two.

**Frontend**: new top-level "Roleplay" nav item (genuinely new feature,
unlike weak-points which fit inside an existing page) — `/roleplay`
(scenario picker + past-conversations list) and `/roleplay/[conversationId]`
(the chat). User messages show corrections inline underneath, reusing
`JournalEntryCard`'s exact corrections-list rendering pattern rather than
inventing a new one. The user's own message appears immediately on send
(local `pendingText` state, cleared once the mutation settles) rather than
waiting for the full round trip including the LLM reply — otherwise sending
would feel broken/laggy for a chat UI.

**Verified live against the real Gemini API**: started a conversation from
"Order coffee," got an in-character opening line in Spanish; sent a message
with two deliberate mistakes ("Yo quiere" wrong conjugation, "con leches"
wrong number) and got back precise, correctly-explained corrections for
both, with the reply staying fully in character and even echoing back the
scenario's own "here or to go" framing; continued for another turn and
confirmed real conversational memory (the final reply correctly referenced
"grande" and "para llevar" from the immediately preceding turn); resumed the
conversation from the picker page's history list and confirmed the full
transcript reloaded correctly. Hit one real transient 502 (Gemini free-tier
overload, same class of flakiness this project has documented before) on a
send — confirmed via query log that the whole request (including the
already-flushed user-message `INSERT`) rolled back atomically on failure, so
retrying produced no orphaned/duplicate row. 9 new backend tests (171
total: 4 pure `roleplay_chat.py` unit tests, 5 route integration tests via
an extended `FakeLLMProvider`), `ruff` clean. 5 new `MessageBubble.test.tsx`
tests (90 frontend tests total) — the two page components themselves
(`roleplay/page.tsx`, `roleplay/[conversationId]/page.tsx`) stay hook-wired
and left to live-browser verification only, per this project's established
convention. `tsc`/`eslint` clean.

**2026-08-15 — Known-vocabulary page now shows the full known set, not just
the tracked half.** User flagged the Vocabulary and Known-words pages as
feeling redundant. Diagnosis, not a merge: they answer different questions
(Vocabulary is the flashcard/deck catalog with study tools; Known words is
the calibration signal reading features -- passage generation, roleplay
chat, coverage-gap analysis -- use to know what *not* to re-teach), but the
Known-words page had a real gap: a word mastered purely through normal deck
review (never touched via placement check, manual add, or promotion) counts
as "known" everywhere `get_full_known_word_set` is used, yet never showed
up as a row on the page itself, since its list endpoint only ever queried
`KnownVocabularyItem`, not mastered `Card`s.

Fixed by adding `get_mastered_vocabulary_items` (`known_vocabulary_lookup.py`
-- `_get_mastered_words` now a thin wrapper over it, same join, no
duplicated query logic) and a new `GET /known-vocabulary/mastered` route
returning full `VocabularyItemRead` details, not just bare strings like
`/full-set` -- the page needs a translation to show, not just a word.
Existing `GET /known-vocabulary` (used by 3 callers: this page, paste-in,
reading-passages) deliberately left untouched; the new data is fetched via
a separate `useMasteredVocabulary` hook and rendered as its own "Mastered
flashcards" section, deduped against the tracked list by normalized
target_text so a promoted-then-mastered word doesn't appear twice. No
Promote button (already has a card) or Remove button (deleting a flashcard
is a real, more consequential action that belongs on the deck page) on
these rows -- read-only, matching what they actually are.

Also resolved in the same conversation: the native-language vocabulary
builder idea from Known Issues needs no engineering at all -- it's just an
ordinary deck in a base=target=English course. Marked resolved there.

**Verified**: 2 new backend tests (173 total: mastered-endpoint details +
excludes non-REVIEW cards, dedupes a word with multiple mastered cards
across directions), `ruff` clean. 2 new `MasteredVocabularyRow.test.tsx`
tests (92 frontend total), `tsc`/`eslint` clean. Live: real Spanish course
data showed 18 genuinely untracked mastered words in the new section;
confirmed the shared search box filters both sections correctly and that
the "no match" message for the tracked list points the user at the
Mastered flashcards section when a query matches there instead.

**2026-08-15 — Real multi-user auth kicked off (Phase 8); Slice 1 (backend
foundation + Google Sign-In) complete and verified.** User's explicit ask
alongside starting Phase 8. An audit before any design work found this is
the largest change in the project's history by far: almost nothing enforces
ownership today (`GET /decks` returns every user's decks, `GET /users`
lists every email, ~10 routes trust a client-supplied `user_id` outright
with zero verification), and the frontend silently creates/reuses one
hardcoded user (`frontend/src/lib/bootstrap.ts`). Confirmed with the user
(AskUserQuestion) on three decisions before any planning: **Course stays
shared/global** (matches how `Language` already works — personal content
gets `user_id` added in Slice 2, not this one); **Google Sign-In only**, no
password flow; **existing single-user dev data gets reassigned** to
whichever Google account first logs in, not wiped.

Sliced like Phase 4/5/6, checkpoint between each — Slice 1 scoped
deliberately narrow: prove the Google OAuth mechanism itself works, in
isolation, before building three more slices on top of it. Chose the
Google Identity Services **ID-token button flow**, not the full
authorization-code redirect flow — the button hands a signed JWT straight
to the frontend; the backend verifies it against Google's public keys
using only the (public) client ID. No client secret anywhere in this flow,
meaningfully simpler than a redirect+code-exchange dance for a project
this size, still genuinely real Google OAuth.

**Backend**: `User` gains a nullable, unique `google_sub` column (Google's
stable per-account id — never changes, unlike email). New
`app/services/auth.py`: `verify_google_id_token` wraps `google-auth`'s
verification (run via `asyncio.to_thread` since the underlying call is
blocking), exposed as a swappable `Depends` (`get_google_token_verifier`)
so tests never hit Google's network — same pattern `get_llm_provider`/
`get_tts_client` already established; `create_session_token`/
`decode_session_token` issue/verify a 30-day HS256 JWT signed with
`settings.secret_key` (already existed, already earmarked "for later
phases" before real auth existed). New `POST /auth/google`: existing
`google_sub` match -> log in; **nobody** has ever signed in for real yet ->
claim the oldest unclaimed row *in place* (update its identity fields,
not move any data -- every existing `user_id`-linked row, decks, journal
entries, conversations, already points at that same row's id, so
"claiming" it is a one-row `UPDATE`, not a migration); otherwise -> create
a genuinely new `User`. Sets an httpOnly `session` cookie
(`secure`/`samesite` flip together based on `settings.environment`,
matching `database.py`'s existing dev-vs-prod pattern). `GET /auth/me` /
`POST /auth/logout` round out the slice. `get_current_user`
(`app/api/auth.py`) exists as a dependency but is **not wired into any
existing route yet** — that's Slice 3. CORS `allow_credentials` flipped to
`True` (the block's own comment already flagged this as the deliberate
"no auth yet" simplification to revisit).

**A real test-isolation bug found live, not by review**: the first version
of the "claims the legacy row" test created its own fixture row and
asserted the response was *that* row — but the shared dev DB's real, much
older "Sanity" seed user is also an unclaimed row, and the route's "oldest
unclaimed row" query correctly (for the app) picked *it* instead, failing
the test. Not an application bug — confirms the claim logic will correctly
find and claim the real dev user once a real login happens — fixed by
giving the test's fixture row an explicit, deliberately-ancient
`created_at` (overriding the column's `server_default`) rather than fighting
the shared DB's real contents, worth remembering as a pattern for any
future test that queries "the oldest X" against this dev database.

**Frontend**: new `app/login/page.tsx` — `GoogleOAuthProvider` +
`<GoogleLogin>`, posts the credential to `/auth/google`, shows "Signed in
as {name}" (this slice's confirmation UI; redirect-to-dashboard behavior
is Slice 4's job once `BootstrapProvider` actually depends on this).
Deliberately not linked from `Nav.tsx` yet, and `BootstrapProvider` is
untouched — still silently creates/reuses its own user on every page,
including this one, for now. `lib/api/client.ts` gained `credentials:
"include"` (one line, every existing call site gets it for free) — needed
for the session cookie to be sent/received at all. New
`frontend/.env.example` (didn't exist before, though `NEXT_PUBLIC_API_URL`
was already used undocumented) plus `NEXT_PUBLIC_GOOGLE_CLIENT_ID`.

Automated verification: 8 new backend tests (181 total), `ruff` clean;
frontend `tsc`/`eslint`/92 tests unaffected, no new frontend tests needed
for a thin library-driven login page.

**Two real bugs found live, only reachable via the user's own Google Cloud
setup and a real sign-in attempt** (the one part of this slice no amount
of automated testing could substitute for): (1) `settings.google_oauth_client_id`
loaded as empty on the running backend even after the user added it to
`.env` — env vars only load at process startup, and uvicorn's `--reload`
watches Python file changes, not `.env` changes, so the fix was restarting
the backend, not a code change. (2) A genuine code bug alongside it: `POST
/auth/google` never caught `AuthError` from a failed verification, so it
leaked as a raw 500 with a stack trace instead of a clean 401 — fixed by
adding an `@app.exception_handler(AuthError)` in `app/main.py`, matching
the exact existing pattern `LLMError`/`TTSError` already use, rather than
a one-off local try/except (`get_current_user`'s own local catch, which
was already correct, stays as the more-specific-message path; the new
global handler is the safety net for every other call site).

**Live end-to-end confirmed working** after both fixes: signed in with a
real Google account, verified directly against the dev DB that the
legacy seed user's row was updated *in place* (`created_at` unchanged from
its original 2026-08-13 seed date, ruling out a new row) with the real
`email`/`display_name` from the Google account, and that all 4 of that
user's existing decks are still attached to the same `user_id` — zero data
loss, exactly as designed.

**2026-08-15 — Phase 8 auth Slice 2 (`user_id` on `VocabularyItem`/
`KnownVocabularyItem`/`ReadingPassage`), complete and verified end-to-end.**
Closes the data-isolation gap Slice 1 deliberately left open: before this
slice, every user shared one pool of personal vocabulary, known-words, and
reading passages on a course. A pre-planning investigation found a real
wrinkle — 12 seeded `VocabularyItem` rows (Greetings/Family skill vocab)
have no deck/card/owner and are referenced directly by shared
`LessonExercise` content — resolved with the user before designing further:
`VocabularyItem.user_id` is **nullable** (`NULL` = shared curriculum, a real
value = personal), while `KnownVocabularyItem.user_id`/`ReadingPassage.user_id`
are **not** nullable (every row there is inherently personal, no shared case).

**Migration** (`2be0ac4d09b6`) is hand-written past the autogenerate
skeleton, this project's first data migration (all prior ones were
schema-only): adds all three columns nullable first, backfills via
`op.execute` to the oldest `User` row (`ORDER BY created_at LIMIT 1` —
portable to an empty DB, where the backfill is just a no-op), with
`VocabularyItem`'s backfill excluding any row present in
`lesson_exercise_vocabulary` so the 12 curriculum rows stay `NULL`, then
`ALTER COLUMN ... SET NOT NULL` on the two non-nullable columns.
`known_vocabulary_items`'s unique constraint changes from
`(course_id, target_text)` to `(user_id, course_id, target_text)`. The
recurring unrelated `ix_cards_due_at` autogenerate-drift (see Known Issues)
was stripped a third time.

**Backend**: `note_cards.get_or_create_vocabulary_item_and_cards`'s note-dedup
lookup now scopes to `VocabularyItem.user_id == deck.user_id` (excluding
`NULL`/shared rows) and sets `user_id` on new notes — a real, intentional
behavior change: two different users' decks in the *same* course no longer
silently share a note for the same word (previously true, no longer is;
same-user multi-deck reuse is unaffected and still covered by a test).
`known_vocabulary_lookup.py`'s functions all gained a `user_id` parameter;
mastered-word lookups scope via a `Deck` join (mastery is "cards *you've*
studied," same join `weak_points.get_weak_cards` already uses) rather than
`VocabularyItem.user_id`, so a curriculum word mastered through your own
deck still counts as yours. Every route touching these three tables
(`known_vocabulary.py`, `vocabulary.py`, `reading_passages.py`,
`paste_in.py`, `conversations.py`) threads `user_id` through as a query
param (GET) or body field (POST) — `vocabulary.py`'s list is the one place
`user_id` is deliberately OR'd with `IS NULL`, so shared curriculum content
stays visible alongside personal words. This slice does **not** add
ownership *checks* (Slice 3's job) — it makes the data model correct and
every route pass the right `user_id` through, same client-supplied-param
convention the rest of the app already uses.

**Frontend**: `VocabularyItem`/`KnownVocabularyItem`/`ReadingPassage` types
gain `user_id`; `queryKeys.vocabulary`/`knownVocabulary`/`readingPassages`
all gain a `userId` segment (matching the existing `journalEntries`/
`weakPoints`/`conversations` convention); the 5 hooks and their API-client
functions thread it through; 7 page call sites updated (the plan's original
6 plus `known-vocabulary/placement-check/page.tsx`'s bulk-add, found only
by grepping for every real call site rather than trusting the plan's list).

**Tests**: extended `test_known_vocabulary.py`/`test_known_vocabulary_lookup.py`/
`test_reading_passages.py`/`test_quick_add_and_gating.py` with cross-user
isolation cases (same word, same course, two users — no collision, no
leakage); every other integration test touching these three tables across
the whole suite needed a `user_id` fixture added (9 files total) since the
fields are now required. One test (`test_first_ever_login_claims_the_legacy_row_in_place`,
Slice 1) started failing here for an unrelated reason — the shared dev DB's
real seed user now genuinely has a `google_sub` (from Slice 1's own live
verification), so the "nobody has ever claimed a Google identity" state the
test needs no longer exists on its own; fixed by resetting every row's
`google_sub` to `NULL` within the test's own (savepoint-rolled-back)
transaction before asserting, rather than fighting the shared DB's real
history.

**Live verification**: `alembic upgrade head` against the real dev DB
backfilled exactly as designed (49 personal `VocabularyItem` rows to the
real user, 12 curriculum rows stayed `NULL`, zero `NULL` rows left in
`known_vocabulary_items`/`reading_passages`). Two real, unrelated
environment issues found only by testing live end-to-end, not by the
automated suite: (1) two stray `uvicorn` processes were both alive on port
8000 (leftover from earlier in the session) — the live one was serving
pre-migration route code, so a real reading-passage generation attempt
through the browser 409'd on a NOT NULL violation; fixed by killing both
and starting one clean process, not a code change. (2) Immediately after
that kill, one request hit a `TimeoutError` acquiring a DB connection from
the pool — confirmed as a one-off blip coinciding with the process kill
(Postgres itself showed a single healthy connection right after), not
reproducible on retry. With a clean backend, `/vocabulary` correctly shows
both personal words and the Greetings/Family curriculum words together,
`/known-vocabulary` (list, full-set, mastered, coverage panel) all scope
correctly to the real signed-in user, and reading-passage generation +
detail-page rendering (new vocabulary, comprehension questions) work
end-to-end via both direct API calls and the real browser UI. Full
verification: 187/188 backend tests pass (`ruff` clean) — the one failure
is a pre-existing, unrelated test-timing flake (`test_due_queue_appends_new_cards_oldest_first_capped_at_new_limit`
uses a hardcoded `now() - 30min` "today" boundary that breaks in the ~30
minutes after UTC midnight, which this run happened to land in; confirmed
by wall-clock, not a Slice 2 regression); frontend 92/92 tests, `tsc`,
`eslint` all clean.

**2026-08-16 — Phase 8 auth Slice 3 (ownership checks on personal data),
complete and verified end-to-end.** A full route-by-route audit of all
~20 files in `backend/app/api/routes/` found the gap was larger than
PLAN.md's own placeholder note suggested — not just `decks.py`/`cards.py`/
`user_exercise_attempts.py`/`user_courses.py`, but also `review_logs.py`,
`conversations.py`, and every route Slice 2 had just added
(`known_vocabulary.py`, `vocabulary.py`, `reading_passages.py`). Before
designing further, confirmed the central sequencing question with the
user (AskUserQuestion): full session-derived identity (removing
client-supplied `user_id` entirely) isn't possible yet without also
forcing real Google sign-in everywhere, since `BootstrapProvider` still
never logs in — that's Slice 4's job. **Slice 3 stays narrower: every
route that reads or mutates a specific user's resource now verifies the
resource actually belongs to the `user_id` it's given**, closing "read/edit/
delete anyone's data by guessing an ID" without yet closing "claim to be
any user_id," which is inherent to client-supplied identity.

**Backend**: new `get_owned_or_404` helper (`app/api/crud_utils.py`,
alongside the existing `get_or_404`) — 403 (not 404) on a real ownership
mismatch, but with the same 404-shaped "not found" detail message, so a
client can't use the error text to enumerate real IDs. Applied directly
(`Deck`, `UserCourse`, `KnownVocabularyItem`, `UserExerciseAttempt`,
`UserProgress`, `Conversation`, `ReadingPassage`) and transitively, by
loading the parent first (`Card` via `Deck.user_id`, `ReviewLog` via
`Card.deck_id -> Deck.user_id`). `VocabularyItem`'s nullable `user_id`
needed one extra rule: a `NULL` row (shared curriculum) is never owned by
anyone, so mutate/delete unconditionally 403s there too, via a plain
`item.user_id != user_id` check (`None != anything` is always true in
Python, so this falls out for free rather than needing a special case);
reads stay open to everyone via the same OR-NULL rule the Slice 2 list
endpoint already used. Every previously-unscoped list endpoint
(`GET /decks`, `GET /cards` with no `deck_id`, `GET /review-logs`,
`GET /user-exercise-attempts`, `GET /user-courses`) gained a required
`user_id` filter. Deliberately out of scope, by design: `users.py` (used
by `bootstrap.ts` before any identity exists to check ownership against)
and course-content CRUD (`courses`/`languages`/`skills`/`lesson_exercises`/
`roleplay_scenarios`) — shared/global by Slice 1's own decision, not a
data-isolation gap.

**Tests**: 30 new tests (one 403 case per hardened route, most in a new
`tests/test_ownership_checks.py` covering routes with no natural home in
an existing feature's test file, plus a few added directly into
`test_review_flow.py`/`test_known_vocabulary.py`/`test_conversations.py`/
`test_vocabulary_examples.py`/`test_tts.py` alongside their existing
happy-path coverage); every other integration test touching a now-hardened
route across the suite needed a `user_id` param/field added since it's
now required (a large but entirely mechanical pass). One real, intentional
behavior change surfaced along the way: `POST /cards` (plain create, not
just `quick-add`) now verifies the target deck's ownership too, closing a
gap the original plan hadn't explicitly named but which was the same class
of issue as `quick_add_card`'s existing check.

**Frontend**: `useDecks`/`useCards`/`useDueCards`/`useCreateCard`/
`useUpdateCard`/`useDeleteCard`/`useQuickAddCard`/`useConversationMessages`/
`useSendMessage` all gained a `userId` parameter, threaded from
`useBootstrapContext()` at each of their ~10 call sites (dashboard, deck
detail, review session, `QuickAddButton`, journal/paste-in/reading-passage
pages, roleplay conversation page) — `DeckRow.tsx` and `useDeckStatsList.ts`
needed no new prop at all, since the `Deck` object they already had in
hand carries its own `user_id`. `review-logs`/`user-exercise-attempts`/
`user-courses` needed zero frontend changes (confirmed via grep: no
current caller).

**Live verification**: browser-automation clicks and screenshots were
unreliable this session (a tooling-side issue, not app-related — clicks
via `find`+ref weren't registering, screenshots errored on a malformed
CDP param); verified via direct `curl` against the real dev DB/backend
instead. `POST /cards/{id}/review` returns 200 with a real FSRS
recompute for the actual owner, and 403 with `{"detail": "Deck not
found"}` for a random `user_id` — confirms both the happy path and the
ID-enumeration-safe error shape work against real data, not just the
test suite. Every other page (dashboard, deck detail, known-vocabulary,
roleplay conversation) loads cleanly with correctly-`user_id`-scoped
requests and zero console errors. Full verification: 216/216 backend
tests pass, `ruff` clean; frontend 92/92 tests, `tsc`, `eslint` all clean.

**2026-08-16 — Phase 8 auth Slice 4 (real Google sign-in everywhere,
session-derived identity), complete and verified end-to-end.** Closes
both remaining gaps at once: `BootstrapProvider`
never actually signed anyone in, and every route still trusted whatever
`user_id` the client claimed. Confirmed the login-UX question with the
user first (AskUserQuestion): an **in-place login gate** — one provider
wraps the app in `layout.tsx`, and a signed-out visitor sees the Google
sign-in screen rendered directly in place of `children` on a 401 from
`GET /auth/me`, same URL, no redirect, no Next.js middleware — rather
than a redirect to a separate route. The standalone `/login` page
(Slice 1's proof-of-mechanism) was deleted, its JSX moved into the new
`AuthProvider`.

**Backend**: every route that used to take `user_id` as a query param or
request-body field now takes `current_user: User = Depends(get_current_user)`
instead — genuinely simpler than Slice 3's version, since ownership checks
(`get_owned_or_404`, `vocabulary.py`'s `_check_read_access`/
`_check_write_access`) compare against `current_user.id` with no separate
param to thread through at all. Every `*Create`/`*Submit`/`*Generate`/
`*Start`/`*Promote`/`*Analyze` input schema had its `user_id` field
removed (~20 occurrences); `*Read` output schemas kept `user_id`
unchanged. `GET /user-progress` dropped its optional `user_id` filter
(Slice 3 had already flagged the inconsistency) — always scoped to self
now, no "list everyone's" mode. `users.py`: `GET/PATCH/DELETE /users/{id}`
locked to self-only; `GET /users` (list-all, a real privacy leak — it
returned every user's email) removed entirely now that its only caller
(`bootstrap.ts`) is gone too; `POST /users` stays, unauthenticated but
harmless.

**Backend tests**: reused this project's established swappable-`Depends`
testing convention (`get_llm_provider`/`get_tts_client`/
`get_google_token_verifier` were already overridden per-test the same
way) — a new `login_as` fixture (`conftest.py`) overrides
`get_current_user` to return a specific `User` row, callable again
mid-test to switch identity for cross-user 403 cases. Every
`params={"user_id": ...}`/`json={"user_id": ...}` call site across the
suite was removed as part of the same pass — the single largest
mechanical change in the slice by file count (~14 test files), but
uniform throughout. One real ordering subtlety learned by trial and
error: since each resource-creation helper (`_make_deck`, `_make_course`,
etc.) now logs in as the user it just created, a cross-user test must
finish everything it needs to do as user A *before* creating user B
(otherwise A's setup silently executes as B), and must explicitly
`login_as` back to A afterward if a final assertion needs to run as A.
216/216 backend tests pass, `ruff` clean.

**Frontend**: new `AuthProvider` (`providers/AuthProvider.tsx`) wraps
`layout.tsx` ahead of `BootstrapProvider`; `logout()` clears the entire
TanStack Query cache (not just auth) before refetching `/auth/me`, so a
real user switch can't show the previous user's stale data even for a
moment — safe to do unconditionally since the gate immediately unmounts
the whole app tree on the resulting 401 anyway. `bootstrap.ts` dropped
its user-creation half entirely (`usersApi.list/create`,
`DEFAULT_USER_EMAIL/DISPLAY_NAME`) along with the now-dead
`lib/api/users.ts`; `BootstrapResult` dropped `userId`, keeping
`courseId`/`baseLanguageId`/`targetLanguageId`. All ~24 hooks and their
`lib/api/*.ts` counterparts that gained a `userId` parameter in Slices
2-3 lost it again, along with the `userId` segment `queryKeys.ts` added
in Slice 2 (no longer needed for cache-scoping now that `logout()` clears
the whole cache on a real identity switch). Every page/component call
site that threaded `userId` through stopped passing it — almost entirely
deletions, not additions. `Nav.tsx` gained a "Signed in as {name} · Log
out" affordance via the new `useAuthContext()`, the first real way to
sign in/out from the UI rather than only provable via a standalone test
page. 92/92 frontend tests pass, `tsc --noEmit` and `eslint` both clean.

**Live verification, and a real dev-environment bug found only by doing
it**: both the backend and frontend dev servers turned out to be running
*stale* processes — the backend was an orphaned `uvicorn --reload`
*worker* subprocess (Windows doesn't cascade killing the parent
reloader to its child worker, so the worker kept serving pre-Slice-4
routes off its old in-memory import even after the reloader "parent" was
killed) still listening on port 8000 from hours earlier, and the frontend
dev server predated all of this slice's provider-tree changes to
`layout.tsx`. Neither is a Slice 4 code bug, but both would have silently
invalidated live testing if not caught — confirmed via a direct `curl
/api/decks`, which returned the *old* "user_id required" 422 shape
against code that no longer has a `user_id` param at all. Killed both
worker and reloader PIDs, restarted fresh from `backend/.venv` and `npm
run dev`. With genuinely fresh servers: dashboard, known-vocabulary, and
journal pages all load correctly with session-derived data and zero
console errors; clicking "Log out" clears the session and the in-place
gate renders instantly at the *same URL* (`/journal`, not a redirect) —
confirming the in-place-gate design actually works as designed, not just
in isolation. Signing back in via the real Google account picker wasn't
completable through browser automation (a real third-party OAuth
popup/account-selection flow, appropriately outside what should be
automated) — handed off to the user to confirm the final leg (same
account's data still intact after a real round trip).

**2026-08-16 — Phase 8 performance/cost review, complete; two real
findings fixed, three deliberately deferred.** Went through every LLM/TTS
call site, backend query pattern, frontend fetch pattern, and the
Docker/DB setup.

**Fixed:**
- **No rate limiting existed anywhere** (confirmed via a full-backend
  grep) — any signed-in user could call journal correction, free-text
  grading, reading-comprehension grading, reading-passage generation, or
  roleplay chat as fast as the UI allowed, each a real, uncached Gemini
  call against a tight, whole-app-shared free-tier quota. Added a small
  in-process `RateLimiter` (`app/api/rate_limit.py`, sliding window,
  per-user, no new dependency — in-memory rather than Redis-backed since
  this app runs as a single process) with one named budget per
  LLM-backed feature (5-15 calls/minute depending on how naturally
  chatty the feature is — roleplay messaging gets the most headroom).
  Wired into all five call sites; `lesson_exercises.py`'s attempt
  endpoint only checks it inside the FREE_TEXT branch, since that's the
  only exercise type that actually calls the LLM. 6 new tests
  (`test_rate_limit.py`) — the window-expiry case is tested by passing an
  explicit `now` into `RateLimiter.check` rather than a real
  `time.sleep`, deliberately avoiding the class of wall-clock-relative
  flake already in Known Issues.
- **N+1 in `_unlock_eligible_production_cards`** (`cards.py`, runs on
  every `GET /cards/due`) did 3-4 separate DB round trips *per suspended
  card* in a loop. Rewritten to batch: course/target_language (identical
  for every card in one deck, so only ever needed once, not per-card) is
  loaded before the loop; vocabulary items, recognition cards, and review
  counts are each fetched in one `IN (...)`/`GROUP BY` query regardless
  of how many cards are suspended. Caller updated to pass the
  already-loaded `Deck` instead of a bare `deck_id`, since it already had
  it in hand. No behavior change — same 34 tests covering this path and
  the wider review/gating flow still pass.

**Deliberately deferred (logged as Known Issues, not fixed now):**
`get_or_create_vocabulary_item_and_cards`'s unbounded per-user
`VocabularyItem` scan (real, but only degrades once a personal vocabulary
grows into the hundreds+ — not there yet); `useDeckStatsList`'s one-
request-per-deck pattern (already self-documented with its own fix
noted, a future backend aggregate endpoint); missing composite
`(user_id, course_id)` indexes and untuned DB connection-pool sizing
(both low-urgency at current scale); the backend `Dockerfile` always
running dev-mode `uvicorn --reload` with dev dependencies installed
(real, but squarely a deploy-slice fix, not a performance-review one).

**2026-08-16 — Phase 8 final test pass, complete.** Ran the full existing
suite as a baseline (green), then audited for coverage gaps by comparing
every backend route file against its test file and checking the four
global exception handlers in `main.py` against what actually exercises
them.

Found and filled real gaps: `courses.py`/`skills.py` had no test at all
for their update/delete routes (only implicit coverage of create, via
other files' setup helpers) — added `test_courses.py`/`test_skills.py`
mirroring `test_languages.py`'s existing CRUD-lifecycle pattern.
`users.py`'s self-only `GET/PATCH/DELETE` (`_check_self`, added Slice 4)
had zero coverage despite being real, security-relevant logic — added
`test_users.py`. More notably: two of the four global exception handlers
in `main.py` (`AuthError`→401, `TTSError`→502) had never been exercised
by a test, and neither had the third (`LLMError`→502) anywhere in the
suite — despite the `AuthError` handler's own comment explicitly saying
it exists because a bad Google credential *leaked a 500 live once*
before this handler was added. Added one regression test per handler
(`test_auth.py`, `test_tts.py`, `test_vocabulary_examples.py`), each
confirming the clean error status instead of an uncaught exception.
While writing the `AuthError` regression test, caught and fixed a real
mistake in the test itself before it could land: forgetting to wrap a
`FastAPI` dependency override in a no-arg `lambda:` made FastAPI
introspect the override's own inner-function signature as a request
param, producing a misleading 422 instead of testing anything real.

On the frontend, confirmed this project's existing test/no-test split is
deliberate and consistently applied throughout (pure, hook-free
presentational components get RTL tests; anything wired to a data-
fetching hook is verified live instead, per every prior phase's decision
log) — then found three components that broke that split without a hook
to excuse it: `SkillNode`, `CardListItem`, and `IntroScreen` were all
pure/props-only, same shape as already-tested `MessageBubble`/
`KnownVocabularyRow`, just missing their test file. Added all three.

Finished with a live smoke test against the running dev servers: real
Google-session dashboard load, and a real end-to-end journal submission
(actual Gemini call, actual 201, actual persisted entry with vocabulary
suggestions rendered) — confirming the new Slice-performance-review rate
limiter doesn't interfere with genuine single-submission usage.

Final tallies: backend 242/242 (up from 222 — 20 new tests), `ruff`
clean; frontend 103/103 (up from 92 — 11 new tests), `tsc`/`eslint`
clean.

## Current Status

**As of 2026-08-16:**

- Done: **Phase 8 final test pass, complete** — audited every backend
  route against its test file and every global exception handler against
  what actually exercises it; found and filled real gaps (courses/skills
  CRUD, users.py's self-only checks, and three untested error-mapping
  handlers, one of which was guarding a bug that had already leaked a 500
  live once before). Added matching frontend component tests for three
  presentational components that had fallen through this project's
  otherwise-consistent test/no-test split. Backend 242/242 (+20), `ruff`
  clean; frontend 103/103 (+11), `tsc`/`eslint` clean; live-verified with
  a real end-to-end journal submission. See the decision log entry just
  above for the full breakdown.
- Done: **Phase 8 performance/cost review, complete** — added per-user
  rate limiting (nothing previously stood between a signed-in user and
  unlimited real Gemini calls) and fixed a real N+1 in the due-queue's
  production-gate unlock check; three lower-urgency findings deferred and
  logged as Known Issues. 222/222 backend tests pass, `ruff` clean. See
  the decision log entry just above for the full breakdown.
- Done: **Phase 8 — real multi-user auth, complete end-to-end (Slices
  1-4).** Slice 4 (real Google sign-in everywhere, session-derived
  identity) closes the phase: an in-place login gate replaces
  `BootstrapProvider`'s old silent user-creation, and every route derives
  "who's asking" from the verified session cookie instead of a
  client-supplied `user_id`. 216/216 backend tests, 92/92 frontend tests,
  `ruff`/`tsc`/`eslint` all clean; live-verified (dashboard/known-
  vocabulary/journal load correctly, logout → in-place gate confirmed at
  the same URL with no stale-data flash) — except the final "sign back in
  with a real Google account" leg, left for the user to confirm directly
  rather than automating a real OAuth popup. See the decision log entry
  just above for the full breakdown, including a real dev-environment bug
  (an orphaned `uvicorn --reload` worker serving stale pre-Slice-4 routes)
  found only by doing live verification.
- Done: **Phase 8 — real multi-user auth, Slice 3 (ownership checks on
  personal data), complete and verified end-to-end** — every route that
  reads or mutates a specific user's resource (decks, cards, known-
  vocabulary, personal vocabulary items, reading passages, conversations,
  review logs, exercise attempts/progress, course enrollments) now
  verifies real ownership via a new `get_owned_or_404` helper, closing
  "read/edit/delete anyone's data by guessing an ID." Deliberately still
  trusts a client-supplied `user_id` for now (full session-derived
  identity is Slice 4's job, confirmed with the user before starting this
  slice). 30 new tests, all passing; verified live against the real dev
  DB via direct `curl` after browser-automation clicks/screenshots proved
  unreliable this session (tooling issue, not app-related) — see the
  decision log entry just above for the full breakdown. Slice 4 (full
  frontend integration replacing `BootstrapProvider` with real login) not
  started.
- Done: **Phase 8 — real multi-user auth, Slice 2 (`user_id` on
  `VocabularyItem`/`KnownVocabularyItem`/`ReadingPassage`), complete and
  verified end-to-end** — data-isolation gap closed for personal
  vocabulary, known-words, and reading passages; shared curriculum content
  (`VocabularyItem.user_id IS NULL`) stays visible to everyone. Two real,
  unrelated environment issues found only via live testing (stray duplicate
  backend process serving stale code; a one-off DB-pool timeout), both
  resolved, neither a code bug — see the decision log entry just above for
  the full breakdown.
- Done: **Phase 8 — real multi-user auth, Slice 1 (backend foundation +
  Google Sign-In), complete and verified live** — real Google account
  sign-in confirmed working end-to-end, including the legacy-data-claim
  logic (the dev seed user's row updated in place, zero data loss). Two
  real bugs found only reachable via live testing, both fixed — see the
  decision log entry just above for the full breakdown.
- Done: **Known-vocabulary page now shows the full known set** (mastered
  flashcards + tracked known-vocabulary items, not just the latter) — see
  the decision log entry just above for the full breakdown. Also resolved
  in passing: the native-language vocabulary builder idea needs no new
  engineering, just an ordinary deck in a base=target=English course.
- Done: **Conversational practice partner (Phase 6), complete and verified
  end-to-end** — pre-authored roleplay scenarios, multi-turn chat (a new
  `generate_chat_reply` method on `LLMProvider`, since the existing
  single-shot `generate_structured` wasn't enough), and in-context
  correction bundled into the same reply call. See the decision log entry
  just above for the full breakdown.
- Done: **Mnemonics gap closed — Phase 5 is now fully complete**, all
  planned slices built and checked off. One shared mnemonic per word, folded
  into the existing example-generation endpoint/`VocabularyExample` cache as
  originally decided back on 2026-08-13. Includes a real (unrelated) dev-env
  bug hit live: `uvicorn --reload` reported reloading but kept serving stale
  code until the process tree was fully restarted — see the decision log
  entry just above for the full breakdown.
- Done: **Adaptive weak-point targeting (Phase 5), complete and
  verified end-to-end** — a new `GET /weak-points` endpoint blending FSRS
  card lapses, per-word lesson-exercise accuracy, and per-skill mastery into
  a ranked "Weak points" panel on the dashboard, each item linking into an
  existing review/lesson flow. Includes a real gap found and fixed live: the
  dashboard had no `CourseProvider` in its tree (unlike every other section)
  since its deck list never needed course-scoping before — see the earlier
  2026-08-15 decision log entry for the full breakdown.
- Done: **Coverage-gap analysis vs. a CEFR/HSK-style list (Phase 5), complete
  and verified end-to-end** — a new `/known-vocabulary/full-set` endpoint, a
  `CoveragePanel` on `/known-vocabulary` showing per-band known-word coverage
  with expandable gap-word lists, and a "Review these words" link into the
  existing paste-in flow pre-filled with each band's gaps. Includes a real
  React Strict Mode / React Query dev-only bug found and fixed live (auto-run
  analysis on mount got stuck on "Analyzing…" forever) — see the decision log
  entry just above for the full breakdown.
- Done: **Paste-in content with unknown-word flagging (Phase 5), complete
  and verified end-to-end across Spanish and Chinese** — real Chinese word
  segmentation via `jieba`, an uncapped known-vocabulary lookup, instant
  (no-LLM) highlighting with translations filled in a beat later, and a
  real prompt bug (translations landing in the wrong direction) found live
  and fixed with a regression test. First Phase 5 slice with zero
  schema/migration changes. Same-day follow-up from real usage: translated
  words now resolve to their dictionary form (infinitive/singular) rather
  than the literal conjugated/inflected surface form encountered, and
  `NewVocabularyRow` (shared with reading-passage generation) gained an
  independent "Mark as known" action alongside "Add to deck," reusing the
  known-vocabulary system's existing manual-add endpoint. See the decision
  log entries just above for the full breakdown.
- Done: **Reading passage generation (Phase 5), complete and verified
  end-to-end across Spanish and Chinese** — new `reading_passages`/
  `reading_passage_attempts` tables, known-vocabulary blending (mastered
  Cards + sampled `KnownVocabularyItem`s), free-text LLM-graded
  comprehension questions, a new "Reading" practice category replacing
  "Vocabulary" for Spanish/Dutch and newly added for Chinese (its first
  practice content ever, needing zero pre-authored `Skill` rows) — see the
  decision log entry just above for the full breakdown.
- Done: **Known-vocabulary system (Phase 5), complete and verified
  end-to-end across Spanish, Chinese, and Dutch** — new `known_vocabulary_items`
  table, real frequency-band data (hermitdave/FrequencyWords for
  Spanish/Dutch, HSK 3.0 official levels for Chinese), an adaptive
  binary-search placement check, a known-words page with manual
  add/search/delete, and a one-way "promote" action that reuses the
  quick-add note-resolution logic (extracted into a shared service) plus
  a new single-word LLM translation call — see the decision log entry
  just above for the full breakdown.
- Done: **Journal correction + auto vocab extraction (Phase 5, slice 3),
  complete and verified end-to-end** (itemized LLM corrections, one-click
  vocab suggestions flowing into a real deck via the existing quick-add
  endpoint) — see the decision log entry just above for the full
  breakdown.
- Done: **Free-text grading (Phase 5, slice 2), complete and verified
  end-to-end** (LLM-graded FREE_TEXT exercises, both translation-style
  and open-ended, real feedback text surfaced in the UI) — see the
  decision log entry just above for the full breakdown.
- Done: **TTS audio for vocab cards, complete and verified end-to-end**
  (Google Cloud Text-to-Speech, real Spanish + Chinese voices, cached in
  Postgres) — see the decision log entry just above for the full
  breakdown, including one real threading bug found and fixed once real
  GCP credentials went live.
- Done: **Anki-style vocab decks (real-input notes, dual-direction
  cards, quick-add, Chinese as a third language) complete and verified
  end-to-end**, including seven real bugs found and fixed live across
  the initial build and a follow-up round of user testing (two during
  the build, five more from actually using it afterward), plus a
  second, larger content batch (15 more Spanish notes, 12 more Chinese)
  — see the decision log entries just above for the full breakdown.
- Done: **Phase 5, slice 1 (LLM service layer + example-sentence
  generation) complete and verified end-to-end**, including live against
  the real Gemini API — see the decision log entry above for the
  full breakdown.
- Done: **v1 Dutch course added, complete and verified end-to-end** —
  second language, ahead of its originally-planned Phase 8 slot,
  specifically to test the "language-agnostic by design" claim for real.
  Found and fixed three real Spanish-hardcoded spots (pronoun labels,
  present-perfect auxiliary, participle-formation fallback) along the
  way. See the decision log entry just above for the full breakdown.
- Done: **Grading is accent-insensitive, and conjugation mistakes reveal
  the correct answer while staying editable for a retry** — see the
  decision log entry above that one.
- Done: **Phase 4's course navigation was reworked after using the built
  version, and is complete and verified end-to-end** — decks/course split
  onto separate pages, a general course switcher, skills regrouped into
  data-driven practice categories, progress locking removed, and Verb
  Conjugation rebuilt as a tense-picker → conjugate-all-6-persons drill
  (now covering 15 irregular verbs across every tense they're actually
  irregular in, plus present perfect). See the decision log entry just
  above for the full breakdown, including two real bugs (both infinite-
  render-loop variants of the same "unstable reference" mistake) found
  live rather than by review.
- Done: **Phase 4's original build (generic lesson core, conjugation
  practice, three subjunctive-trigger skills) is complete and verified
  end-to-end** — see the Stage A / Stage B decision log entries above,
  including a real schema gap (`intro_content` missing from `SkillRead`)
  found and fixed while verifying Stage B live.
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
- Done: **Two Phase 3 gaps found and fixed by using the live app.** The
  review session's terminal states ("Session complete," "nothing due") had
  no way back to the deck — fixed with a link to `/decks/[deckId]`. Deck
  editing (rename, description, delete) didn't exist at all — the backend
  endpoints were already there from Phase 1, just never wired to the
  frontend; added via a shared `DeckForm`, exposed inline on the dashboard
  ("Edit" next to "Study," no navigation needed) and on the deck detail
  page. Both re-verified live via browser automation; 12/12 frontend tests
  and `tsc`/`eslint` still clean. See decision log for both.
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
- Blocked: nothing. (The manual "sign back in via the real Google account
  picker" follow-up from the auth-slice-4 verification has since been
  confirmed by the user — data intact — and the commit pushed.)
- Next: Phase 8's auth sub-scope (slices 1-4), performance/cost review,
  and the final test pass are all done; still remaining: deployment
  (Vercel + Railway/Fly.io, per the 2026-08-11 decision) and a final
  README (setup, architecture overview, screenshots/demo). See the
  Phase 8 line in the plan checklist above.
- Open questions: none blocking — deployment target was already decided
  (2026-08-11); nothing else to resolve before starting the remaining
  Phase 8 work.

## Known Issues / Follow-ups

- `get_or_create_vocabulary_item_and_cards` (`note_cards.py`, backs
  quick-add and known-vocabulary promote) loads *every* `VocabularyItem`
  a user has in a course, unfiltered, and matches target/base text in
  Python rather than SQL (accent/case-insensitive matching has no simple
  SQL-pushdown without a Postgres extension). Fine at the tens-of-words
  scale this app is at now; would need a normalized/indexed column (or
  `unaccent`) if a personal vocabulary ever grows into the hundreds+.
  Found during the 2026-08-16 performance review, deliberately deferred.
- `useDeckStatsList` makes one request per deck (`useQueries`) rather
  than a single aggregate call — already self-documented in the hook's
  own comment as fine at portfolio scale, with the real fix (a backend
  `GET /decks/stats`-style endpoint) noted for if deck count ever grows.
  Re-confirmed as still the right call during the 2026-08-16 performance
  review, not fixed.
- No composite `(user_id, course_id)` indexes on the tables filtered by
  both (vocabulary items, known-vocabulary, reading passages) — the
  existing single-column indexes on each are adequate at current scale.
  Also, `database.py` uses SQLAlchemy's default connection-pool sizing
  (5 + 10 overflow), untuned. Both low-urgency; revisit once real hosting
  with a real connection cap is picked (the deploy slice).
- The backend `Dockerfile` always runs `uvicorn --reload` with dev
  dependencies installed (`pip install -e ".[dev]"`) — correct for local
  Docker parity, not what should actually ship. Real fix (multi-stage
  build, a real ASGI server command, prod-only deps) belongs in the
  deploy slice, not before.
- On Windows, killing a `uvicorn --reload` process by its listed PID can
  leave an orphaned worker subprocess still bound to the port and still
  serving old code — the reloader (parent) and the actual server (child
  worker) are separate processes, and `Stop-Process` on the parent alone
  doesn't cascade to the child. Symptom: the backend responds fine, but to
  routes/behavior from before the last edit, even though the file on disk
  is correct. Found live during Phase 8 Slice 4 verification. Fix: check
  `netstat -ano` for the actual PID bound to the port (it may differ from
  whichever PID you tried to kill) and stop that one too before
  restarting.
- `SECRET_KEY`'s dev default (`dev-secret-change-me`, 20 bytes) signs the
  new session JWT (Phase 8 slice 1) and is now genuinely security-relevant,
  not just a placeholder — PyJWT already warns on it
  (`InsecureKeyLengthWarning`, below the 32-byte HS256 minimum). Must be
  replaced with a real random value before deployment (Phase 8's later
  slice); harmless for local dev.
- `alembic revision --autogenerate` keeps proposing to drop a pre-existing
  `ix_cards_due_at` index on `cards` (superseded by the composite
  `ix_cards_deck_id_due_at`, never cleaned up) — surfaced a third time in
  the Phase 8 Slice 2 migration (previously the 2026-08-15 roleplay-chat
  migration and the auth Slice 1 migration), each time manually stripped
  out to keep the migration scoped. Worth an actual cleanup migration at
  some point so this stops recurring.
- `test_due_queue_appends_new_cards_oldest_first_capped_at_new_limit`
  (`test_review_flow.py`) marks a review as "today" via a hardcoded
  `datetime.now(UTC) - timedelta(minutes=30)` — breaks in the ~30 minutes
  after UTC midnight, when that offset lands on the previous calendar day
  and `_count_new_cards_shown_today`'s "today" filter no longer counts it,
  letting one extra NEW card through the cap. Found live on 2026-08-15 at
  00:10 UTC; confirmed via wall-clock, not a real regression. Worth
  rewriting with an explicit fixed timestamp instead of a wall-clock-relative
  one if it recurs.
- `VocabularyExample`/`VocabularyAudio` are still cached per-`VocabularyItem`,
  not per-`(VocabularyItem, user)` — now that Phase 8 Slice 2 gives personal
  vocabulary its own `user_id`, two different users' independent
  `VocabularyItem` rows for the same word (e.g. both quick-adding "perro")
  each generate and cache their own examples/audio, duplicating LLM/TTS
  spend that used to be shared across everyone on a course. Accepted as
  out of scope for Slice 2 (a deliberate call, not an oversight); revisit
  if per-user LLM/TTS cost becomes a real concern.
- Gemini free-tier rate limits are tight (~10-15 req/min depending on model,
  as of 2026-08, shared across the whole app, not per user) — per-user
  rate limiting was added in the 2026-08-16 performance review
  (`app/api/rate_limit.py`) to stop any single user from exhausting it,
  but the underlying app-wide quota itself is still real; revisit if a
  paid Gemini tier or real concurrent multi-user load makes it a
  bottleneck.
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
  doesn't require rewriting the rest of the app). **Design resolved
  2026-08-13 after a clarifying-questions conversation — see that date's
  Decisions Log entry** ("Conjugation/subjunctive feature design
  resolved") for the schema, exercise-type, and v1-scope decisions.

- ~~**Native-language vocabulary builder (requested 2026-08-13)**~~ —
  **resolved 2026-08-15, no engineering needed.** Originally floated as a
  possible new Phase 9+ section; user pointed out it's just an ordinary
  Anki deck in the existing deck system (target_text = an advanced English
  word, base_text = its definition), inside a course where base and target
  language both happen to be English. Nothing in the schema prevents that
  — `Course.base_language_id`/`target_language_id` are two independent FKs
  to `Language` with no constraint forcing them apart.
