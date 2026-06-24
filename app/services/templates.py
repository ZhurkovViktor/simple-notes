from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.automap import get_system_note_template_model
from app.repositories.templates import TemplateRepository


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self.templates = TemplateRepository(session)

    async def get_all(self) -> list[Any]:
        template_model = get_system_note_template_model()
        return await self.templates.get_all(template_model)
