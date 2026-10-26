"""Destination and attraction information cache table.

Caches geocoded coordinates, country metadata, and verified attraction lists
per destination so external API queries (Geoapify, SerpApi) are performed once
and then served instantly from the database.
"""
from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DestinationInfoCache(Base):
    __tablename__ = "destination_info_cache"

    query_key: Mapped[str] = mapped_column(String(180), primary_key=True)
    destination_name: Mapped[str] = mapped_column(String(160), nullable=False)
    country: Mapped[str] = mapped_column(String(120), default="")
    formatted_address: Mapped[str] = mapped_column(String(255), default="")
    coordinates: Mapped[dict] = mapped_column(JSON, default=dict)
    attractions: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

