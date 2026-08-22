"""One-off maintenance script: fills in `VocabularyItem.attributes.
transliteration` (and `.example_sentence_transliteration`, when the note
has an `example_sentence`) for every existing note in a course whose
target language needs one (`grammar_config.vocab_deck.needs_transliteration`)
but doesn't have one yet -- notes created before card_generation.py grew
transliteration support, or added via the plain manual quick-add form
(whose "Transliteration" field is optional and easy to skip).

Run via: docker compose exec backend python -m app.backfill_transliteration
(or, on Railway, the same command in the backend service's Shell -- see
README's "Railway Shell" step for `alembic upgrade head`, same idea).

Uses the ORM directly against `AsyncSessionLocal` and the real
`get_llm_provider()`, same convention as `app/seed.py` -- a one-off
management script, not app logic serving a request. Safe to re-run: only
ever fills in a currently-missing `attributes` key, never overwrites one
that's already there.
"""

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.language import Language
from app.models.vocabulary import VocabularyItem
from app.services.card_generation import generate_transliteration
from app.services.llm import get_llm_provider


def _needs_backfill(attributes: dict, example_sentence: str | None) -> bool:
    """True if this note is missing a transliteration it should have --
    either the word's own, or (when it has an example sentence) that
    sentence's. Split out and unit-tested on its own: the seeded Chinese
    seed batch (2026-08-14) added a word-level `transliteration` for every
    note but no `example_sentence_transliteration`, and an earlier version
    of this script's `if attributes.get("transliteration"): continue` skip
    missed that whole batch by only checking the word half.
    """
    if not attributes.get("transliteration"):
        return True
    return bool(example_sentence) and not attributes.get("example_sentence_transliteration")


async def backfill_transliteration() -> None:
    llm = get_llm_provider()
    async with AsyncSessionLocal() as session:
        languages = list((await session.execute(select(Language))).scalars())
        languages_needing_transliteration = {
            language.id: language.grammar_config["vocab_deck"].get(
                "transliteration_label", "transliteration"
            )
            for language in languages
            if language.grammar_config.get("vocab_deck", {}).get("needs_transliteration")
        }
        if not languages_needing_transliteration:
            print(
                "No language is configured with vocab_deck.needs_transliteration -- "
                "nothing to do."
            )
            return

        courses = list((await session.execute(select(Course))).scalars())
        course_id_to_label = {
            course.id: languages_needing_transliteration[course.target_language_id]
            for course in courses
            if course.target_language_id in languages_needing_transliteration
        }
        if not course_id_to_label:
            print("No course targets a transliteration-needing language -- nothing to do.")
            return

        items = list(
            (
                await session.execute(
                    select(VocabularyItem).where(
                        VocabularyItem.course_id.in_(course_id_to_label.keys())
                    )
                )
            ).scalars()
        )
        language_by_id = {language.id: language for language in languages}
        course_by_id = {course.id: course for course in courses}

        updated_count = 0
        for item in items:
            if not _needs_backfill(item.attributes, item.example_sentence):
                continue

            transliteration_label = course_id_to_label[item.course_id]
            target_language = language_by_id[course_by_id[item.course_id].target_language_id]
            result = await generate_transliteration(
                llm,
                target_language.name,
                transliteration_label,
                item.target_text,
                item.example_sentence,
            )

            # Only fill gaps, never overwrite a value that's already there
            # (per this script's own docstring) -- generate_transliteration
            # always returns a fresh `transliteration` even when this note
            # only needed its example_sentence_transliteration filled in.
            new_attributes = dict(item.attributes)
            if not new_attributes.get("transliteration"):
                new_attributes["transliteration"] = result.transliteration
            if item.example_sentence and not new_attributes.get("example_sentence_transliteration"):
                new_attributes["example_sentence_transliteration"] = (
                    result.example_sentence_transliteration
                )
            item.attributes = new_attributes
            updated_count += 1
            print(f"Backfilled {item.target_text!r} (id={item.id})")

        await session.commit()
        print(f"Done -- backfilled {updated_count} of {len(items)} note(s).")


if __name__ == "__main__":
    asyncio.run(backfill_transliteration())
