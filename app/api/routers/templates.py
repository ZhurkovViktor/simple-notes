from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.database.automap import get_system_note_template_model
from app.schemas.templates import TemplateResponse


router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    session: AsyncSession = Depends(get_session),
) -> list[Any]:
    template_model = get_system_note_template_model()
    result = await session.execute(select(template_model).order_by(template_model.id))

    return list(result.scalars().all())
