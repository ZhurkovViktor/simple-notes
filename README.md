# Personal Notes API

Personal Notes API is a small FastAPI backend for personal note management.
The project demonstrates a complete backend stack: authentication, protected
CRUD endpoints, PostgreSQL, SQLAlchemy, Alembic migrations, Docker Compose,
layered architecture, dependency injection, Unit of Work, and automated tests.

The main user flow is simple: a user registers, receives a JWT token, creates
notes, updates them, reads note history, uses predefined templates, and cannot
access notes that belong to another user.

---

## Implemented Stack

### 2.1 FastAPI Service

The API is implemented with FastAPI in `app/main.py` and routers under
`app/api/routers/`. The service exposes authentication, users, notes,
templates, and health-check endpoints.

The application can be opened at `http://localhost:8000/docs`, where Swagger UI
shows all available endpoints.

### 2.2 Poetry Environment Manager

Poetry manages project dependencies through `pyproject.toml` and fixed package
versions through `poetry.lock`. Runtime dependencies include FastAPI,
SQLAlchemy, asyncpg, Alembic, Pydantic, JWT, Argon2 password hashing, and
Dishka.

Development dependencies include pytest, pytest-asyncio, httpx, Ruff, aiosqlite,
and greenlet. Commands such as `poetry run pytest` and `poetry run ruff check .`
run inside the project environment.

### 2.3 Swagger and Pydantic Models

Swagger is generated automatically by FastAPI from routes and Pydantic schemas.
Request and response models are stored in `app/schemas/`.

For example, `UserRegister` validates email and password length, while
`UserResponse` returns only safe user fields and does not expose
`password_hash`. Notes use separate schemas for create, update, response, and
history responses.

### 2.4 FastAPI Service in Docker

The FastAPI application is containerized with `Dockerfile`. The image uses
Python 3.14, installs Poetry, installs production dependencies, copies the
project code, and starts Uvicorn.

In `compose.yaml`, the `app` service builds this image, exposes port `8000`,
loads `.env`, mounts the project into `/app`, runs Alembic migrations, and then
starts the API server.

### 2.5 Relational Database in Docker

PostgreSQL runs as the `db` service in `compose.yaml` using
`postgres:17-alpine`. The database name, user, and password are configured as
`notes`.

The database has a healthcheck with `pg_isready`, and the FastAPI app waits for
PostgreSQL to become healthy before starting. Data is stored in the
`postgres_data` Docker volume.

### 2.6 SQLAlchemy Automap Base

SQLAlchemy Automap is used for the `system_note_templates` table. The table is
created and filled by Alembic, then reflected at application startup in
`app/database/automap.py`.

`TemplateService` receives the reflected model and reads templates through
`TemplateRepository`. This demonstrates how to work with an existing database
table without writing a manual ORM class for it.

### 2.7 SQLAlchemy Declarative Base

Declarative Base is used for the main domain models in `app/database/models.py`.
The project defines `User`, `Note`, and `NoteHistory` as SQLAlchemy ORM classes.

These models describe the real database tables, columns, relationships, and
foreign keys. For example, `Note.owner_id` points to `users.id`, and
`NoteHistory.note_id` points to `notes.id`.

### 2.8 Alembic Migrations

Alembic migrations are stored in `migrations/versions/`. They create the
`users`, `notes`, `note_history`, and `system_note_templates` tables.

The Docker Compose command runs `alembic upgrade head` before starting Uvicorn.
This allows the project to start from an empty PostgreSQL database with one
command.

### 2.9 Basic Layered Architecture

The project follows a layered backend architecture. Routers handle HTTP,
services contain business logic, repositories access the database, and models
describe database tables.

This keeps responsibilities separated. For example, routers do not write SQL,
repositories do not know about HTTP, and services do not directly expose
Swagger-specific behavior.

### 2.10 Application Restructuring by Folders

The application is split into clear folders:

```text
app/api/routers     HTTP endpoints
app/core            settings, security, exceptions
app/database        engine, sessions, ORM models, Automap
app/repositories    database access layer
app/schemas         Pydantic request and response schemas
app/services        business logic
tests               automated tests
migrations          Alembic migrations
```

This structure makes the project easier to read, test, and extend.

### 2.11 FastAPI Built-in Dependency Injection

FastAPI dependency injection is used through `Depends`. The main examples are
`get_session`, `oauth2_scheme`, and `get_current_user` in
`app/api/dependencies.py`.

`get_current_user` extracts the Bearer token, decodes the JWT, loads the user
from the database, and provides the current user to protected endpoints.

### 2.12 Dishka Dependency Injection

Dishka is configured in `app/ioc.py`. It provides application-level and
request-level dependencies such as settings, database engine, session factory,
repositories, Unit of Work, and services.

The notes router uses Dishka with `FromDishka[NoteService]` and `@inject`.
FastAPI `Depends` is still used for HTTP-native dependencies like
`current_user`.

### 2.13 Unit of Work Pattern

The Unit of Work pattern is implemented in `app/unit_of_work.py`. It groups
repository operations into one transaction and provides `commit()` and
`rollback()`.

It is especially important when updating notes: the note update and the
`NoteHistory` insert must either both succeed or both roll back. This behavior
is covered by tests.

---

## Running the Project

Start the application and PostgreSQL:

```bash
docker compose up --build
```

Open Swagger UI:

```text
http://localhost:8000/docs
```

Stop containers without deleting database data:

```bash
docker compose down
```

Stop containers and delete local PostgreSQL data:

```bash
docker compose down -v
```

## Example Workflow in Swagger

### 1. Register User A

Open:

```text
POST /api/v1/auth/register
```

Request body:

```json
{
  "email": "user-a@example.com",
  "password": "qwerty123"
}
```

Expected result: `201 Created`.

### 2. Authorize as User A

Open the Swagger `Authorize` button and enter:

```text
username: user-a@example.com
password: qwerty123
```

Swagger sends these credentials to `POST /api/v1/auth/token`, receives an
access token, and uses it for protected requests.

### 3. Create a Note

Open:

```text
POST /api/v1/notes
```

Request body:

```json
{
  "title": "My first note",
  "content": "This note belongs to User A"
}
```

Expected result: `201 Created`. Save the returned `id`.

### 4. Update the Note

Open:

```text
PATCH /api/v1/notes/{note_id}
```

Use the saved note id and send:

```json
{
  "title": "Updated note",
  "content": "Updated note content"
}
```

Expected result: `200 OK`.

### 5. Get Note History

Open:

```text
GET /api/v1/notes/{note_id}/history
```

Expected result: `200 OK` with a list containing the old and new note values.

### 6. Get Templates

Open:

```text
GET /api/v1/templates
```

Expected result: `200 OK` with predefined templates such as lecture notes,
meeting plan, and task list.

### 7. Register and Authorize User B

Register another user:

```json
{
  "email": "user-b@example.com",
  "password": "qwerty123"
}
```

Then authorize in Swagger as User B using the same password.

### 8. User B Tries to Read User A's Note

Open:

```text
GET /api/v1/notes/{note_id}
```

Use the note id created by User A.

Expected result:

```json
{
  "detail": "Note not found"
}
```

HTTP status: `404 Not Found`.

### 9. Delete the Note as User A

Authorize again as User A, then open:

```text
DELETE /api/v1/notes/{note_id}
```

Expected result: `204 No Content`.

## Checks

Run tests:

```bash
poetry run pytest
```

Run Ruff:

```bash
poetry run ruff check .
poetry run ruff format --check .
```

Check migrations inside Docker:

```bash
docker compose exec -T app alembic current
docker compose exec -T app alembic history
```
