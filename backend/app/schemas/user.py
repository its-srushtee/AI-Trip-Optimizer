"""User schemas."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

# A profile counts as complete once these preference keys hold a real value.
# `interests` must be a non-empty list; the rest must be non-empty strings.
REQUIRED_PREFERENCE_KEYS = ("style", "interests", "pace", "accommodation", "food")


def is_profile_complete(preferences: dict | None) -> bool:
    """True when every required travel preference has been provided."""
    prefs = preferences or {}
    for key in REQUIRED_PREFERENCE_KEYS:
        value = prefs.get(key)
        if key == "interests":
            if not isinstance(value, list) or len(value) == 0:
                return False
        elif not isinstance(value, str) or not value.strip():
            return False
    return True


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    preferences: dict = Field(default_factory=dict)

    @computed_field  # exposed to the client so it never has to infer this
    @property
    def profile_complete(self) -> bool:
        return is_profile_complete(self.preferences)


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    preferences: dict | None = None
