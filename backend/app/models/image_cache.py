"""Resolved destination photos.

We cache the *URL and its credit*, never the bytes. One row per search term,
so a destination is looked up against the provider once and then served from
the database forever after. This is what stops the app making an outbound
HTTP call on every dashboard render.
"""
from datetime import datetime 

from sqlalchemy import DateTime ,String ,Text ,func 
from sqlalchemy .orm import Mapped ,mapped_column 

from app .database .base import Base 

class ImageCache (Base ):
    __tablename__ ="image_cache"

    query :Mapped [str ]=mapped_column (String (160 ),primary_key =True )

    url :Mapped [str ]=mapped_column (Text )
    thumb_url :Mapped [str ]=mapped_column (Text ,default ="")
    credit :Mapped [str ]=mapped_column (String (200 ),default ="")
    credit_url :Mapped [str ]=mapped_column (Text ,default ="")
    license :Mapped [str ]=mapped_column (String (80 ),default ="")
    license_url :Mapped [str ]=mapped_column (Text ,default ="")
    source_name :Mapped [str ]=mapped_column (String (60 ),default ="")
    source_url :Mapped [str ]=mapped_column (Text ,default ="")
    title :Mapped [str ]=mapped_column (String (300 ),default ="")
    provider :Mapped [str ]=mapped_column (String (40 ),default ="")

    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),server_default =func .now ()
    )
