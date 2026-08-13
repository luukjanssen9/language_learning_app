# Language App

A language learning app combining an Anki-style spaced-repetition
flashcard system with a Duolingo-style structured course, grounded in
learning-science research (spaced repetition via FSRS, retrieval practice,
interleaving, comprehensible input).

First language pair: English (base) → Spanish (target). The data model and
business logic are language-agnostic by design so additional target languages
can be added as data/config, not code changes.

Status: Phases 1–3 complete (backend data model + API, FSRS spaced-repetition
engine, frontend foundation — deck/card management and a full review-session
UI). See [PLAN.md](./PLAN.md) for the full build plan, current status, and
decisions log.

## Getting started

Requires Docker (for Postgres + the API) and Node.js 20+ (for the frontend).

```bash
cp .env.example .env               # repo root
docker compose up -d postgres
docker compose up -d --build backend
docker compose exec backend alembic upgrade head

cd frontend
cp .env.example .env.local
npm install
npm run dev                        # http://localhost:3000
```

API docs (interactive): http://localhost:8000/docs

A full architecture overview and screenshots will land here as the project
is built out further (Phase 8).

## License

MIT — see [LICENSE](./LICENSE).
