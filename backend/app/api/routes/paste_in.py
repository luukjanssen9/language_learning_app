from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.models.language import Language
from app.models.user import User
from app.schemas.paste_in import (
    PasteInAnalyzeRequest,
    PasteInAnalyzeResponse,
    PasteInTranslateRequest,
    PasteInTranslateResponse,
    TextSegment,
)
from app.schemas.vocabulary import NewVocabularyWord
from app.services.known_vocabulary_lookup import get_full_known_word_set
from app.services.llm import LLMProvider, get_llm_provider
from app.services.paste_in_tokenizer import tokenize
from app.services.text_normalize import normalize_for_comparison
from app.services.word_translation import translate_words

router = APIRouter(prefix="/paste-in", tags=["paste-in"])


@router.post("/analyze", response_model=PasteInAnalyzeResponse)
async def analyze_pasted_text(
    payload: PasteInAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PasteInAnalyzeResponse:
    """No LLM call -- pure tokenization + a set-membership check, so the
    frontend can render highlighted text instantly. See
    `POST /paste-in/translate-unknown-words` for the (separate, slower)
    translation step.
    """
    course = await get_or_404(db, Course, payload.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)

    known_words = await get_full_known_word_set(db, course.id, current_user.id)
    raw_segments = tokenize(payload.text, target_language.grammar_config)

    segments: list[TextSegment] = []
    unknown_words: list[str] = []
    seen_unknown = set()
    for text, is_word in raw_segments:
        normalized = normalize_for_comparison(text)
        is_known = is_word and normalized in known_words
        segments.append(TextSegment(text=text, is_word=is_word, is_known=is_known))
        if is_word and not is_known and normalized not in seen_unknown:
            seen_unknown.add(normalized)
            unknown_words.append(text)

    return PasteInAnalyzeResponse(segments=segments, unknown_words=unknown_words)


@router.post("/translate-unknown-words", response_model=PasteInTranslateResponse)
async def translate_unknown_words(
    payload: PasteInTranslateRequest,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> PasteInTranslateResponse:
    course = await get_or_404(db, Course, payload.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    if not payload.words:
        return PasteInTranslateResponse(translations=[])

    results = await translate_words(
        llm, target_language.name, base_language.name, payload.words
    )

    # translate_words returns each word's dictionary form (e.g. every
    # conjugation of a verb resolves to its infinitive), so distinct input
    # words can legitimately collapse to the same output -- "hablo" and
    # "hablas" both become "hablar". Dedupe here rather than showing the
    # same glossary row twice; add-to-deck's own quick-add idempotency
    # would no-op a second click anyway, but there's no reason to render
    # the duplicate row in the first place.
    seen: set[str] = set()
    translations: list[NewVocabularyWord] = []
    for r in results:
        normalized = normalize_for_comparison(r.target_text)
        if normalized in seen:
            continue
        seen.add(normalized)
        translations.append(NewVocabularyWord(target_text=r.target_text, base_text=r.base_text))

    return PasteInTranslateResponse(translations=translations)
