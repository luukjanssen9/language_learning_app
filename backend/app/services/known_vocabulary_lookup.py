"""Assembles the "known words" a course's user knows, from two signals --
see PLAN.md's reading-passage decision for why this blends both rather
than reading from a single table. Two composed entry points, for two
different purposes:

- `get_known_words_for_passage`: a prompt-budget-capped sample, for
  injecting into an LLM generation prompt (see reading_passage_generation.py).
- `get_full_known_word_set`: the *complete*, uncapped, normalized set, for
  exact membership testing (see paste_in_tokenizer.py's flagging use case
  -- under-counting known words here would incorrectly flag things the
  user actually knows).

Unlike this project's other services, this one *does* touch the DB (plain
SELECTs, not a mutation) -- there's no meaningful "pure" version of "what
does the user currently know," so it lives here rather than being threaded
through as pre-fetched arguments the way `build_cards_for_note`'s
caller-loads-everything convention works for simpler cases.
"""

import random
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.enums import CardState
from app.models.known_vocabulary import KnownVocabularyItem
from app.models.vocabulary import VocabularyItem
from app.services.text_normalize import normalize_for_comparison


async def _get_mastered_words(db: AsyncSession, course_id: uuid.UUID) -> list[str]:
    """A `Card` that's graduated to `REVIEW` -- ground truth, an existing
    FSRS signal, not a new tuned threshold.
    """
    result = await db.execute(
        select(VocabularyItem.target_text)
        .join(Card, Card.vocabulary_item_id == VocabularyItem.id)
        .where(VocabularyItem.course_id == course_id, Card.state == CardState.REVIEW)
        .distinct()
    )
    return list(result.scalars().all())


async def _get_estimated_words(db: AsyncSession, course_id: uuid.UUID) -> list[str]:
    """`KnownVocabularyItem`, any source (placement-check, manual, or
    promoted) -- the starting-assumption estimate.
    """
    result = await db.execute(
        select(KnownVocabularyItem.target_text).where(KnownVocabularyItem.course_id == course_id)
    )
    return list(result.scalars().all())


async def get_known_words_for_passage(
    db: AsyncSession, course_id: uuid.UUID, sample_cap: int = 300
) -> list[str]:
    """Mastered words are always included in full; estimated words fill
    the rest of the budget via a random sample, both to keep prompt size
    reasonable against a course that can hold thousands of placement-check
    rows, and so regenerating a passage doesn't always draw from the same
    handful of most-common words.
    """
    mastered_words = await _get_mastered_words(db, course_id)

    remaining_budget = max(0, sample_cap - len(mastered_words))
    estimated_words: list[str] = []
    if remaining_budget > 0:
        estimated_pool = await _get_estimated_words(db, course_id)
        estimated_words = random.sample(
            estimated_pool, min(remaining_budget, len(estimated_pool))
        )

    return mastered_words + estimated_words


async def get_full_known_word_set(db: AsyncSession, course_id: uuid.UUID) -> set[str]:
    """The complete known-word set, normalized (accent/case-insensitive)
    for exact membership testing -- no sampling, no cap.
    """
    mastered_words = await _get_mastered_words(db, course_id)
    estimated_words = await _get_estimated_words(db, course_id)
    return {normalize_for_comparison(w) for w in mastered_words + estimated_words}
