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
- [ ] **Phase 5 — Core AI/NLP features**: LLM service layer (provider-agnostic,
  Gemini default), example generation, free-text grading, auto-card-generation,
  mnemonics, adaptive weak-point targeting.
- [ ] **Phase 6 — Conversational practice partner**: chat UI, roleplay
  scenarios constrained to known vocabulary, in-context correction.
- [ ] **Phase 7 — Speech (stretch goal)**: Whisper integration, pronunciation
  comparison/feedback.
- [ ] **Phase 8 — Scalability check, polish & deploy**: ~~add a second
  language's config to prove the architecture generalizes~~ — done early,
  2026-08-14 (v1 Dutch course, see Decisions Log); performance/cost
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

## Current Status

**As of 2026-08-14:**

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
- Blocked: nothing.
- Next: design TTS audio for vocab cards together first (flagged, not
  started — see the decision log entry above; check whether Gemini's
  audio-out capability covers this before reaching for a separate TTS
  API), then continue Phase 5 with the next slice — likely free-text
  grading, per the sub-feature list below — checkpoint with the user
  first per this project's per-slice cadence.
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
  doesn't require rewriting the rest of the app). **Design resolved
  2026-08-13 after a clarifying-questions conversation — see that date's
  Decisions Log entry** ("Conjugation/subjunctive feature design
  resolved") for the schema, exercise-type, and v1-scope decisions.

- **Native-language vocabulary builder (requested 2026-08-13, not yet
  scheduled)** — a separate, lower-priority idea: an Anki-like tool for
  building vocabulary in the user's *native* language (e.g. advanced/"big"
  English words), not L2 acquisition. User suggested this as possibly its
  own distinct section of the site, "maybe at the end." Not yet added as a
  numbered phase — ask the user whether this becomes its own Phase 9+ or
  stays a loose idea when it's actually time to consider it.
