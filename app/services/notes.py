from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Note, NoteHistory
from app.repositories.notes import NoteRepository
from app.schemas.notes import NoteCreate, NoteUpdate
from app.unit_of_work import UnitOfWork


class NoteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.notes = NoteRepository(session)

    async def create(self, owner_id: int, note_data: NoteCreate) -> Note:
        async with UnitOfWork(self.session) as uow:
            note = Note(
                owner_id=owner_id,
                title=note_data.title,
                content=note_data.content,
            )
            note = await uow.notes.add(note)
            await uow.commit()

            return note

    async def get_all(self, owner_id: int) -> list[Note]:
        return await self.notes.get_all_by_owner(owner_id)

    async def get_one(self, note_id: int, owner_id: int) -> Note:
        note = await self.notes.get_by_id_and_owner(note_id, owner_id)

        if note is None:
            raise_note_not_found()

        return note

    async def update(self, note_id: int, owner_id: int, note_data: NoteUpdate) -> Note:
        async with UnitOfWork(self.session) as uow:
            note = await uow.notes.get_by_id_and_owner(note_id, owner_id)

            if note is None:
                raise_note_not_found()

            old_title = note.title
            old_content = note.content
            update_data = note_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(note, field, value)

            history = NoteHistory(
                note_id=note.id,
                old_title=old_title,
                old_content=old_content,
                new_title=note.title,
                new_content=note.content,
            )
            await uow.notes.add_history(history)
            await uow.commit()
            await self.session.refresh(note)

            return note

    async def delete(self, note_id: int, owner_id: int) -> None:
        async with UnitOfWork(self.session) as uow:
            deleted = await uow.notes.delete(note_id, owner_id)

            if not deleted:
                raise_note_not_found()

            await uow.commit()

    async def add_history(self, history: NoteHistory) -> NoteHistory:
        return await self.notes.add_history(history)

    async def get_history(self, note_id: int, owner_id: int) -> list[NoteHistory]:
        note = await self.get_one(note_id, owner_id)
        return await self.notes.get_history(note.id)


def raise_note_not_found() -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Note not found",
    )
