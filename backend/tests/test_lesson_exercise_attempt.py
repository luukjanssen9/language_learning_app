import uuid

from httpx import AsyncClient

from app.main import app
from app.services.free_text_grading import FreeTextGradeResult
from app.services.llm import get_llm_provider

CONJUGATION_GRAMMAR_CONFIG = {
    "conjugation": {
        "regular_endings": {
            "ar": {"present": {"indicative": {"tú": "as"}}},
        },
        "irregular_verbs": {},
    },
}


async def _make_skill(
    client: AsyncClient, *, target_grammar_config: dict | None = None
) -> dict:
    """Builds Language(x2) -> Course -> User -> Skill via HTTP, same
    convention as test_review_flow.py's _make_deck. Returns the skill
    dict with `_user_id` stashed on it (attempts need a user_id).
    """
    suffix = uuid.uuid4().hex[:6]  # Language.code is capped at String(10)
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_es = (
        await client.post(
            "/api/languages",
            json={
                "code": f"es-{suffix}",
                "name": "Spanish",
                "grammar_config": target_grammar_config or {},
            },
        )
    ).json()
    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_es["id"],
                "name": "English to Spanish",
                "slug": f"en-es-attempt-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"attempt-{suffix}@example.com", "display_name": "Attempt Test"},
        )
    ).json()
    skill = (
        await client.post(
            "/api/skills",
            json={"course_id": course["id"], "name": "Test Skill", "slug": f"test-{suffix}"},
        )
    ).json()
    skill["_user_id"] = user["id"]
    return skill


async def _make_exercise(
    client: AsyncClient, skill_id: str, exercise_type: str, prompt: dict
) -> dict:
    resp = await client.post(
        "/api/lesson-exercises",
        json={"skill_id": skill_id, "exercise_type": exercise_type, "prompt": prompt},
    )
    return resp.json()


async def test_multiple_choice_correct_answer_marks_correct(client: AsyncClient):
    skill = await _make_skill(client)
    exercise = await _make_exercise(
        client,
        skill["id"],
        "multiple_choice",
        {"question": "Hello?", "options": ["Hola", "Adiós"], "correct_index": 0},
    )

    resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"selected_index": 0}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["attempt"]["is_correct"] is True
    assert body["progress"]["times_attempted"] == 1
    assert body["progress"]["times_correct"] == 1
    assert body["progress"]["mastery_level"] == 1.0


async def test_multiple_choice_wrong_answer_marks_incorrect(client: AsyncClient):
    skill = await _make_skill(client)
    exercise = await _make_exercise(
        client,
        skill["id"],
        "multiple_choice",
        {"question": "Hello?", "options": ["Hola", "Adiós"], "correct_index": 0},
    )

    resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"selected_index": 1}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["attempt"]["is_correct"] is False
    assert body["progress"]["times_attempted"] == 1
    assert body["progress"]["times_correct"] == 0
    assert body["progress"]["mastery_level"] == 0.0


async def test_translation_grades_case_and_whitespace_insensitively(client: AsyncClient):
    skill = await _make_skill(client)
    exercise = await _make_exercise(
        client,
        skill["id"],
        "translation",
        {"source_text": "hello", "correct_answer": "hola"},
    )

    resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"text": "  HOLA  "}},
    )
    assert resp.status_code == 200
    assert resp.json()["attempt"]["is_correct"] is True


async def test_fill_in_blank_wrong_answer(client: AsyncClient):
    skill = await _make_skill(client)
    exercise = await _make_exercise(
        client,
        skill["id"],
        "fill_in_blank",
        {"sentence": "Yo ___ español.", "correct_answer": "hablo"},
    )

    resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"text": "como"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["attempt"]["is_correct"] is False
    assert body["correct_answer"] == "hablo"


