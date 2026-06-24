from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.schemas.templates import TemplateResponse
from app.services.templates import TemplateService


router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    session: AsyncSession = Depends(get_session),
) -> list[Any]:
    service = TemplateService(session)
    return await service.get_all()
