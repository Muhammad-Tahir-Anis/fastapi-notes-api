from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate
from app.services import note as note_service

router = APIRouter(prefix="/notes", tags=["notes"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_owned_note(note_id: int, user: CurrentUser, db: DbSession) -> Note:
    note = await note_service.get_note(db, user.id, note_id)
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found")
    return note


OwnedNote = Annotated[Note, Depends(get_owned_note)]


@router.get("", response_model=list[NoteRead])
async def list_notes(
    user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await note_service.list_notes(db, user.id, limit, offset)


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(data: NoteCreate, user: CurrentUser, db: DbSession):
    return await note_service.create_note(db, user.id, data)


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(note: OwnedNote):
    return note


@router.put("/{note_id}", response_model=NoteRead)
async def update_note(data: NoteUpdate, note: OwnedNote, db: DbSession):
    return await note_service.update_note(db, note, data)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note: OwnedNote, db: DbSession):
    await note_service.delete_note(db, note)