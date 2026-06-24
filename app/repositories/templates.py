from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self, template_model: type[Any]) -> list[Any]:
        result = await self.session.execute(
            select(template_model).order_by(template_model.id),
        )
        return list(result.scalars().all())
