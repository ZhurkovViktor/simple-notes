from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routers.auth import auth_router, users_router
from app.api.routers.notes import router as notes_router
from app.api.routers.templates import router as templates_router
from app.core.exceptions import (
    InvalidCredentialsError,
    NoteNotFoundError,
    UserAlreadyExistsError,
)
from app.database.automap import prepare_automap
from app.database.session import engine
from app.ioc import create_container


dishka_container = create_container()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await prepare_automap(engine)
    try:
        yield
    finally:
        await dishka_container.close()


app = FastAPI(
    title="Personal Notes API",
    version="1.0.0",
    description="API для управления личными заметками",
    lifespan=lifespan,
)
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(users_router, prefix="/api/v1/users")
app.include_router(notes_router, prefix="/api/v1/notes")
app.include_router(templates_router, prefix="/api/v1/templates")
setup_dishka(dishka_container, app)


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_handler(
    _request: Request,
    _exc: UserAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "User with this email already exists"},
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    _request: Request,
    _exc: InvalidCredentialsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Incorrect email or password"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(NoteNotFoundError)
async def note_not_found_handler(
    _request: Request,
    _exc: NoteNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Note not found"},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(
    _request: Request,
    _exc: SQLAlchemyError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
