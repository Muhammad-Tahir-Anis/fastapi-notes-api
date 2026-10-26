# FastAPI Notes API

A small REST API where users register, log in, and manage their own notes.
Built with FastAPI, async SQLAlchemy 2.0, PostgreSQL, Alembic migrations, and JWT authentication.

## Stack

- **FastAPI** with async endpoints
- **PostgreSQL 16** via **SQLAlchemy 2.0** (async) and the `asyncpg` driver
- **Alembic** for schema migrations
- **JWT** access tokens (PyJWT) and **Argon2** password hashing (pwdlib)
- **pytest** + **httpx** for tests, run against a separate test database
- **uv** for dependency management, **Docker Compose** for Postgres

## Quick start

Requirements: Python 3.13+, [uv](https://docs.astral.sh/uv/), Docker.

```bash
git clone <repo-url> && cd fastapi-notes-api
cp .env.example .env          # then set SECRET_KEY and a real password
uv sync
docker compose up -d          # starts Postgres
uv run alembic upgrade head   # creates the tables
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API docs. Use the **Authorize**
button with the email and password of a registered user.

## Run the tests

```bash
uv run pytest
```

The tests need the Postgres container running. They create a throwaway database named
`<POSTGRES_DB>_test`, so your development data is never touched, and drop it afterwards.

## Endpoints

All routes except `/health` live under `/api/v1`.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | none | Create a user (201, 409 if the email exists) |
| POST | `/api/v1/auth/login` | none | Returns a JWT access token (form fields `username` = email, `password`) |
| GET | `/api/v1/notes` | JWT | List my notes, with `limit` (1-100, default 20) and `offset` |
| POST | `/api/v1/notes` | JWT | Create a note |
| GET | `/api/v1/notes/{id}` | JWT | Get one (404 if it isn't mine) |
| PUT | `/api/v1/notes/{id}` | JWT | Replace one |
| DELETE | `/api/v1/notes/{id}` | JWT | Delete one (204) |
| GET | `/health` | none | Health check, including a database ping |

Errors always use one JSON shape:

```json
{"error": {"code": 422, "message": "Validation failed", "details": [{"field": "email", "message": "..."}]}}
```

## Project layout

```
app/
├── main.py            # app, routers, exception handlers, /health
├── api/
│   ├── deps.py        # get_current_user dependency
│   └── v1/            # auth.py, notes.py (thin HTTP layer)
├── services/          # business logic (user.py, note.py)
├── schemas/           # Pydantic request/response models
├── models/            # SQLAlchemy models: User, Note
├── core/              # config, security (hashing, JWT), errors, logging
└── db/                # declarative base, engine, session
alembic/               # migrations
tests/                 # pytest suite
```

## Design notes

**Authentication flow.** `/auth/login` verifies the password and returns a signed JWT whose
`sub` claim is the user id and whose `exp` claim limits its lifetime (30 minutes by default).
Protected routes depend on `get_current_user`, which decodes and verifies the token, loads
the user, and rejects inactive users. Any problem with the token gives the same `401`.

**Password hashing.** Passwords are hashed with Argon2id and never stored or logged in plain
text. Login always runs one hash verification, even for unknown emails (against a dummy hash),
so response time doesn't reveal which emails are registered. Wrong password and unknown email
return an identical `401`.

**Ownership checks.** Every note query filters by both the note id and the owner id, inside
the SQL query itself. Someone else's note returns `404`, not `403`, so note ids of other users
can't be probed. `owner_id` is never accepted from the client.

**Layering.** Routers handle HTTP only, services hold the logic and raise plain Python
exceptions (for example `EmailAlreadyRegistered`), and routers translate those into status codes.

**Duplicate emails.** The service checks for an existing email for a friendly error, and the
unique index on `users.email` is the final guard: a concurrent duplicate insert is caught as an
`IntegrityError` and also returns `409`.

**Error handling and logging.** Custom handlers give HTTP errors, validation errors and
unexpected errors one JSON shape. Unexpected errors return a generic `500` with no internal
details, while the full traceback goes to the log. Passwords and tokens are never logged.

**Migrations.** The schema is managed by Alembic only (autogenerate with a naming convention
for constraints). A test builds the schema from scratch with `alembic upgrade head` and rolls
it back with `alembic downgrade base`.
