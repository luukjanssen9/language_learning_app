import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.crud_utils import get_or_404
from app.database import get_db
from app.models.course import Course
from app.models.enums import MessageRole
from app.models.language import Language
from app.models.roleplay import Conversation, ConversationMessage, RoleplayScenario
from app.schemas.roleplay import (
    ConversationMessageRead,
    ConversationRead,
    ConversationStart,
    ConversationStartResponse,
    MessageSubmit,
    MessageSubmitResponse,
)
from app.services.known_vocabulary_lookup import get_known_words_for_passage
from app.services.llm import LLMProvider, get_llm_provider
from app.services.llm.base import ChatTurn
from app.services.roleplay_chat import continue_conversation, start_conversation

router = APIRouter(prefix="/conversations", tags=["roleplay"])


@router.post("", response_model=ConversationStartResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationStart,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> ConversationStartResponse:
    """Creates the conversation and generates its opening line -- no user
    message exists yet, so this goes through `start_conversation`'s
    single-shot path, not `continue_conversation`'s multi-turn one.
    """
    scenario = await get_or_404(db, RoleplayScenario, payload.scenario_id)
    course = await get_or_404(db, Course, payload.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    known_words = await get_known_words_for_passage(db, course.id)
    result = await start_conversation(
        llm, target_language.name, base_language.name, scenario.setup_prompt, known_words
    )

    conversation = Conversation(
        user_id=payload.user_id, course_id=payload.course_id, scenario_id=payload.scenario_id
    )
    db.add(conversation)
    await db.flush()

    opening = ConversationMessage(
        conversation_id=conversation.id, role=MessageRole.ASSISTANT, text=result.reply_text
    )
    db.add(opening)
    await db.commit()
    await db.refresh(conversation)
    await db.refresh(opening)

    return ConversationStartResponse(
        conversation=ConversationRead.model_validate(conversation),
        messages=[ConversationMessageRead.model_validate(opening)],
    )


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    user_id: uuid.UUID, course_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[Conversation]:
    query = (
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.course_id == course_id)
        .order_by(Conversation.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessageRead])
async def list_conversation_messages(
    conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[ConversationMessage]:
    await get_or_404(db, Conversation, conversation_id)
    query = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{conversation_id}/messages", response_model=MessageSubmitResponse)
async def send_message(
    conversation_id: uuid.UUID,
    payload: MessageSubmit,
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> MessageSubmitResponse:
    """Persists the user's turn, replies via `continue_conversation`'s
    multi-turn path (full prior history + this turn), and grades the
    user's turn in the same call -- the reply and its correction of what
    was just said are the same LLM response, not two round trips.
    """
    conversation = await get_or_404(db, Conversation, conversation_id)
    scenario = await get_or_404(db, RoleplayScenario, conversation.scenario_id)
    course = await get_or_404(db, Course, conversation.course_id)
    target_language = await get_or_404(db, Language, course.target_language_id)
    base_language = await get_or_404(db, Language, course.base_language_id)

    existing_result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at)
    )
    existing_messages = list(existing_result.scalars().all())

    user_message = ConversationMessage(
        conversation_id=conversation_id, role=MessageRole.USER, text=payload.text
    )
    db.add(user_message)
    await db.flush()

    history = [
        ChatTurn(role="assistant" if m.role == MessageRole.ASSISTANT else "user", text=m.text)
        for m in existing_messages
    ]
    history.append(ChatTurn(role="user", text=payload.text))

    known_words = await get_known_words_for_passage(db, course.id)
    result = await continue_conversation(
        llm,
        target_language.name,
        base_language.name,
        scenario.setup_prompt,
        known_words,
        history,
    )

    user_message.corrections = [c.model_dump() for c in result.corrections]

    assistant_message = ConversationMessage(
        conversation_id=conversation_id, role=MessageRole.ASSISTANT, text=result.reply_text
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)

    return MessageSubmitResponse(
        user_message=ConversationMessageRead.model_validate(user_message),
        assistant_message=ConversationMessageRead.model_validate(assistant_message),
    )
