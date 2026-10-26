from fastapi import APIRouter

from app.main import app


async def test_health(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unknown_url_uses_error_format(client):
    response = await client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": 404, "message": "Not Found"}}


async def test_unexpected_error_returns_generic_500(client):
    router = APIRouter()

    @router.get("/boom")
    async def boom():
        raise RuntimeError("secret internal detail")

    app.include_router(router)
    try:
        response = await client.get("/boom")
    finally:
        app.router.routes.pop()

    assert response.status_code == 500
    assert response.json() == {"error": {"code": 500, "message": "Internal server error"}}
    assert "secret internal detail" not in response.text
