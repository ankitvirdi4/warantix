from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.security import create_access_token, get_password_hash, verify_password
from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import AuthResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = data.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "user_id": user.id}, expires_delta=timedelta(hours=1))
    return AuthResponse(access_token=token, user=user)


@router.post("/signup", response_model=AuthResponse)
def signup(data: UserCreate, db: Session = Depends(get_db)) -> AuthResponse:
    email = data.email.lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    password_hash = get_password_hash(data.password)
    user = User(
        email=email,
        name=data.name or "",
        password_hash=password_hash,
        role="engineer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "user_id": user.id}, expires_delta=timedelta(hours=1))
    return AuthResponse(access_token=token, user=user)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    return current_user
