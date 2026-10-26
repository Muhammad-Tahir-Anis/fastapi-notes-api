from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


async def list_notes(
    db: AsyncSession, owner_id: int, limit: int, offset: int
) -> list[Note]:
    result = await db.scalars(
        select(Note)
        .where(Note.owner_id == owner_id)
        .order_by(Note.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result)


async def get_note(db: AsyncSession, owner_id: int, note_id: int) -> Note | None:
    return await db.scalar(
        select(Note).where(Note.id == note_id, Note.owner_id == owner_id)
    )


async def create_note(db: AsyncSession, owner_id: int, data: NoteCreate) -> Note:
    note = Note(title=data.title, body=data.body, owner_id=owner_id)
    db.add(note)
    await db.commit()
    return note


async def update_note(db: AsyncSession, note: Note, data: NoteUpdate) -> Note:
    note.title = data.title
    note.body = data.body
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(db: AsyncSession, note: Note) -> None:
    await db.delete(note)
    await db.commit()
