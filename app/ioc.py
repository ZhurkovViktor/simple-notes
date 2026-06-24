from collections.abc import AsyncIterator

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import FastapiProvider
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings, settings
from app.database.session import engine, session_factory
from app.repositories.notes import NoteRepository
from app.repositories.users import UserRepository
from app.services.auth import AuthService
from app.services.notes import NoteService
from app.unit_of_work import UnitOfWork


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        return settings

    @provide(scope=Scope.APP)
    def get_engine(self) -> AsyncEngine:
        return engine

    @provide(scope=Scope.APP)
    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return session_factory

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
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


def create_container() -> AsyncContainer:
    return make_async_container(AppProvider(), FastapiProvider())
