REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"


async def test_register_succeeds(client):
    response = await client.post(REGISTER, json={"email": "a@example.com", "password": "secret123"})

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "a@example.com"
    assert body["role"] == "user"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_email_returns_409(client):
    payload = {"email": "a@example.com", "password": "secret123"}
    await client.post(REGISTER, json=payload)

    same = await client.post(REGISTER, json=payload)
    different_case = await client.post(
        REGISTER, json={"email": "A@Example.com", "password": "secret123"}
    )

    assert same.status_code == 409
    assert different_case.status_code == 409


async def test_register_invalid_email_returns_422(client):
    response = await client.post(REGISTER, json={"email": "not-an-email", "password": "secret123"})

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "email"


async def test_register_short_password_returns_422(client):
    response = await client.post(REGISTER, json={"email": "a@example.com", "password": "short"})

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "password"


async def test_login_succeeds(client):
    await client.post(REGISTER, json={"email": "a@example.com", "password": "secret123"})

    response = await client.post(LOGIN, data={"username": "a@example.com", "password": "secret123"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_wrong_password_returns_401(client):
    await client.post(REGISTER, json={"email": "a@example.com", "password": "secret123"})

    response = await client.post(LOGIN, data={"username": "a@example.com", "password": "wrong-password"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_login_unknown_user_returns_same_401(client):
    await client.post(REGISTER, json={"email": "a@example.com", "password": "secret123"})
    wrong_password = await client.post(
        LOGIN, data={"username": "a@example.com", "password": "wrong-password"}
    )

    unknown_user = await client.post(
        LOGIN, data={"username": "nobody@example.com", "password": "secret123"}
    )

    assert unknown_user.status_code == 401
    assert unknown_user.json() == wrong_password.json()
