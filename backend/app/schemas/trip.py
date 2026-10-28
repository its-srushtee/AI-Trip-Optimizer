"""Trip schemas."""
from datetime import date, datetime

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TripCreate(BaseModel):
    destination: str = Field(min_length=1, max_length=120)
    start_date: date
    end_date: date
    budget: int = Field(default=1000, ge=1)
    travelers: int = Field(default=1, ge=1, le=15)
    interests: list[str] = Field(default_factory=list)
    currency: str | None = None
    preferences: dict = Field(default_factory=dict)


class TripUpdate(BaseModel):
    destination: str | None = Field(default=None, min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    budget: int | None = Field(default=None, ge=1)
    travelers: int | None = Field(default=None, ge=1, le=15)
    interests: list[str] | None = None
    status: str | None = None
    currency: str | None = None
    preferences: dict | None = None


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    destination: str
    start_date: date
    end_date: date
    budget: int
    travelers: int
    interests: list
    status: str
    currency: str = "USD"
    preferences: dict = Field(default_factory=dict)
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def resolve_currency(cls, data: Any) -> Any:
        if isinstance(data, dict):
            curr = data.get("currency") or (data.get("preferences") or {}).get("currency") or "USD"
            data["currency"] = str(curr).upper()
        elif hasattr(data, "currency"):
            curr = getattr(data, "currency", None) or getattr(data, "preferences", {}).get("currency") or "USD"
            if isinstance(data, dict):
                data["currency"] = str(curr).upper()
        return data


