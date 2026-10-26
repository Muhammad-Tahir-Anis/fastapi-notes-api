from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate

DUMMY_HASH = hash_password("dummy-password")

class EmailAlreadyRegistered(Exception):
    pass

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email.lower()))

async def create_user(db: AsyncSession, data: UserCreate) -> User:
    if await get_user_by_email(db, data.email):
        raise EmailAlreadyRegistered

    user = User(email=data.email.lower(),
                hashed_password=hash_password(data.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise EmailAlreadyRegistered
    return user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)

    hashed = user.hashed_password if user else DUMMY_HASH
    verified_password = verify_password(password, hashed)

    if user is None or not verified_password or not user.is_active:
        return None

    return user
