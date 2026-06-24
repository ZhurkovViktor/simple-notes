import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.models import Note, NoteHistory, User
from app.schemas.notes import NoteCreate
from app.unit_of_work import UnitOfWork


pytestmark = pytest.mark.asyncio


async def register_user(
    client: AsyncClient,
    email: str,
    password: str = "qwerty123",
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201


async def login_user(
    client: AsyncClient,
    email: str,
    password: str = "qwerty123",
) -> str:
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_note_create_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        NoteCreate(title="", content="Content")


async def test_user_cannot_access_another_users_note(client: AsyncClient) -> None:
    await register_user(client, "user-a@example.com")
    await register_user(client, "user-b@example.com")
    user_a_token = await login_user(client, "user-a@example.com")
    user_b_token = await login_user(client, "user-b@example.com")

    create_response = await client.post(
        "/api/v1/notes",
        json={"title": "Private", "content": "Only user A"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert create_response.status_code == 201
    note_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/notes/{note_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Note not found"}


async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await register_user(client, "wrong-password@example.com")

    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "wrong-password@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


async def test_unit_of_work_rolls_back_on_error(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        user = User(
            email="rollback@example.com",
            password_hash="hash",
        )
        note = Note(
            owner=user,
            title="Before",
            content="Original",
        )
        session.add_all([user, note])
        await session.commit()
        await session.refresh(note)
        note_id = note.id

        with pytest.raises(RuntimeError):
            async with UnitOfWork(session) as uow:
                stored_note = await uow.notes.get_by_id_and_owner(note_id, user.id)
                assert stored_note is not None
                stored_note.title = "After"
                await uow.notes.add_history(
                    NoteHistory(
                        note_id=note_id,
                        old_title="Before",
                        old_content="Original",
                        new_title="After",
                        new_content="Original",
                    ),
                )
                raise RuntimeError("force rollback")

        await session.refresh(note)
        history = await session.execute(
            select(NoteHistory).where(NoteHistory.note_id == note_id),
        )

        assert note.title == "Before"
        assert history.scalars().all() == []
