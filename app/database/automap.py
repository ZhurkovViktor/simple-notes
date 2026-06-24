from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.automap import automap_base


AutomapBase = automap_base()
_is_prepared = False


async def prepare_automap(engine: AsyncEngine) -> None:
    global _is_prepared

    if _is_prepared:
        return

    async with engine.connect() as connection:
        await connection.run_sync(
            lambda sync_connection: AutomapBase.prepare(
                autoload_with=sync_connection,
            ),
        )

    _is_prepared = True


def get_system_note_template_model() -> type[Any]:
    return AutomapBase.classes.system_note_templates
