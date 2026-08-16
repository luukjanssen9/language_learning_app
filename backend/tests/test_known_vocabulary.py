"""Integration tests for the known-vocabulary endpoints, through the live
API + DB (`client`/`db_session` fixtures from conftest.py). The real
Gemini provider is swapped out for `promote_known_vocabulary`'s translation
call via the same dependency-override mechanism `get_db` uses.
"""

import uuid

from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.card import Card
from app.models.enums import CardDirection, CardState
from app.services.llm import get_llm_provider
from app.services.llm.base import ModelTier
from app.services.word_translation import WordTranslation


class FakeLLMProvider:
    def __init__(self, canned_response: BaseModel) -> None:
        self.canned_response = canned_response
        self.call_count = 0

    async def generate_structured(
        self, prompt: str, response_model: type, model_tier: ModelTier = "fast"
    ) -> BaseModel:
        self.call_count += 1
        return self.canned_response


async def _make_deck(client: AsyncClient, login_as) -> dict:
    suffix = uuid.uuid4().hex[:6]  # Language.code is capped at String(10)
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_es = (
        await client.post("/api/languages", json={"code": f"es-{suffix}", "name": "Spanish"})
    ).json()
    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_es["id"],
                "name": "English to Spanish",
                "slug": f"en-es-knownvocab-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"knownvocab-{suffix}@example.com", "display_name": "Known Vocab Test"},
        )
    ).json()
    await login_as(user["id"])
    deck = (
        await client.post(
            "/api/decks", json={"course_id": course["id"], "name": "Known vocab deck"}
        )
    ).json()
    return deck


async def _make_deck_in_course(client: AsyncClient, login_as, course_id: str) -> dict:
    """A second user + deck in an already-existing course -- for testing
    that two users sharing a course don't see each other's known-vocabulary/
    mastered data, distinct from `_make_deck`'s always-fresh-course setup.
    Logs in as the new (second) user before returning.
    """
    suffix = uuid.uuid4().hex[:6]
    user = (
        await client.post(
            "/api/users",
            json={"email": f"knownvocab-{suffix}@example.com", "display_name": "Second User"},
        )
    ).json()
    await login_as(user["id"])
    deck = (
        await client.post(
            "/api/decks", json={"course_id": course_id, "name": "Second user's deck"}
        )
    ).json()
    return deck


