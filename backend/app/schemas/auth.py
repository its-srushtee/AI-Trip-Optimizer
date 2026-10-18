"""Auth schemas."""
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserOut


class SignupRequest(BaseModel):
    """Account creation only.

    Travel preferences are deliberately NOT collected here — they are captured
    after the first sign-in via the profile completion flow (PATCH /users/me).
    """

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    access_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
