import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from google.cloud import texttospeech
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.models.language import Language
from app.models.vocabulary import VocabularyItem
from app.models.vocabulary_audio import VocabularyAudio
from app.models.vocabulary_example import VocabularyExample
from app.schemas.vocabulary import (
    VocabularyExampleRead,
    VocabularyItemCreate,
    VocabularyItemRead,
    VocabularyItemUpdate,
)
from app.services.llm import LLMProvider, get_llm_provider
from app.services.sentence_generation import generate_example_sentences
from app.services.tts import get_tts_client, synthesize_speech

router = APIRouter(prefix="/vocabulary-items", tags=["vocabulary"])


@router.post("", response_model=VocabularyItemRead, status_code=status.HTTP_201_CREATED)
async def create_vocabulary_item(
    payload: VocabularyItemCreate, db: AsyncSession = Depends(get_db)
) -> VocabularyItem:
    item = VocabularyItem(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("", response_model=list[VocabularyItemRead])
async def list_vocabulary_items(
    user_id: uuid.UUID,
    course_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[VocabularyItem]:
    # user_id OR NULL: shared curriculum content (NULL) stays visible
    # alongside this user's own personal words -- see
    # VocabularyItem.user_id's docstring.
    query = (
        select(VocabularyItem)
        .where((VocabularyItem.user_id == user_id) | (VocabularyItem.user_id.is_(None)))
        .order_by(VocabularyItem.target_text)
    )
    if course_id is not None:
        query = query.where(VocabularyItem.course_id == course_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{item_id}", response_model=VocabularyItemRead)
async def get_vocabulary_item(
    item_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> VocabularyItem:
    return await get_or_404(db, VocabularyItem, item_id)


@router.patch("/{item_id}", response_model=VocabularyItemRead)
async def update_vocabulary_item(
    item_id: uuid.UUID, payload: VocabularyItemUpdate, db: AsyncSession = Depends(get_db)
) -> VocabularyItem:
    item = await get_or_404(db, VocabularyItem, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vocabulary_item(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    item = await get_or_404(db, VocabularyItem, item_id)
    await db.delete(item)
    await db.commit()


@router.get("/{item_id}/examples", response_model=list[VocabularyExampleRead])
async def get_vocabulary_item_examples(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> list[VocabularyExample]:
    """Get-or-generate: returns cached examples if any exist for this word,
    otherwise generates them via the LLM layer and persists the result --
    so a given vocabulary item only ever costs one real LLM call across
    its whole lifetime, not one per page view (see `VocabularyExample`'s
    docstring for why that matters on Gemini's free tier).
    """
    item = await get_or_404(db, VocabularyItem, item_id)

    result = await db.execute(
        select(VocabularyExample).where(VocabularyExample.vocabulary_item_id == item_id)
    )
    existing = list(result.scalars().all())
    if existing:
        return existing

    course = await get_or_404(db, Course, item.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    generated = await generate_example_sentences(
        llm,
        target_language_name=target_language.name,
        base_language_name=base_language.name,
        target_text=item.target_text,
        part_of_speech=item.part_of_speech,
    )
    examples = [
        VocabularyExample(
            vocabulary_item_id=item.id,
            target_text=example.target_text,
            base_text=example.base_text,
            mnemonic=generated.mnemonic,
        )
        for example in generated.examples
    ]
    db.add_all(examples)
    await db.commit()
    for example in examples:
        await db.refresh(example)
    return examples


@router.get("/{item_id}/audio")
async def get_vocabulary_item_audio(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tts_client: texttospeech.TextToSpeechAsyncClient = Depends(get_tts_client),
) -> Response:
    """Get-or-generate, same shape as the /examples endpoint above: returns
    a cached pronunciation clip if one exists, otherwise synthesizes it via
    Google Cloud TTS and persists the result -- one real TTS call per word
    across its whole lifetime, not one per playback. Raw audio bytes, not
    JSON -- the first binary response in this app. `Cache-Control` is set
    aggressively since the audio never changes once generated, so repeat
    plays don't even reach this endpoint after the first.
    """
    item = await get_or_404(db, VocabularyItem, item_id)

    result = await db.execute(
        select(VocabularyAudio).where(VocabularyAudio.vocabulary_item_id == item_id)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return Response(
            content=existing.audio_data,
            media_type=existing.content_type,
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )

    course = await get_or_404(db, Course, item.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    tts_config = target_language.grammar_config.get("tts")
    if tts_config is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"TTS is not configured for {target_language.name}",
        )

    audio_data = await synthesize_speech(
        tts_client,
        text=item.target_text,
        language_code=tts_config["language_code"],
        voice_name=tts_config["voice_name"],
    )
    audio = VocabularyAudio(
        vocabulary_item_id=item.id, audio_data=audio_data, content_type="audio/mpeg"
    )
    db.add(audio)
    await db.commit()

    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
