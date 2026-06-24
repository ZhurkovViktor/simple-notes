from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routers.auth import router as auth_router
from app.api.routers.notes import router as notes_router
from app.api.routers.templates import router as templates_router
from app.database.automap import prepare_automap
from app.database.session import engine
from app.ioc import create_container
from dishka.integrations.fastapi import setup_dishka


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
app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(templates_router)
setup_dishka(dishka_container, app)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
