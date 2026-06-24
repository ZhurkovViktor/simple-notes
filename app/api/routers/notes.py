from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_current_user
from app.database.models import Note, User
from app.schemas.notes import NoteCreate, NoteResponse, NoteUpdate
from app.services.notes import NoteService


router = APIRouter(tags=["Notes"])


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_note(
    note_data: NoteCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: FromDishka[NoteService],
) -> Note:
    return await service.create(current_user.id, note_data)


@router.get("", response_model=list[NoteResponse])
@inject
async def list_notes(
    current_user: Annotated[User, Depends(get_current_user)],
    service: FromDishka[NoteService],
) -> list[Note]:
    return await service.get_all(current_user.id)


@router.get("/{note_id}", response_model=NoteResponse)
@inject
async def get_note(
    note_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: FromDishka[NoteService],
) -> Note:
    return await service.get_one(note_id, current_user.id)


@router.patch("/{note_id}", response_model=NoteResponse)
@inject
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: FromDishka[NoteService],
) -> Note:
    return await service.update(note_id, current_user.id, note_data)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_note(
    note_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: FromDishka[NoteService],
) -> Response:
    await service.delete(note_id, current_user.id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
