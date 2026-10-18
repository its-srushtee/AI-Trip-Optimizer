"""Destination catalogue — powers the recommendations endpoint."""
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(120))
    image_url: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)      # interest ids
    styles: Mapped[list] = mapped_column(JSON, default=list)    # Budget/Comfort/Luxury
    paces: Mapped[list] = mapped_column(JSON, default=list)     # Relaxed/Balanced/Packed
    price_label: Mapped[str] = mapped_column(String(40))
    blurb: Mapped[str] = mapped_column(Text)
