import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import MessageRole


class RoleplayScenarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    setup_prompt: str
    order_index: int
    created_at: datetime


class ConversationStart(BaseModel):
    """Request body for POST /conversations."""

    user_id: uuid.UUID
    course_id: uuid.UUID
    scenario_id: uuid.UUID


class MessageSubmit(BaseModel):
    """Request body for POST /conversations/{id}/messages."""

    user_id: uuid.UUID
    text: str


class Correction(BaseModel):
    original: str
    corrected: str
    explanation: str


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    scenario_id: uuid.UUID
    created_at: datetime


class ConversationMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    text: str
    corrections: list[Correction] | None
    created_at: datetime


class ConversationStartResponse(BaseModel):
    conversation: ConversationRead
    messages: list[ConversationMessageRead]


class MessageSubmitResponse(BaseModel):
    user_message: ConversationMessageRead
    assistant_message: ConversationMessageRead