async def test_translation_grades_missing_accent_as_correct(client: AsyncClient):
    # 2026-08-14: typing Spanish accents on a non-Spanish keyboard is real
    # friction -- grading is accent-insensitive now.
    skill = await _make_skill(client)
    exercise = await _make_exercise(
        client,
        skill["id"],
        "translation",
        {"source_text": "goodbye", "correct_answer": "adiós"},
    )

    resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"text": "adios"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["attempt"]["is_correct"] is True
    assert body["correct_answer"] == "adiós"


async def test_conjugation_exercise_computes_answer_from_grammar_config(client: AsyncClient):
    skill = await _make_skill(client, target_grammar_config=CONJUGATION_GRAMMAR_CONFIG)
    exercise = await _make_exercise(
        client,
        skill["id"],
        "conjugation",
        {"infinitive": "hablar", "tense": "present", "mood": "indicative", "pronoun": "tú"},
    )

    correct_resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"answer": "Hablas"}},
    )
    assert correct_resp.status_code == 200
    assert correct_resp.json()["attempt"]["is_correct"] is True

    wrong_resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"answer": "hablo"}},
    )
    assert wrong_resp.status_code == 200
    wrong_body = wrong_resp.json()
    assert wrong_body["attempt"]["is_correct"] is False
    assert wrong_body["correct_answer"] == "hablas"


async def test_second_attempt_on_same_skill_accumulates_progress(client: AsyncClient):
    skill = await _make_skill(client)
    exercise_a = await _make_exercise(
        client,
        skill["id"],
        "multiple_choice",
        {"question": "A?", "options": ["right", "wrong"], "correct_index": 0},
    )
    exercise_b = await _make_exercise(
        client,
        skill["id"],
        "multiple_choice",
        {"question": "B?", "options": ["right", "wrong"], "correct_index": 0},
    )

    await client.post(
        f"/api/lesson-exercises/{exercise_a['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"selected_index": 0}},
    )
    resp = await client.post(
        f"/api/lesson-exercises/{exercise_b['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"selected_index": 1}},
    )

    body = resp.json()
    assert body["progress"]["times_attempted"] == 2
    assert body["progress"]["times_correct"] == 1
    assert body["progress"]["mastery_level"] == 0.5


class FakeLLMProvider:
    """Overrides `get_llm_provider` for FREE_TEXT attempts, same
    dependency-override mechanism `test_tts.py` uses for `get_tts_client`.
    """

    def __init__(self, result: FreeTextGradeResult) -> None:
        self.result = result

    async def generate_structured(self, prompt, response_model, model_tier="fast"):
        return self.result


async def test_free_text_translation_style_correct_answer(client: AsyncClient):
    skill = await _make_skill(client)
    exercise = await _make_exercise(
        client,
        skill["id"],
        "free_text",
        {"source_text": "Thank you very much for your help."},
    )
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        FreeTextGradeResult(is_correct=True, feedback="Nicely done.")
    )

    resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={
            "user_id": skill["_user_id"],
            "submitted_answer": {"text": "Muchas gracias por tu ayuda."},
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["attempt"]["is_correct"] is True
    assert body["attempt"]["llm_feedback"] == "Nicely done."
    assert body["correct_answer"] is None
    assert body["progress"]["times_correct"] == 1


async def test_free_text_open_ended_incorrect_answer(client: AsyncClient):
    skill = await _make_skill(client)
    exercise = await _make_exercise(
        client,
        skill["id"],
        "free_text",
        {"question_text": "¿Cómo te llamas?"},
    )
    app.dependency_overrides[get_llm_provider] = lambda: FakeLLMProvider(
        FreeTextGradeResult(
            is_correct=False, feedback="That doesn't answer the question asked."
        )
    )

    resp = await client.post(
        f"/api/lesson-exercises/{exercise['id']}/attempt",
        json={"user_id": skill["_user_id"], "submitted_answer": {"text": "Hace sol hoy."}},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["attempt"]["is_correct"] is False
    assert body["attempt"]["llm_feedback"] == "That doesn't answer the question asked."
    assert body["progress"]["times_attempted"] == 1
    assert body["progress"]["times_correct"] == 0