async def test_manual_add_forces_placement_check_source_to_manual(
    client: AsyncClient, login_as
):
    deck = await _make_deck(client, login_as)

    resp = await client.post(
        "/api/known-vocabulary",
        json={"course_id": deck["course_id"], "target_text": "Hola"},
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["target_text"] == "hola"  # stored lowercased
    assert body["source"] == "manual"


async def test_list_known_vocabulary_filters_by_course(client: AsyncClient, login_as):
    deck_a = await _make_deck(client, login_as)
    await client.post(
        "/api/known-vocabulary",
        json={"course_id": deck_a["course_id"], "target_text": "casa"},
    )
    deck_b = await _make_deck(client, login_as)
    await client.post(
        "/api/known-vocabulary",
        json={"course_id": deck_b["course_id"], "target_text": "perro"},
    )

    await login_as(deck_a["user_id"])
    resp = await client.get(
        "/api/known-vocabulary", params={"course_id": deck_a["course_id"]}
    )

    assert resp.status_code == 200
    words = [item["target_text"] for item in resp.json()]
    assert words == ["casa"]


async def test_bulk_add_dedupes_via_on_conflict(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)

    first = await client.post(
        "/api/known-vocabulary/bulk",
        json={"course_id": deck["course_id"], "target_texts": ["uno", "dos", "dos"]},
    )
    assert first.status_code == 200
    assert first.json()["inserted_count"] == 2  # "dos" deduped within the same call too

    second = await client.post(
        "/api/known-vocabulary/bulk",
        json={"course_id": deck["course_id"], "target_texts": ["dos", "tres"]},
    )
    assert second.json()["inserted_count"] == 1  # only "tres" is new

    list_resp = await client.get(
        "/api/known-vocabulary", params={"course_id": deck["course_id"]}
    )
    words = {item["target_text"] for item in list_resp.json()}
    assert words == {"uno", "dos", "tres"}


async def test_delete_known_vocabulary(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    item = (
        await client.post(
            "/api/known-vocabulary",
            json={"course_id": deck["course_id"], "target_text": "gato"},
        )
    ).json()

    resp = await client.delete(f"/api/known-vocabulary/{item['id']}")
    assert resp.status_code == 204

    list_resp = await client.get(
        "/api/known-vocabulary", params={"course_id": deck["course_id"]}
    )
    assert list_resp.json() == []


async def test_promote_creates_real_vocabulary_item_and_flips_source(
    client: AsyncClient, login_as
):
    deck = await _make_deck(client, login_as)
    item = (
        await client.post(
            "/api/known-vocabulary",
            json={"course_id": deck["course_id"], "target_text": "perro"},
        )
    ).json()

    fake = FakeLLMProvider(WordTranslation(base_text="dog", part_of_speech="noun"))
    app.dependency_overrides[get_llm_provider] = lambda: fake

    resp = await client.post(
        f"/api/known-vocabulary/{item['id']}/promote", json={"deck_id": deck["id"]}
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["vocabulary_item"]["target_text"] == "perro"
    assert body["vocabulary_item"]["base_text"] == "dog"
    assert body["vocabulary_item"]["source"] == "Known vocabulary"
    assert len(body["cards"]) == 1
    assert fake.call_count == 1

    list_resp = await client.get(
        "/api/known-vocabulary", params={"course_id": deck["course_id"]}
    )
    promoted = next(i for i in list_resp.json() if i["id"] == item["id"])
    assert promoted["source"] == "promoted"


async def test_promoting_a_word_that_already_exists_as_vocabulary_item_reuses_it(
    client: AsyncClient, login_as
):
    deck = await _make_deck(client, login_as)
    # Already a real VocabularyItem via quick-add, same identity promote
    # will resolve to (accent/case-insensitive on target_text + base_text).
    existing = (
        await client.post(
            "/api/cards/quick-add",
            json={"deck_id": deck["id"], "target_text": "PERRO", "base_text": "DOG"},
        )
    ).json()

    item = (
        await client.post(
            "/api/known-vocabulary",
            json={"course_id": deck["course_id"], "target_text": "perro"},
        )
    ).json()

    fake = FakeLLMProvider(WordTranslation(base_text="dog"))
    app.dependency_overrides[get_llm_provider] = lambda: fake

    resp = await client.post(
        f"/api/known-vocabulary/{item['id']}/promote", json={"deck_id": deck["id"]}
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["vocabulary_item"]["id"] == existing["vocabulary_item"]["id"]
    assert body["cards"][0]["id"] == existing["cards"][0]["id"]

    list_resp = await client.get(
        "/api/vocabulary-items", params={"course_id": deck["course_id"]}
    )
    assert len(list_resp.json()) == 1


async def test_full_set_unions_manual_entries_and_mastered_cards(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    deck = await _make_deck(client, login_as)
    await client.post(
        "/api/known-vocabulary", json={"course_id": deck["course_id"], "target_text": "Hola"}
    )
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={"course_id": deck["course_id"], "target_text": "perro", "base_text": "dog"},
        )
    ).json()
    # A REVIEW-state card has no HTTP path without real FSRS review timing
    # -- inserted directly via db_session, same convention used in
    # test_paste_in.py's equivalent fixture.
    db_session.add(
        Card(
            deck_id=uuid.UUID(deck["id"]),
            vocabulary_item_id=uuid.UUID(item["id"]),
            direction=CardDirection.TARGET_TO_BASE,
            state=CardState.REVIEW,
        )
    )
    await db_session.flush()

    resp = await client.get(
        "/api/known-vocabulary/full-set", params={"course_id": deck["course_id"]}
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["words"] == ["hola", "perro"]  # sorted, normalized


async def test_mastered_returns_full_details_and_excludes_non_review_cards(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    deck = await _make_deck(client, login_as)
    mastered_item = (
        await client.post(
            "/api/vocabulary-items",
            json={"course_id": deck["course_id"], "target_text": "perro", "base_text": "dog"},
        )
    ).json()
    new_item = (
        await client.post(
            "/api/vocabulary-items",
            json={"course_id": deck["course_id"], "target_text": "gato", "base_text": "cat"},
        )
    ).json()
    db_session.add_all(
        [
            Card(
                deck_id=uuid.UUID(deck["id"]),
                vocabulary_item_id=uuid.UUID(mastered_item["id"]),
                direction=CardDirection.TARGET_TO_BASE,
                state=CardState.REVIEW,
            ),
            # Not yet mastered -- should be excluded.
            Card(
                deck_id=uuid.UUID(deck["id"]),
                vocabulary_item_id=uuid.UUID(new_item["id"]),
                direction=CardDirection.TARGET_TO_BASE,
                state=CardState.NEW,
            ),
        ]
    )
    await db_session.flush()

    resp = await client.get(
        "/api/known-vocabulary/mastered", params={"course_id": deck["course_id"]}
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 1
    assert body[0]["target_text"] == "perro"
    assert body[0]["base_text"] == "dog"


async def test_mastered_dedupes_a_word_with_multiple_mastered_cards(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    deck = await _make_deck(client, login_as)
    item = (
        await client.post(
            "/api/vocabulary-items",
            json={"course_id": deck["course_id"], "target_text": "perro", "base_text": "dog"},
        )
    ).json()
    db_session.add_all(
        [
            Card(
                deck_id=uuid.UUID(deck["id"]),
                vocabulary_item_id=uuid.UUID(item["id"]),
                direction=CardDirection.TARGET_TO_BASE,
                state=CardState.REVIEW,
            ),
            Card(
                deck_id=uuid.UUID(deck["id"]),
                vocabulary_item_id=uuid.UUID(item["id"]),
                direction=CardDirection.BASE_TO_TARGET,
                state=CardState.REVIEW,
            ),
        ]
    )
    await db_session.flush()

    resp = await client.get(
        "/api/known-vocabulary/mastered", params={"course_id": deck["course_id"]}
    )

    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1


async def test_manual_add_same_word_does_not_collide_across_users_in_same_course(
    client: AsyncClient, login_as
):
    """Unique constraint is (user_id, course_id, target_text), not just
    (course_id, target_text) -- two users sharing a course can each know
    the same word.
    """
    deck_a = await _make_deck(client, login_as)
    resp_a = await client.post(
        "/api/known-vocabulary",
        json={"course_id": deck_a["course_id"], "target_text": "sol"},
    )

    await _make_deck_in_course(client, login_as, deck_a["course_id"])
    resp_b = await client.post(
        "/api/known-vocabulary",
        json={"course_id": deck_a["course_id"], "target_text": "sol"},
    )

    assert resp_a.status_code == 201, resp_a.text
    assert resp_b.status_code == 201, resp_b.text
    assert resp_a.json()["id"] != resp_b.json()["id"]


async def test_bulk_add_does_not_collide_across_users_in_same_course(
    client: AsyncClient, login_as
):
    deck_a = await _make_deck(client, login_as)
    resp_a = await client.post(
        "/api/known-vocabulary/bulk",
        json={"course_id": deck_a["course_id"], "target_texts": ["luna"]},
    )

    await _make_deck_in_course(client, login_as, deck_a["course_id"])
    resp_b = await client.post(
        "/api/known-vocabulary/bulk",
        json={"course_id": deck_a["course_id"], "target_texts": ["luna"]},
    )

    assert resp_a.json()["inserted_count"] == 1
    assert resp_b.json()["inserted_count"] == 1  # not swallowed by the other user's row


async def test_list_full_set_and_mastered_exclude_other_users_data(
    client: AsyncClient, db_session: AsyncSession, login_as
):
    deck_a = await _make_deck(client, login_as)
    await client.post(
        "/api/known-vocabulary",
        json={"course_id": deck_a["course_id"], "target_text": "estrella"},
    )
    item_a = (
        await client.post(
            "/api/vocabulary-items",
            json={"course_id": deck_a["course_id"], "target_text": "perro", "base_text": "dog"},
        )
    ).json()

    deck_b = await _make_deck_in_course(client, login_as, deck_a["course_id"])
    await client.post(
        "/api/known-vocabulary",
        json={"course_id": deck_a["course_id"], "target_text": "planeta"},
    )
    item_b = (
        await client.post(
            "/api/vocabulary-items",
            json={"course_id": deck_a["course_id"], "target_text": "gato", "base_text": "cat"},
        )
    ).json()

    db_session.add_all(
        [
            Card(
                deck_id=uuid.UUID(deck_a["id"]),
                vocabulary_item_id=uuid.UUID(item_a["id"]),
                direction=CardDirection.TARGET_TO_BASE,
                state=CardState.REVIEW,
            ),
            Card(
                deck_id=uuid.UUID(deck_b["id"]),
                vocabulary_item_id=uuid.UUID(item_b["id"]),
                direction=CardDirection.TARGET_TO_BASE,
                state=CardState.REVIEW,
            ),
        ]
    )
    await db_session.flush()

    await login_as(deck_a["user_id"])
    list_resp = await client.get(
        "/api/known-vocabulary", params={"course_id": deck_a["course_id"]}
    )
    assert [i["target_text"] for i in list_resp.json()] == ["estrella"]

    full_set_resp = await client.get(
        "/api/known-vocabulary/full-set", params={"course_id": deck_a["course_id"]}
    )
    assert full_set_resp.json()["words"] == ["estrella", "perro"]

    mastered_resp = await client.get(
        "/api/known-vocabulary/mastered", params={"course_id": deck_a["course_id"]}
    )
    assert [i["target_text"] for i in mastered_resp.json()] == ["perro"]


async def test_delete_someone_elses_known_vocabulary_is_403(client: AsyncClient, login_as):
    deck_a = await _make_deck(client, login_as)
    item = (
        await client.post(
            "/api/known-vocabulary",
            json={"course_id": deck_a["course_id"], "target_text": "gato"},
        )
    ).json()

    await _make_deck_in_course(client, login_as, deck_a["course_id"])
    resp = await client.delete(f"/api/known-vocabulary/{item['id']}")
    assert resp.status_code == 403


async def test_promote_someone_elses_known_vocabulary_is_403(client: AsyncClient, login_as):
    deck_a = await _make_deck(client, login_as)
    item = (
        await client.post(
            "/api/known-vocabulary",
            json={"course_id": deck_a["course_id"], "target_text": "perro"},
        )
    ).json()

    await _make_deck_in_course(client, login_as, deck_a["course_id"])
    resp = await client.post(
        f"/api/known-vocabulary/{item['id']}/promote", json={"deck_id": deck_a["id"]}
    )
    assert resp.status_code == 403


async def test_promote_into_someone_elses_deck_is_403(client: AsyncClient, login_as):
    deck_a = await _make_deck(client, login_as)
    item = (
        await client.post(
            "/api/known-vocabulary",
            json={"course_id": deck_a["course_id"], "target_text": "perro"},
        )
    ).json()

    deck_b = await _make_deck_in_course(client, login_as, deck_a["course_id"])
    await login_as(deck_a["user_id"])  # own the item, but not deck_b
    resp = await client.post(
        f"/api/known-vocabulary/{item['id']}/promote", json={"deck_id": deck_b["id"]}
    )
    assert resp.status_code == 403
