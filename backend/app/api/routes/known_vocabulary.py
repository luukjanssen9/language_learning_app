import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.models.deck import Deck
from app.models.enums import KnownVocabularySource
from app.models.known_vocabulary import KnownVocabularyItem
from app.models.language import Language
from app.models.vocabulary import VocabularyItem
from app.schemas.card import CardQuickAddResponse, CardRead
from app.schemas.known_vocabulary import (
    FullKnownWordSetResponse,
    KnownVocabularyBulkCreate,
    KnownVocabularyBulkCreateResponse,
    KnownVocabularyItemCreate,
    KnownVocabularyItemRead,
    KnownVocabularyPromote,
)
from app.schemas.vocabulary import VocabularyItemRead
from app.services.known_vocabulary_lookup import (
    get_full_known_word_set,
    get_mastered_vocabulary_items,
)
from app.services.llm import LLMProvider, get_llm_provider
from app.services.note_cards import get_or_create_vocabulary_item_and_cards
from app.services.word_translation import translate_word

router = APIRouter(prefix="/known-vocabulary", tags=["known-vocabulary"])


@router.get("", response_model=list[KnownVocabularyItemRead])
async def list_known_vocabulary(
    course_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[KnownVocabularyItem]:
    result = await db.execute(
        select(KnownVocabularyItem)
        .where(KnownVocabularyItem.course_id == course_id)
        .order_by(KnownVocabularyItem.target_text)
    )
    return list(result.scalars().all())


@router.get("/full-set", response_model=FullKnownWordSetResponse)
async def get_known_vocabulary_full_set(
    course_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> FullKnownWordSetResponse:
    """The complete, normalized known-word set (mastered `Card`s + all
    `KnownVocabularyItem` rows, no sampling) -- see PLAN.md's
    "coverage-gap analysis" decision for why this needs the full set
    rather than `get_known_words_for_passage`'s prompt-budget-capped
    sample. Sorted for a deterministic response.
    """
    words = await get_full_known_word_set(db, course_id)
    return FullKnownWordSetResponse(words=sorted(words))


@router.get("/mastered", response_model=list[VocabularyItemRead])
async def list_mastered_vocabulary(
    course_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[VocabularyItem]:
    """Full details (target_text, base_text, part_of_speech) for every word
    mastered via FSRS review -- the "known but never touched the
    known-vocabulary system" half of what the known-vocabulary page shows
    as known, complementing this router's `KnownVocabularyItem`-backed
    endpoints above. See PLAN.md's 2026-08-15 decision.
    """
    items = await get_mastered_vocabulary_items(db, course_id)
    return sorted(items, key=lambda item: item.target_text)


@router.post("", response_model=KnownVocabularyItemRead, status_code=status.HTTP_201_CREATED)
async def add_known_vocabulary(
    payload: KnownVocabularyItemCreate, db: AsyncSession = Depends(get_db)
) -> KnownVocabularyItem:
    item = KnownVocabularyItem(
        course_id=payload.course_id,
        target_text=payload.target_text.strip().lower(),
        source=KnownVocabularySource.MANUAL,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/bulk", response_model=KnownVocabularyBulkCreateResponse)
async def bulk_add_known_vocabulary(
    payload: KnownVocabularyBulkCreate, db: AsyncSession = Depends(get_db)
) -> KnownVocabularyBulkCreateResponse:
    """Saves the placement check's estimated known band(s) in one call.
    `ON CONFLICT DO NOTHING` on `(course_id, target_text)` rather than a
    Python dedup scan -- unlike quick-add's low-volume, free-typed input,
    this can insert hundreds of rows from a fixed dataset at once, and
    retaking the check must stay harmless (no duplicates) on a re-save.
    """
    words = {w.strip().lower() for w in payload.target_texts if w.strip()}
    if not words:
        return KnownVocabularyBulkCreateResponse(inserted_count=0)

    stmt = (
        pg_insert(KnownVocabularyItem)
        .values(
            [
                {
                    "course_id": payload.course_id,
                    "target_text": word,
                    "source": KnownVocabularySource.PLACEMENT_CHECK.value,
                }
                for word in words
            ]
        )
        .on_conflict_do_nothing(index_elements=["course_id", "target_text"])
        .returning(KnownVocabularyItem.id)
    )
    result = await db.execute(stmt)
    inserted_count = len(result.fetchall())
    await db.commit()
    return KnownVocabularyBulkCreateResponse(inserted_count=inserted_count)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_known_vocabulary(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    item = await get_or_404(db, KnownVocabularyItem, item_id)
    await db.delete(item)
    await db.commit()


@router.post("/{item_id}/promote", response_model=CardQuickAddResponse)
async def promote_known_vocabulary(
    item_id: uuid.UUID,
    payload: KnownVocabularyPromote,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> CardQuickAddResponse:
    """The one-way bridge from a passive known-vocabulary row to a real,
    translated `VocabularyItem` + `Card` -- see PLAN.md's 2026-08-14
    "known-vocabulary system" decision. Translates the word (an LLM call,
    since known-vocabulary rows never store a translation), then reuses
    the same resolve-or-create logic `POST /cards/quick-add` uses, so
    promoting a word that already exists as a `VocabularyItem` in this
    course reuses it rather than duplicating.
    """
    item = await get_or_404(db, KnownVocabularyItem, item_id)
    deck = await get_or_404(db, Deck, payload.deck_id)
    course = await get_or_404(db, Course, deck.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    translation = await translate_word(
        llm, target_language.name, base_language.name, item.target_text
    )

    vocabulary_item, cards = await get_or_create_vocabulary_item_and_cards(
        db,
        deck,
        target_language,
        target_text=item.target_text,
        base_text=translation.base_text,
        part_of_speech=translation.part_of_speech,
        source="Known vocabulary",
    )
    item.source = KnownVocabularySource.PROMOTED

    await db.commit()
    await db.refresh(vocabulary_item)
    for card in cards:
        await db.refresh(card, attribute_names=["vocabulary_item"])

    return CardQuickAddResponse(
        vocabulary_item=VocabularyItemRead.model_validate(vocabulary_item),
        cards=[CardRead.model_validate(card) for card in cards],
    )
