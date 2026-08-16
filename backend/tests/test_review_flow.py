import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient


async def _make_deck(client: AsyncClient, login_as) -> dict:
    """Builds Language(x2) -> Course -> User -> Deck via HTTP, same
    convention as test_course_deck_card_flow.py. Returns the deck dict
    with `_course_id` stashed on it (cards need vocabulary items, which
    need the course). Logs in as the new user before returning.
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
                "slug": f"en-es-review-{suffix}",
            },
        )
    ).json()
    user = (
        await client.post(
            "/api/users",
            json={"email": f"review-{suffix}@example.com", "display_name": "Review Test"},
        )
    ).json()
    await login_as(user["id"])
    deck = (
        await client.post(
            "/api/decks", json={"course_id": course["id"], "name": "Review test deck"}
        )
    ).json()
    deck["_course_id"] = course["id"]
    return deck


async def _make_card(client: AsyncClient, deck_id: str, course_id: str) -> dict:
    suffix = uuid.uuid4().hex[:8]
    vocab = (
        await client.post(
            "/api/vocabulary-items",
            json={
                "course_id": course_id,
                "target_text": f"palabra-{suffix}",
                "base_text": f"word-{suffix}",
            },
        )
    ).json()
    card_resp = await client.post(
        "/api/cards", json={"deck_id": deck_id, "vocabulary_item_id": vocab["id"]}
    )
    return card_resp.json()


async def test_review_new_card_transitions_out_of_new_state(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    card = await _make_card(client, deck["id"], deck["_course_id"])

    resp = await client.post(f"/api/cards/{card['id']}/review", json={"rating": "good"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["card"]["state"] == "learning"
    assert body["card"]["due_at"] is not None
    assert body["card"]["reps"] == 1
    assert body["review_log"]["card_id"] == card["id"]
    assert body["review_log"]["state_before"] == "new"
    assert body["review_log"]["elapsed_days"] is None


async def test_review_missing_card_404s(client: AsyncClient, login_as):
    user = (
        await client.post(
            "/api/users", json={"email": "missing-card@example.com", "display_name": "X"}
        )
    ).json()
    await login_as(user["id"])
    resp = await client.post(f"/api/cards/{uuid.uuid4()}/review", json={"rating": "good"})
    assert resp.status_code == 404


async def test_review_invalid_rating_422s(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    card = await _make_card(client, deck["id"], deck["_course_id"])

    resp = await client.post(f"/api/cards/{card['id']}/review", json={"rating": "excellent"})
    assert resp.status_code == 422


async def test_review_naive_reviewed_at_422s(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    card = await _make_card(client, deck["id"], deck["_course_id"])

    resp = await client.post(
        f"/api/cards/{card['id']}/review",
        json={"rating": "good", "reviewed_at": "2026-01-01T00:00:00"},
    )
    assert resp.status_code == 422


async def test_multi_step_learning_then_graduation_via_backdated_reviewed_at(
    client: AsyncClient, login_as
):
    deck = await _make_deck(client, login_as)
    card = await _make_card(client, deck["id"], deck["_course_id"])

    t0 = datetime.now(UTC) - timedelta(hours=1)
    resp1 = await client.post(
        f"/api/cards/{card['id']}/review",
        json={"rating": "good", "reviewed_at": t0.isoformat()},
    )
    assert resp1.json()["card"]["state"] == "learning"

    t1 = t0 + timedelta(minutes=11)
    resp2 = await client.post(
        f"/api/cards/{card['id']}/review",
        json={"rating": "good", "reviewed_at": t1.isoformat()},
    )
    assert resp2.json()["card"]["state"] == "review"


async def test_review_then_lapse_then_relearning(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    card = await _make_card(client, deck["id"], deck["_course_id"])

    resp1 = await client.post(f"/api/cards/{card['id']}/review", json={"rating": "easy"})
    assert resp1.json()["card"]["state"] == "review"

    resp2 = await client.post(f"/api/cards/{card['id']}/review", json={"rating": "again"})
    body = resp2.json()
    assert body["card"]["state"] == "relearning"
    assert body["card"]["lapses"] == 1
    assert body["review_log"]["state_before"] == "review"


async def test_reviewed_at_in_future_400s(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    card = await _make_card(client, deck["id"], deck["_course_id"])

    future = datetime.now(UTC) + timedelta(days=1)
    resp = await client.post(
        f"/api/cards/{card['id']}/review",
        json={"rating": "good", "reviewed_at": future.isoformat()},
    )
    assert resp.status_code == 400


async def test_reviewed_at_before_last_review_400s(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    card = await _make_card(client, deck["id"], deck["_course_id"])

    t0 = datetime.now(UTC) - timedelta(hours=1)
    await client.post(
        f"/api/cards/{card['id']}/review",
        json={"rating": "good", "reviewed_at": t0.isoformat()},
    )

    earlier = t0 - timedelta(hours=1)
    resp = await client.post(
        f"/api/cards/{card['id']}/review",
        json={"rating": "good", "reviewed_at": earlier.isoformat()},
    )
    assert resp.status_code == 400


async def test_due_queue_excludes_not_due_and_uncapped_new_cards(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    await _make_card(client, deck["id"], deck["_course_id"])  # a NEW card
    reviewed_card = await _make_card(client, deck["id"], deck["_course_id"])
    await client.post(
        f"/api/cards/{reviewed_card['id']}/review", json={"rating": "good"}
    )  # due ~10 minutes from now, not yet due

    resp = await client.get(
        "/api/cards/due", params={"deck_id": deck["id"], "new_limit": 0}
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_due_queue_orders_most_overdue_first(client: AsyncClient, login_as):
    deck = await _make_deck(client, login_as)
    card_a = await _make_card(client, deck["id"], deck["_course_id"])
    card_b = await _make_card(client, deck["id"], deck["_course_id"])

    now = datetime.now(UTC)
    await client.post(
        f"/api/cards/{card_a['id']}/review",
        json={"rating": "good", "reviewed_at": (now - timedelta(minutes=30)).isoformat()},
    )
    await client.post(
        f"/api/cards/{card_b['id']}/review",
        json={"rating": "good", "reviewed_at": (now - timedelta(minutes=15)).isoformat()},
    )

    resp = await client.get(
        "/api/cards/due", params={"deck_id": deck["id"], "new_limit": 0}
    )
    ids = [c["id"] for c in resp.json()]
    assert ids == [card_a["id"], card_b["id"]]


async def test_due_queue_appends_new_cards_oldest_first_capped_at_new_limit(
    client: AsyncClient, login_as
):
    deck = await _make_deck(client, login_as)
    due_card = await _make_card(client, deck["id"], deck["_course_id"])
    await client.post(
        f"/api/cards/{due_card['id']}/review",
        json={
            "rating": "good",
            "reviewed_at": (datetime.now(UTC) - timedelta(minutes=30)).isoformat(),
        },
    )
    new_1 = await _make_card(client, deck["id"], deck["_course_id"])
    new_2 = await _make_card(client, deck["id"], deck["_course_id"])
    await _make_card(client, deck["id"], deck["_course_id"])  # new_3, beyond the cap

    # new_limit is 3, not 2: due_card's own review above is itself a
    # NEW-card's first review (state_before == NEW), which counts toward
    # today's already-shown total the same as any other (see
    # api/routes/cards.py's _count_new_cards_shown_today) -- it already
    # spent one of the requested slots before new_1/new_2 are considered,
    # leaving exactly 2 remaining, same as this test intends to verify.
    resp = await client.get(
        "/api/cards/due", params={"deck_id": deck["id"], "new_limit": 3}
    )
    ids = [c["id"] for c in resp.json()]
    assert ids == [due_card["id"], new_1["id"], new_2["id"]]


async def test_due_queue_requires_deck_id(client: AsyncClient, login_as):
    user = (
        await client.post(
            "/api/users", json={"email": "due-no-deck@example.com", "display_name": "X"}
        )
    ).json()
    await login_as(user["id"])
    resp = await client.get("/api/cards/due")
    assert resp.status_code == 422


async def test_due_queue_scopes_to_deck(client: AsyncClient, login_as):
    deck_a = await _make_deck(client, login_as)
    card_a = await _make_card(client, deck_a["id"], deck_a["_course_id"])
    deck_b = await _make_deck(client, login_as)
    card_b = await _make_card(client, deck_b["id"], deck_b["_course_id"])

    await login_as(deck_a["user_id"])
    resp = await client.get(
        "/api/cards/due", params={"deck_id": deck_a["id"], "new_limit": 10}
    )
    ids = [c["id"] for c in resp.json()]
    assert card_a["id"] in ids
    assert card_b["id"] not in ids


async def test_due_queue_unknown_deck_404s(client: AsyncClient, login_as):
    user = (
        await client.post(
            "/api/users", json={"email": "due-unknown-deck@example.com", "display_name": "X"}
        )
    ).json()
    await login_as(user["id"])
    resp = await client.get("/api/cards/due", params={"deck_id": str(uuid.uuid4())})
    assert resp.status_code == 404


async def test_due_queue_wrong_deck_owner_is_403(client: AsyncClient, login_as):
    deck_a = await _make_deck(client, login_as)
    # Second deck exists only to switch the logged-in session to a
    # different user before the request below.
    await _make_deck(client, login_as)

    resp = await client.get("/api/cards/due", params={"deck_id": deck_a["id"]})
    assert resp.status_code == 403


async def test_review_someone_elses_card_is_403(client: AsyncClient, login_as):
    deck_a = await _make_deck(client, login_as)
    card = await _make_card(client, deck_a["id"], deck_a["_course_id"])
    # Second deck exists only to switch the logged-in session to a
    # different user before the request below.
    await _make_deck(client, login_as)

    resp = await client.post(f"/api/cards/{card['id']}/review", json={"rating": "good"})
    assert resp.status_code == 403
