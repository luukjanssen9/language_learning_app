"""Lightweight in-process per-user rate limiting for the routes that
trigger a real, uncached LLM call -- see PLAN.md's Phase 8 performance/
cost review. Before this, nothing stood between a signed-in user and
unlimited real Gemini calls against its tight free-tier per-minute quota
(shared across the whole app, not per user).

In-memory, not Redis-backed: this app runs as a single process (see
docker-compose.yml), so a distributed limiter would be solving a scaling
problem it doesn't have yet -- revisit if the backend ever runs as more
than one instance.
"""

import time
import uuid
from collections import defaultdict

from fastapi import HTTPException, status


class RateLimiter:
    """Sliding-window limiter: at most `max_calls` calls per
    `window_seconds` per user. One instance per named budget below, so
    different features don't share a cap.
    """

    def __init__(self, max_calls: int, window_seconds: float) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: dict[uuid.UUID, list[float]] = defaultdict(list)

    def check(self, user_id: uuid.UUID, *, now: float | None = None) -> None:
        # `now` is only ever overridden by tests, to exercise the
        # sliding-window-expiry path deterministically instead of a real
        # `time.sleep` -- this project already hit one real wall-clock-
        # relative test flake (see PLAN.md's Known Issues), so this stays
        # injectable from the start.
        now = now if now is not None else time.monotonic()
        window_start = now - self.window_seconds
        calls = self._calls[user_id]
        # Drop expired timestamps -- keeps memory bounded per user
        # without a separate background sweep.
        while calls and calls[0] < window_start:
            calls.pop(0)
        if len(calls) >= self.max_calls:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests -- please wait a moment and try again.",
            )
        calls.append(now)


# One named budget per LLM-backed feature, sized to stay well under
# Gemini's free-tier per-minute quota (shared across the whole app, not
# per user) even under normal interactive use. Roleplay messaging gets
# the most headroom since a real back-and-forth conversation naturally
# sends several messages in quick succession.
journal_correction_limiter = RateLimiter(max_calls=5, window_seconds=60)
reading_passage_generation_limiter = RateLimiter(max_calls=5, window_seconds=60)
reading_passage_attempt_limiter = RateLimiter(max_calls=10, window_seconds=60)
free_text_grading_limiter = RateLimiter(max_calls=10, window_seconds=60)
roleplay_start_limiter = RateLimiter(max_calls=5, window_seconds=60)
roleplay_message_limiter = RateLimiter(max_calls=15, window_seconds=60)
card_generation_limiter = RateLimiter(max_calls=10, window_seconds=60)
