import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import auth, notes
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.db.session import get_db

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Notes API")
register_exception_handlers(app)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check failed")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database unavailable")
    return {"status": "ok"}
