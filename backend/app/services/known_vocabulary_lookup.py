"""Assembles the "known words" list fed into reading-passage generation --
see PLAN.md's reading-passage decision for why this blends two signals
rather than reading from a single table.

Unlike this project's other services, this one *does* touch the DB (a
plain SELECT/join, not a mutation) -- there's no meaningful "pure" version
of "what does the user currently know," so it lives here rather than being
threaded through as pre-fetched arguments the way `build_cards_for_note`'s
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


async def get_known_words_for_passage(
    db: AsyncSession, course_id: uuid.UUID, sample_cap: int = 300
) -> list[str]:
    """Mastered words (a `Card` that's graduated to `REVIEW`) are ground
    truth and always included in full -- an existing FSRS signal, not a new
    tuned threshold. Estimated words (`KnownVocabularyItem`, any source --
    placement-check, manual, or promoted) fill the rest of the budget via a
    random sample, both to keep prompt size reasonable against a course
    that can hold thousands of placement-check rows, and so regenerating a
    passage doesn't always draw from the same handful of most-common words.
    """
    mastered_result = await db.execute(
        select(VocabularyItem.target_text)
        .join(Card, Card.vocabulary_item_id == VocabularyItem.id)
        .where(VocabularyItem.course_id == course_id, Card.state == CardState.REVIEW)
        .distinct()
    )
    mastered_words = list(mastered_result.scalars().all())

    remaining_budget = max(0, sample_cap - len(mastered_words))
    estimated_words: list[str] = []
    if remaining_budget > 0:
        estimated_result = await db.execute(
            select(KnownVocabularyItem.target_text).where(
                KnownVocabularyItem.course_id == course_id
            )
        )
        estimated_pool = list(estimated_result.scalars().all())
        estimated_words = random.sample(
            estimated_pool, min(remaining_budget, len(estimated_pool))
        )

    return mastered_words + estimated_words
