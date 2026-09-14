"""User model."""
from datetime import datetime 

from sqlalchemy import DateTime ,JSON ,String ,func 
from sqlalchemy .orm import Mapped ,mapped_column ,relationship 

from app .database .base import Base 

class User (Base ):
    __tablename__ ="users"

    id :Mapped [int ]=mapped_column (primary_key =True )
    name :Mapped [str ]=mapped_column (String (120 ))
    email :Mapped [str ]=mapped_column (String (255 ),unique =True ,index =True )
    hashed_password :Mapped [str ]=mapped_column (String (255 ))

    preferences :Mapped [dict ]=mapped_column (JSON ,default =dict )
    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),server_default =func .now ()
    )

    trips :Mapped [list ["Trip"]]=relationship (
    back_populates ="user",cascade ="all, delete-orphan"
    )
