from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routers.auth import router as auth_router


app = FastAPI(
    title="Personal Notes API",
    version="1.0.0",
    description="API для управления личными заметками",
)
app.include_router(auth_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
