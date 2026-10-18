"""GET /users/me, PATCH /users/me"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import ProfileUpdate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_unset=True)

    if "email" in data and data["email"] is not None:
        email = data["email"].lower()
        exists = db.query(User).filter(User.email == email, User.id != user.id).first()
        if exists:
            raise HTTPException(status_code=409, detail="Email already registered")
        user.email = email

    if "name" in data and data["name"] is not None:
        user.name = data["name"].strip()

    if "preferences" in data and data["preferences"] is not None:
        user.preferences = data["preferences"]

    db.commit()
    db.refresh(user)
    return user
