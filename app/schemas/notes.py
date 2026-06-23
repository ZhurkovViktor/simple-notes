from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class NoteHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    old_title: str
    old_content: str
    new_title: str
    new_content: str
    changed_at: datetime
