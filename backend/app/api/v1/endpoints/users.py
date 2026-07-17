import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession):
    return db.query(User).order_by(User.full_name).all()


@router.post("", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: DbSession):
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(status_code=409, detail="A user with this email already exists")
    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: DbSession):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
