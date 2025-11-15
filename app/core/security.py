from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any, Dict, Optional

import bcrypt
from jose import jwt

from ..config import settings


PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def _prepare_password(password: str) -> str:
    """Pre-hash the password to avoid bcrypt's 72-byte limit."""

    return sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    prepared = _prepare_password(plain_password).encode("utf-8")
    return bcrypt.checkpw(prepared, hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    prepared = _prepare_password(password).encode("utf-8")
    return bcrypt.hashpw(prepared, bcrypt.gensalt()).decode("utf-8")
