"""Integration tests for POST /cards/quick-add and the production-gate/
daily-new-card-cap logic in GET /cards/due, through the live API + DB
(same `client`/`db_session` fixtures as test_review_flow.py).
"""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

DUAL_DIRECTION_CONFIG = {
    "vocab_deck": {
        "dual_direction_cards": True,
        "production_gate": {
            "min_successful_recognition_reviews": 2,
            "min_days_since_note_added": 9999,
        },
    }
}


async def _make_deck(client: AsyncClient, *, target_grammar_config: dict | None = None) -> dict:
    suffix = uuid.uuid4().hex[:6]
    lang_en = (
        await client.post("/api/languages", json={"code": f"en-{suffix}", "name": "English"})
    ).json()
    lang_target = (
        await client.post(
            "/api/languages",
            json={
                "code": f"zh-{suffix}",
                "name": "Chinese",
                "grammar_config": target_grammar_config or {},
            },
        )
    ).json()
    course = (
        await client.post(
            "/api/courses",
            json={
                "base_language_id": lang_en["id"],
                "target_language_id": lang_target["id"],
                "name": "English to Chinese",
                "slug": f"en-zh-quickadd-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"quickadd-{suffix}@example.com", "display_name": "Quick Add Test"},
        )
    ).json()
    deck = (
        await client.post(
            "/api/decks",
            json={"user_id": user["id"], "course_id": course["id"], "name": "Quick add deck"},
        )
    ).json()
    return deck


async def _quick_add(client: AsyncClient, deck_id: str, **overrides) -> dict:
    payload = {
        "deck_id": deck_id,
        "target_text": "你好",
        "base_text": "hello",
        "source": "Podcast: ChinesePod - Greetings",
        "example_sentence": "你好，很高兴认识你。",
        "example_sentence_translation": "Hello, nice to meet you.",
        "tags": ["greetings"],
        "attributes": {"pinyin": "nǐ hǎo"},
        **overrides,
    }
    resp = await client.post("/api/cards/quick-add", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_quick_add_single_direction_language_creates_one_card(client: AsyncClient):
    deck = await _make_deck(client)  # no vocab_deck config -> single-direction

    body = await _quick_add(client, deck["id"])

    assert body["vocabulary_item"]["target_text"] == "你好"
    assert body["vocabulary_item"]["source"] == "Podcast: ChinesePod - Greetings"
    assert body["vocabulary_item"]["example_sentence"] == "你好，很高兴认识你。"
    assert body["vocabulary_item"]["tags"] == ["greetings"]
    assert body["vocabulary_item"]["attributes"] == {"pinyin": "nǐ hǎo"}
    assert len(body["cards"]) == 1
    assert body["cards"][0]["direction"] == "target_to_base"
    assert body["cards"][0]["state"] == "new"
    assert body["cards"][0]["vocabulary_item"]["target_text"] == "你好"


async def test_quick_add_dual_direction_language_creates_recognition_and_suspended_production(
    client: AsyncClient,
):
    deck = await _make_deck(client, target_grammar_config=DUAL_DIRECTION_CONFIG)

    body = await _quick_add(client, deck["id"])

    assert len(body["cards"]) == 2
    recognition, production = body["cards"]
    assert recognition["direction"] == "target_to_base"
    assert recognition["state"] == "new"
    assert production["direction"] == "base_to_target"
    assert production["state"] == "suspended"


async def test_reviewing_a_suspended_card_is_rejected(client: AsyncClient):
    deck = await _make_deck(client, target_grammar_config=DUAL_DIRECTION_CONFIG)
    body = await _quick_add(client, deck["id"])
    _recognition, production = body["cards"]

    resp = await client.post(f"/api/cards/{production['id']}/review", json={"rating": "good"})

    assert resp.status_code == 400


async def test_production_card_unlocks_after_enough_successful_recognition_reviews(
    client: AsyncClient,
):
    deck = await _make_deck(client, target_grammar_config=DUAL_DIRECTION_CONFIG)
    body = await _quick_add(client, deck["id"])
    recognition, production = body["cards"]

    # DUAL_DIRECTION_CONFIG requires 2 successful reviews (min_days is
    # effectively unreachable at 9999, so only the review-count path can
    # unlock it here).
    for _ in range(2):
        resp = await client.post(
            f"/api/cards/{recognition['id']}/review", json={"rating": "good"}
        )
        assert resp.status_code == 200

    due_resp = await client.get("/api/cards/due", params={"deck_id": deck["id"]})
    ids_and_states = {c["id"]: c["state"] for c in due_resp.json()}
    assert ids_and_states.get(production["id"]) == "new"


async def test_production_card_stays_suspended_before_gate_is_met(client: AsyncClient):
    deck = await _make_deck(client, target_grammar_config=DUAL_DIRECTION_CONFIG)
    body = await _quick_add(client, deck["id"])
    recognition, production = body["cards"]

    # Only one successful review -- below the config's threshold of 2.
    await client.post(f"/api/cards/{recognition['id']}/review", json={"rating": "good"})

    due_resp = await client.get("/api/cards/due", params={"deck_id": deck["id"]})
    ids = [c["id"] for c in due_resp.json()]
    assert production["id"] not in ids


async def test_production_card_unlocks_via_day_based_gate(client: AsyncClient):
    day_gated_config = {
        "vocab_deck": {
            "dual_direction_cards": True,
            "production_gate": {
                "min_successful_recognition_reviews": 9999,
                "min_days_since_note_added": 0,
            },
        }
    }
    deck = await _make_deck(client, target_grammar_config=day_gated_config)
    body = await _quick_add(client, deck["id"])
    _recognition, production = body["cards"]

    # Zero reviews -- only the "0 days since the note was added" path can
    # unlock it, and it's already true the instant the note exists.
    due_resp = await client.get("/api/cards/due", params={"deck_id": deck["id"]})
    ids_and_states = {c["id"]: c["state"] for c in due_resp.json()}
    assert ids_and_states.get(production["id"]) == "new"


async def test_daily_new_card_cap_limits_new_cards_across_requests(client: AsyncClient):
    deck = await _make_deck(client)
    resp = await client.patch(f"/api/decks/{deck['id']}", json={"daily_new_card_cap": 1})
    assert resp.status_code == 200

    first = await _quick_add(client, deck["id"], target_text="第一", base_text="first")
    await _quick_add(client, deck["id"], target_text="第二", base_text="second")

    # No explicit new_limit override -- exercises the deck's own
    # configured cap, not a request-level parameter.
    await client.post(
        f"/api/cards/{first['cards'][0]['id']}/review", json={"rating": "good"}
    )

    due_resp = await client.get("/api/cards/due", params={"deck_id": deck["id"]})
    new_cards = [c for c in due_resp.json() if c["state"] == "new"]
    assert new_cards == []


async def test_quick_add_is_idempotent_on_matching_target_and_base_text(client: AsyncClient):
    deck = await _make_deck(client)

    first = await _quick_add(client, deck["id"])
    # Different casing/accents on both fields -- still the same word.
    second = await _quick_add(
        client, deck["id"], target_text="你好", base_text="HELLO"
    )

    assert first["vocabulary_item"]["id"] == second["vocabulary_item"]["id"]
    assert first["cards"][0]["id"] == second["cards"][0]["id"]

    list_resp = await client.get(
        "/api/vocabulary-items",
        params={"course_id": deck["course_id"], "user_id": deck["user_id"]},
    )
    assert len(list_resp.json()) == 1


async def test_quick_add_keeps_distinct_senses_of_a_homonym_separate(client: AsyncClient):
    # Same target_text, genuinely different meanings -- e.g. Dutch "bank"
    # -> bank/couch/bench. Differing on base_text must NOT be merged.
    deck = await _make_deck(client)

    bank_the_institution = await _quick_add(
        client, deck["id"], target_text="bank", base_text="the (financial) bank"
    )
    bank_the_couch = await _quick_add(client, deck["id"], target_text="bank", base_text="couch")

    assert (
        bank_the_institution["vocabulary_item"]["id"] != bank_the_couch["vocabulary_item"]["id"]
    )

    list_resp = await client.get(
        "/api/vocabulary-items",
        params={"course_id": deck["course_id"], "user_id": deck["user_id"]},
    )
    assert len(list_resp.json()) == 2


async def test_quick_add_reuses_note_but_adds_missing_card_in_a_different_deck(
    client: AsyncClient,
):
    deck = await _make_deck(client)
    first = await _quick_add(client, deck["id"])

    # A second deck for the SAME user in the same course (e.g. a separate
    # "Podcast vocab" deck) -- note-reuse is scoped by user, not by deck
    # (VocabularyItem.user_id), so this must stay same-user to still
    # exercise cross-deck reuse; a different user's deck would instead
    # correctly create its own separate note (see note_cards.py).
    second_deck = (
        await client.post(
            "/api/decks",
            json={
                "user_id": deck["user_id"],
                "course_id": deck["course_id"],
                "name": "Second deck",
            },
        )
    ).json()

    second = await _quick_add(client, second_deck["id"])

    # Same note reused across decks, but each deck gets its own card(s)
    # for it.
    assert first["vocabulary_item"]["id"] == second["vocabulary_item"]["id"]
    assert first["cards"][0]["id"] != second["cards"][0]["id"]
    assert second["cards"][0]["deck_id"] == second_deck["id"]


async def test_quick_add_does_not_reuse_another_users_note_in_the_same_course(
    client: AsyncClient,
):
    """Unlike the same-user cross-deck case above, a different user's
    quick-add for the identical word must create its own separate note --
    VocabularyItem.user_id scoping (see note_cards.py) means personal
    vocabulary is never silently shared across users, even within one
    course.
    """
    deck = await _make_deck(client)
    first = await _quick_add(client, deck["id"])

    other_user_resp = await client.post(
        "/api/users", json={"email": "other-user@example.com", "display_name": "Other User"}
    )
    other_user_id = other_user_resp.json()["id"]
    other_deck = (
        await client.post(
            "/api/decks",
            json={
                "user_id": other_user_id,
                "course_id": deck["course_id"],
                "name": "Other user's deck",
            },
        )
    ).json()

    second = await _quick_add(client, other_deck["id"])

    assert first["vocabulary_item"]["id"] != second["vocabulary_item"]["id"]
    assert second["vocabulary_item"]["user_id"] == other_user_id


async def test_daily_new_card_cap_does_not_count_yesterdays_reviews(client: AsyncClient):
    deck = await _make_deck(client)
    resp = await client.patch(f"/api/decks/{deck['id']}", json={"daily_new_card_cap": 1})
    assert resp.status_code == 200

    yesterday_card = await _quick_add(
        client, deck["id"], target_text="昨天", base_text="yesterday"
    )
    today_card = await _quick_add(client, deck["id"], target_text="今天", base_text="today")

    yesterday = datetime.now(UTC) - timedelta(days=1)
    await client.post(
        f"/api/cards/{yesterday_card['cards'][0]['id']}/review",
        json={"rating": "good", "reviewed_at": yesterday.isoformat()},
    )

    due_resp = await client.get("/api/cards/due", params={"deck_id": deck["id"]})
    new_ids = [c["id"] for c in due_resp.json() if c["state"] == "new"]
    assert new_ids == [today_card["cards"][0]["id"]]
