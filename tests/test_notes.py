NOTES = "/api/v1/notes"


async def create_note(client, headers, title="Title", body="Body"):
    response = await client.post(NOTES, json={"title": title, "body": body}, headers=headers)
    assert response.status_code == 201
    return response.json()


async def test_notes_without_token_returns_401(client):
    response = await client.get(NOTES)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == 401


async def test_notes_with_bad_token_returns_401(client):
    response = await client.get(NOTES, headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_create_and_get_note(client, auth_headers):
    created = await create_note(client, auth_headers, title="Groceries", body="milk")

    response = await client.get(f"{NOTES}/{created['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["title"] == "Groceries"
    assert response.json()["body"] == "milk"


async def test_create_note_with_empty_title_returns_422(client, auth_headers):
    response = await client.post(NOTES, json={"title": ""}, headers=auth_headers)

    assert response.status_code == 422


async def test_list_notes_pagination(client, auth_headers):
    for i in range(5):
        await create_note(client, auth_headers, title=f"note {i}")

    everything = (await client.get(NOTES, headers=auth_headers)).json()
    first_page = (await client.get(NOTES, params={"limit": 2}, headers=auth_headers)).json()
    second_page = (
        await client.get(NOTES, params={"limit": 2, "offset": 2}, headers=auth_headers)
    ).json()

    assert len(everything) == 5
    assert len(first_page) == 2 and len(second_page) == 2
    assert {n["id"] for n in first_page}.isdisjoint({n["id"] for n in second_page})


async def test_list_notes_rejects_invalid_limit(client, auth_headers):
    response = await client.get(NOTES, params={"limit": 0}, headers=auth_headers)

    assert response.status_code == 422


async def test_update_note(client, auth_headers):
    created = await create_note(client, auth_headers)

    response = await client.put(
        f"{NOTES}/{created['id']}",
        json={"title": "Updated", "body": "new body"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["body"] == "new body"


async def test_delete_note(client, auth_headers):
    created = await create_note(client, auth_headers)

    deleted = await client.delete(f"{NOTES}/{created['id']}", headers=auth_headers)
    fetched = await client.get(f"{NOTES}/{created['id']}", headers=auth_headers)

    assert deleted.status_code == 204
    assert fetched.status_code == 404


async def test_user_cannot_access_another_users_note(client, auth_headers, other_headers):
    note = await create_note(client, auth_headers, title="private")
    url = f"{NOTES}/{note['id']}"

    get = await client.get(url, headers=other_headers)
    put = await client.put(url, json={"title": "hacked"}, headers=other_headers)
    delete = await client.delete(url, headers=other_headers)
    other_list = await client.get(NOTES, headers=other_headers)

    assert get.status_code == 404
    assert put.status_code == 404
    assert delete.status_code == 404
    assert other_list.json() == []
    still_there = await client.get(url, headers=auth_headers)
    assert still_there.json()["title"] == "private"
