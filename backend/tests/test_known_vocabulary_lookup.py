"""Integration tests for get_known_words_for_passage -- needs real
Card/KnownVocabularyItem rows, so this goes through `db_session` directly
(ORM inserts, no HTTP) rather than pure unit tests.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.course import Course
from app.models.deck import Deck
from app.models.enums import CardDirection, CardState, KnownVocabularySource
from app.models.known_vocabulary import KnownVocabularyItem
from app.models.language import Language
from app.models.user import User
from app.models.vocabulary import VocabularyItem
from app.services.known_vocabulary_lookup import (
    get_full_known_word_set,
    get_known_words_for_passage,
)


async def _make_course(db: AsyncSession) -> Course:
    suffix = uuid.uuid4().hex[:6]
    base = Language(code=f"en-{suffix}", name="English")
    target = Language(code=f"es-{suffix}", name="Spanish")
    db.add_all([base, target])
    await db.flush()
    course = Course(
        base_language_id=base.id,
        target_language_id=target.id,
        name="English to Spanish",
        slug=f"en-es-lookup-{suffix}",
    )
    db.add(course)
    await db.flush()
    return course


async def _make_deck(db: AsyncSession, course: Course) -> Deck:
    user = User(email=f"{uuid.uuid4().hex[:8]}@example.com", display_name="Lookup Test")
    db.add(user)
    await db.flush()
    deck = Deck(user_id=user.id, course_id=course.id, name="Lookup deck")
    db.add(deck)
    await db.flush()
    return deck


async def _make_mastered_card(db: AsyncSession, course: Course, deck: Deck, word: str) -> None:
    item = VocabularyItem(
        course_id=course.id, user_id=deck.user_id, target_text=word, base_text=f"{word}-en"
    )
    db.add(item)
    await db.flush()
    card = Card(
        deck_id=deck.id,
        vocabulary_item_id=item.id,
        direction=CardDirection.TARGET_TO_BASE,
        state=CardState.REVIEW,
    )
    db.add(card)
    await db.flush()


async def test_mastered_words_are_always_included(db_session: AsyncSession):
    course = await _make_course(db_session)
    deck = await _make_deck(db_session, course)
    await _make_mastered_card(db_session, course, deck, "perro")
    await _make_mastered_card(db_session, course, deck, "gato")

    words = await get_known_words_for_passage(db_session, course.id, deck.user_id)

    assert set(words) == {"perro", "gato"}


async def test_new_card_state_is_not_counted_as_mastered(db_session: AsyncSession):
    course = await _make_course(db_session)
    deck = await _make_deck(db_session, course)
    item = VocabularyItem(
        course_id=course.id, user_id=deck.user_id, target_text="nuevo", base_text="new"
    )
    db_session.add(item)
    await db_session.flush()
    card = Card(
        deck_id=deck.id,
        vocabulary_item_id=item.id,
        direction=CardDirection.TARGET_TO_BASE,
        state=CardState.NEW,
    )
    db_session.add(card)
    await db_session.flush()

    words = await get_known_words_for_passage(db_session, course.id, deck.user_id)

    assert words == []


async def test_estimated_words_fill_remaining_budget_up_to_cap(db_session: AsyncSession):
    course = await _make_course(db_session)
    deck = await _make_deck(db_session, course)
    await _make_mastered_card(db_session, course, deck, "perro")
    for i in range(10):
        db_session.add(
            KnownVocabularyItem(
                course_id=course.id,
                user_id=deck.user_id,
                target_text=f"word{i}",
                source=KnownVocabularySource.PLACEMENT_CHECK,
            )
        )
    await db_session.flush()

    words = await get_known_words_for_passage(db_session, course.id, deck.user_id, sample_cap=4)

    assert "perro" in words
    assert len(words) == 4  # 1 mastered + 3 sampled estimated, capped at 4 total


async def test_empty_known_vocabulary_returns_empty_list_without_erroring(db_session: AsyncSession):
    course = await _make_course(db_session)
    deck = await _make_deck(db_session, course)

    words = await get_known_words_for_passage(db_session, course.id, deck.user_id)

    assert words == []


async def test_full_known_word_set_is_uncapped_and_normalized(db_session: AsyncSession):
    course = await _make_course(db_session)
    deck = await _make_deck(db_session, course)
    await _make_mastered_card(db_session, course, deck, "PERRO")  # uppercase, still matches
    for i in range(500):  # well beyond get_known_words_for_passage's default 300 cap
        db_session.add(
            KnownVocabularyItem(
                course_id=course.id,
                user_id=deck.user_id,
                target_text=f"word{i}",
                source=KnownVocabularySource.PLACEMENT_CHECK,
            )
        )
    await db_session.flush()

    words = await get_full_known_word_set(db_session, course.id, deck.user_id)

    assert len(words) == 501  # every row present, nothing sampled away
    assert "perro" in words  # normalized (lowercased) form


async def test_full_known_word_set_unions_mastered_and_estimated(db_session: AsyncSession):
    course = await _make_course(db_session)
    deck = await _make_deck(db_session, course)
    await _make_mastered_card(db_session, course, deck, "perro")
    db_session.add(
        KnownVocabularyItem(
            course_id=course.id,
            user_id=deck.user_id,
            target_text="gato",
            source=KnownVocabularySource.MANUAL,
        )
    )
    await db_session.flush()

    words = await get_full_known_word_set(db_session, course.id, deck.user_id)

    assert words == {"perro", "gato"}


async def test_full_known_word_set_empty_returns_empty_set(db_session: AsyncSession):
    course = await _make_course(db_session)
    deck = await _make_deck(db_session, course)

    words = await get_full_known_word_set(db_session, course.id, deck.user_id)

    assert words == set()


async def test_mastered_and_estimated_words_exclude_other_users_in_same_course(
    db_session: AsyncSession,
):
    course = await _make_course(db_session)
    deck_a = await _make_deck(db_session, course)
    deck_b = await _make_deck(db_session, course)
    await _make_mastered_card(db_session, course, deck_a, "perro")
    await _make_mastered_card(db_session, course, deck_b, "gato")
    db_session.add_all(
        [
            KnownVocabularyItem(
                course_id=course.id,
                user_id=deck_a.user_id,
                target_text="sol",
                source=KnownVocabularySource.MANUAL,
            ),
            KnownVocabularyItem(
                course_id=course.id,
                user_id=deck_b.user_id,
                target_text="luna",
                source=KnownVocabularySource.MANUAL,
            ),
        ]
    )
    await db_session.flush()

    words = await get_full_known_word_set(db_session, course.id, deck_a.user_id)

    assert words == {"perro", "sol"}
