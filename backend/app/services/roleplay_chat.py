"""Generates roleplay chat turns via an `LLMProvider`. Pure function, no DB
access -- same convention as `reading_passage_generation.py`; the caller
(route) is responsible for loading `known_words`/history and persisting the
result as `ConversationMessage` rows.

Split into two functions rather than one, because starting a conversation
and continuing one need genuinely different prompt framing: starting has no
prior turns and nothing yet to correct, so it's a single-shot
`generate_structured` call; continuing needs the model's real conversational
memory, so it goes through `generate_chat_reply`'s multi-turn path instead.
"""

from pydantic import BaseModel

from app.services.journal_correction import Correction
from app.services.llm.base import ChatTurn, LLMProvider


class ChatReplyResult(BaseModel):
    reply_text: str
    corrections: list[Correction]


def _known_vocab_clause(target_language_name: str, known_words: list[str]) -> str:
    if known_words:
        return (
            f"The learner already knows these {target_language_name} words: "
            f"{', '.join(known_words)}. Favor words from this list where natural."
        )
    return (
        f"The learner is a complete beginner in {target_language_name} -- use "
        "only very basic, common vocabulary."
    )


async def start_conversation(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    scenario_setup_prompt: str,
    known_words: list[str],
) -> ChatReplyResult:
    vocab_clause = _known_vocab_clause(target_language_name, known_words)
    prompt = (
        f"You are roleplaying with a {base_language_name}-speaking learner of "
        f"{target_language_name}. {scenario_setup_prompt}\n\n"
        f"{vocab_clause}\n\n"
        f"Start the roleplay now with a short opening line in {target_language_name}, "
        "staying fully in character. Return `reply_text` (the opening line) and an "
        "empty `corrections` list -- there's nothing to correct yet."
    )
    return await llm.generate_structured(prompt, ChatReplyResult, model_tier="reasoning")


async def continue_conversation(
    llm: LLMProvider,
    target_language_name: str,
    base_language_name: str,
    scenario_setup_prompt: str,
    known_words: list[str],
    history: list[ChatTurn],
) -> ChatReplyResult:
    vocab_clause = _known_vocab_clause(target_language_name, known_words)
    system_prompt = (
        f"You are roleplaying with a {base_language_name}-speaking learner of "
        f"{target_language_name}. {scenario_setup_prompt}\n\n"
        f"{vocab_clause}\n\n"
        f"Stay fully in character and reply naturally in {target_language_name}. "
        "Also review the learner's most recent message for real language mistakes "
        "-- grammar, vocabulary, conjugation (not stylistic nitpicks or equally-"
        "valid alternate phrasings). Return:\n"
        "- reply_text: your in-character reply.\n"
        "- corrections: the specific real errors in the learner's last message, "
        "each as {original, corrected, explanation} -- empty list if there were "
        "none."
    )
    return await llm.generate_chat_reply(
        system_prompt, history, ChatReplyResult, model_tier="reasoning"
    )
