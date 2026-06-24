from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path

import pytest_asyncio
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import FastapiProvider
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.dependencies import get_session
from app.core.config import Settings, settings
from app.database.base import Base
from app.main import app
from app.repositories.notes import NoteRepository
from app.repositories.users import UserRepository
from app.services.auth import AuthService
from app.services.notes import NoteService
from app.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class TestDatabase:
    engine: AsyncEngine
    session_factory: async_sessionmaker[AsyncSession]


class TestProvider(Provider):
    def __init__(
        self,
        engine: AsyncEngine,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__()
        self.engine = engine
        self.session_factory = session_factory

    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        return settings

    @provide(scope=Scope.APP)
    def get_engine(self) -> AsyncEngine:
        return self.engine

    @provide(scope=Scope.APP)
    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self.session_factory

    @provide(scope=Scope.REQUEST)
    async def get_request_session(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def get_user_repository(self, session: AsyncSession) -> UserRepository:
        return UserRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_note_repository(self, session: AsyncSession) -> NoteRepository:
        return NoteRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_unit_of_work(self, session: AsyncSession) -> UnitOfWork:
        return UnitOfWork(session)

    @provide(scope=Scope.REQUEST)
    def get_auth_service(self, session: AsyncSession) -> AuthService:
        return AuthService(session)

    @provide(scope=Scope.REQUEST)
    def get_note_service(self, session: AsyncSession) -> NoteService:
        return NoteService(session)


@pytest_asyncio.fixture
async def test_database(tmp_path: Path) -> AsyncGenerator[TestDatabase, None]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield TestDatabase(engine=engine, session_factory=session_factory)

    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(
    test_database: TestDatabase,
) -> async_sessionmaker[AsyncSession]:
    return test_database.session_factory


@pytest_asyncio.fixture
async def client(
    test_database: TestDatabase,
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_database.session_factory() as session:
            yield session

    test_container = make_async_container(
        TestProvider(test_database.engine, test_database.session_factory),
        FastapiProvider(),
    )
    original_container = app.state.dishka_container

    app.dependency_overrides[get_session] = override_get_session
    app.state.dishka_container = test_container

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    app.state.dishka_container = original_container
    await test_container.close()
