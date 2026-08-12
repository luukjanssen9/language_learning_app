import uuid

from httpx import AsyncClient


async def test_create_and_get_language(client: AsyncClient):
    create_resp = await client.post("/api/languages", json={"code": "en", "name": "English"})
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["code"] == "en"
    assert body["name"] == "English"
    assert body["script_direction"] == "ltr"
    assert body["grammar_config"] == {}

    get_resp = await client.get(f"/api/languages/{body['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == body["id"]


async def test_list_languages_includes_created(client: AsyncClient):
    await client.post("/api/languages", json={"code": "es", "name": "Spanish"})
    list_resp = await client.get("/api/languages")
    assert list_resp.status_code == 200
    assert "es" in [item["code"] for item in list_resp.json()]


async def test_get_language_404(client: AsyncClient):
    resp = await client.get(f"/api/languages/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_update_and_delete_language(client: AsyncClient):
    created = (
        await client.post("/api/languages", json={"code": "fr", "name": "French"})
    ).json()

    patch_resp = await client.patch(f"/api/languages/{created['id']}", json={"name": "Français"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Français"

    delete_resp = await client.delete(f"/api/languages/{created['id']}")
    assert delete_resp.status_code == 204

    assert (await client.get(f"/api/languages/{created['id']}")).status_code == 404


async def test_duplicate_language_code_conflicts(client: AsyncClient):
    await client.post("/api/languages", json={"code": "dup", "name": "Dup"})
    resp = await client.post("/api/languages", json={"code": "dup", "name": "Dup2"})
    assert resp.status_code == 409
