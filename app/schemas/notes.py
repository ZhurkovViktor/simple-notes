from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1)
    content: str


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
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
