import uuid

from pydantic import BaseModel

from app.schemas.vocabulary import NewVocabularyWord


class PasteInAnalyzeRequest(BaseModel):
    """Request body for POST /paste-in/analyze."""

    course_id: uuid.UUID
    user_id: uuid.UUID
    text: str


class TextSegment(BaseModel):
    text: str
    is_word: bool
    # Only meaningful when is_word is True -- a passthrough (punctuation/
    # whitespace) segment is never "known" or "unknown", it's just not a
    # vocabulary word at all.
    is_known: bool


class PasteInAnalyzeResponse(BaseModel):
    segments: list[TextSegment]
    # Deduped (by the same accent/case-insensitive comparison used to
    # build `segments`' is_known flags), original first-seen casing --
    # the frontend passes this straight to /translate-unknown-words.
    unknown_words: list[str]


class PasteInTranslateRequest(BaseModel):
    """Request body for POST /paste-in/translate-unknown-words."""

    course_id: uuid.UUID
    words: list[str]


class PasteInTranslateResponse(BaseModel):
    translations: list[NewVocabularyWord]
