from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Note, NoteHistory


class NoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, note: Note) -> Note:
        self.session.add(note)
        await self.session.flush()
        await self.session.refresh(note)
        return note

    async def get_all_by_owner(self, owner_id: int) -> list[Note]:
        result = await self.session.execute(
            select(Note).where(Note.owner_id == owner_id).order_by(Note.id),
        )
        return list(result.scalars().all())

    async def get_by_id_and_owner(self, note_id: int, owner_id: int) -> Note | None:
        result = await self.session.execute(
            select(Note).where(
                Note.id == note_id,
                Note.owner_id == owner_id,
            ),
        )
        return result.scalar_one_or_none()

    async def delete(self, note_id: int, owner_id: int) -> bool:
        await self.session.execute(
            delete(NoteHistory).where(NoteHistory.note_id == note_id),
        )
        result = await self.session.execute(
            delete(Note).where(
                Note.id == note_id,
                Note.owner_id == owner_id,
            ),
        )
        return result.rowcount > 0

    async def add_history(self, history: NoteHistory) -> NoteHistory:
        self.session.add(history)
        await self.session.flush()
        await self.session.refresh(history)
        return history

    async def get_history(self, note_id: int) -> list[NoteHistory]:
        result = await self.session.execute(
            select(NoteHistory)
            .where(NoteHistory.note_id == note_id)
            .order_by(NoteHistory.changed_at),
        )
        return list(result.scalars().all())
