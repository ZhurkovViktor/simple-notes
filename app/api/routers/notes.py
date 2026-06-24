from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_session
from app.database.models import Note, User
from app.schemas.notes import NoteCreate, NoteResponse, NoteUpdate
from app.services.notes import NoteService


router = APIRouter(prefix="/api/v1/notes", tags=["Notes"])


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    service = NoteService(session)
    return await service.create(current_user.id, note_data)


@router.get("", response_model=list[NoteResponse])
async def list_notes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Note]:
    service = NoteService(session)
    return await service.get_all(current_user.id)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    service = NoteService(session)
    return await service.get_one(note_id, current_user.id)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    service = NoteService(session)
    return await service.update(note_id, current_user.id, note_data)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = NoteService(session)
    await service.delete(note_id, current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
