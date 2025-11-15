from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db as _get_db
from .schemas import UserRead


def get_db() -> Session:
    yield from _get_db()


def get_current_user(db: Session = Depends(get_db)) -> UserRead:
    # Placeholder implementation. Replace with JWT verification logic later.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented yet."
    )
