import uuid

from httpx import AsyncClient


async def _make_deck(client: AsyncClient) -> dict:
    """Builds Language(x2) -> Course -> User -> Deck via HTTP, same
    convention as test_review_flow.py. Returns the deck dict with
    `_course_id` stashed on it (cards need vocabulary items, which need
    the course).
    """
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
                "slug": f"en-es-filter-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"filter-{suffix}@example.com", "display_name": "Filter Test"},
        )
    ).json()
    deck = (
        await client.post(
            "/api/decks",
            json={"user_id": user["id"], "course_id": course["id"], "name": "Filter test deck"},
        )
    ).json()
    deck["_course_id"] = course["id"]
    return deck


async def _make_card(client: AsyncClient, deck_id: str, course_id: str, user_id: str) -> dict:
    suffix = uuid.uuid4().hex[:8]
    vocab = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course_id,
                "user_id": user_id,
                "target_text": f"palabra-{suffix}",
                "base_text": f"word-{suffix}",
            },
        )
    ).json()
    card_resp = await client.post(
        "/api/cards",
        params={"user_id": user_id},
        json={"deck_id": deck_id, "vocabulary_item_id": vocab["id"]},
    )
    return card_resp.json()


async def test_list_cards_without_deck_id_returns_all(client: AsyncClient):
    deck = await _make_deck(client)
    card = await _make_card(client, deck["id"], deck["_course_id"], deck["user_id"])

    resp = await client.get("/api/cards", params={"user_id": deck["user_id"]})
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert card["id"] in ids


async def test_list_cards_filters_by_deck_id(client: AsyncClient):
    deck_a = await _make_deck(client)
    deck_b = await _make_deck(client)
    card_a = await _make_card(client, deck_a["id"], deck_a["_course_id"], deck_a["user_id"])
    await _make_card(client, deck_b["id"], deck_b["_course_id"], deck_b["user_id"])

    resp = await client.get(
        "/api/cards", params={"deck_id": deck_a["id"], "user_id": deck_a["user_id"]}
    )
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert ids == [card_a["id"]]


async def test_list_cards_without_deck_id_excludes_other_users_cards(client: AsyncClient):
    deck_a = await _make_deck(client)
    deck_b = await _make_deck(client)
    card_a = await _make_card(client, deck_a["id"], deck_a["_course_id"], deck_a["user_id"])
    await _make_card(client, deck_b["id"], deck_b["_course_id"], deck_b["user_id"])

    resp = await client.get("/api/cards", params={"user_id": deck_a["user_id"]})
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert ids == [card_a["id"]]


async def test_get_card_from_another_users_deck_is_403(client: AsyncClient):
    deck_a = await _make_deck(client)
    deck_b = await _make_deck(client)
    card_a = await _make_card(client, deck_a["id"], deck_a["_course_id"], deck_a["user_id"])

    resp = await client.get(f"/api/cards/{card_a['id']}", params={"user_id": deck_b["user_id"]})
    assert resp.status_code == 403


async def test_list_cards_wrong_deck_owner_is_403(client: AsyncClient):
    deck_a = await _make_deck(client)
    deck_b = await _make_deck(client)

    resp = await client.get(
        "/api/cards", params={"deck_id": deck_a["id"], "user_id": deck_b["user_id"]}
    )
    assert resp.status_code == 403
