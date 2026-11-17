"""Auth business logic: signup / login -> { access_token, user }."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest

import os

from supabase import create_client

from app.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    SignupRequest,
)


def _token_response(user: User) -> dict:
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": user,
    }

def google_login(db: Session, body: GoogleAuthRequest) -> dict:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase server configuration is missing",
        )

    try:
        supabase = create_client(supabase_url, supabase_key)
        response = supabase.auth.get_user(body.access_token)
        google_user = response.user
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google authentication",
        )

    if not google_user or not google_user.email:
        raise HTTPException(
            status_code=400,
            detail="Google account does not have an email address",
        )

    email = google_user.email.lower()

    user = db.query(User).filter(User.email == email).first()

    if not user:
        metadata = google_user.user_metadata or {}
        name = (
            metadata.get("full_name")
            or metadata.get("name")
            or email.split("@")[0]
        )

        user = User(
            name=name[:120],
            email=email,
            # Google handles authentication, so this is not used for
            # Google login.
            hashed_password=hash_password(os.urandom(32).hex()),
            preferences={},
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    return _token_response(user)

def signup(db: Session, body: SignupRequest) -> dict:
    email = body.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Travel preferences can be captured at signup or updated later via PATCH /users/me
    user = User(
        name=body.name.strip(),
        email=email,
        hashed_password=hash_password(body.password),
        preferences=body.preferences or {},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_response(user)


def login(db: Session, body: LoginRequest) -> dict:
    email = body.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _token_response(user)
