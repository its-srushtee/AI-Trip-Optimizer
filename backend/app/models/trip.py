"""Trip model."""
from datetime import date ,datetime 

from sqlalchemy import Date ,DateTime ,ForeignKey ,Integer ,JSON ,String ,func 
from sqlalchemy .orm import Mapped ,mapped_column ,relationship 

from app .database .base import Base 

class Trip (Base ):
    __tablename__ ="trips"

    id :Mapped [int ]=mapped_column (primary_key =True )
    user_id :Mapped [int ]=mapped_column (ForeignKey ("users.id",ondelete ="CASCADE"),index =True )
    destination :Mapped [str ]=mapped_column (String (120 ))
    start_date :Mapped [date ]=mapped_column (Date )
    end_date :Mapped [date ]=mapped_column (Date )
    budget :Mapped [int ]=mapped_column (Integer ,default =1000 )
    travelers :Mapped [int ]=mapped_column (Integer ,default =1 )
    interests :Mapped [list ]=mapped_column (JSON ,default =list )
    status :Mapped [str ]=mapped_column (String (40 ),default ="Planning")
    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),server_default =func .now ()
    )

    user :Mapped ["User"]=relationship (back_populates ="trips")
