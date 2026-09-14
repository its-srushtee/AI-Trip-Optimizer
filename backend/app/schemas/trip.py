"""Trip schemas."""
from datetime import date ,datetime 

from pydantic import BaseModel ,ConfigDict ,Field 

class TripCreate (BaseModel ):
    destination :str =Field (min_length =1 ,max_length =120 )
    start_date :date 
    end_date :date 
    budget :int =Field (default =1000 ,ge =0 )
    travelers :int =Field (default =1 ,ge =1 ,le =20 )
    interests :list [str ]=Field (default_factory =list )

class TripOut (BaseModel ):
    model_config =ConfigDict (from_attributes =True )
    id :int 
    destination :str 
    start_date :date 
    end_date :date 
    budget :int 
    travelers :int 
    interests :list 
    status :str 
    created_at :datetime 
