from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_session
from app.database.models import Note, User
from app.schemas.notes import NoteCreate, NoteResponse, NoteUpdate


router = APIRouter(prefix="/api/v1/notes", tags=["Notes"])


async def get_user_note(
    note_id: int,
    current_user: User,
    session: AsyncSession,
) -> Note | None:
    result = await session.execute(
        select(Note).where(
            Note.id == note_id,
            Note.owner_id == current_user.id,
        ),
    )
    return result.scalar_one_or_none()


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    note = Note(
        owner_id=current_user.id,
        title=note_data.title,
        content=note_data.content,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    return note


@router.get("", response_model=list[NoteResponse])
async def list_notes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Note]:
    result = await session.execute(
        select(Note).where(Note.owner_id == current_user.id).order_by(Note.id),
    )
    return list(result.scalars().all())


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    note = await get_user_note(note_id, current_user, session)

    if note is None:
        raise_note_not_found()

    return note


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Note:
    note = await get_user_note(note_id, current_user, session)

    if note is None:
        raise_note_not_found()

    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await session.commit()
    await session.refresh(note)

    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    result = await session.execute(
        delete(Note).where(
            Note.id == note_id,
            Note.owner_id == current_user.id,
        ),
    )

    if result.rowcount == 0:
        raise_note_not_found()

    await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def raise_note_not_found() -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Note not found",
    )
