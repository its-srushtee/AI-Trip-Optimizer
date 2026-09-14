"""Itinerary schemas (POST /trips/optimize)."""
from datetime import date 

from pydantic import BaseModel ,Field 

class OptimizeRequest (BaseModel ):
    destination :str =Field (min_length =1 ,max_length =120 )
    start_date :date 
    end_date :date 
    budget :int =Field (default =1000 ,ge =0 )
    travelers :int =Field (default =1 ,ge =1 ,le =20 )
    interests :list [str ]=Field (default_factory =list )

class DayOut (BaseModel ):
    day :int 
    date :date 
    theme :str 
    morning :str 
    afternoon :str 
    evening :str 
    stay :str 
    estimate_usd :int 

class BudgetBreakdown (BaseModel ):
    flights :int 
    stay :int 
    food :int 
    activities :int 
    total :int 

class ItineraryDates (BaseModel ):
    start :date 
    end :date 
    nights :int 

class ItineraryOut (BaseModel ):
    destination :str 
    dates :ItineraryDates 
    travelers :int 
    interests :list [str ]
    budget :int 
    budget_breakdown :BudgetBreakdown 
    summary :str 
    days :list [DayOut ]

class OptimizeResponse (BaseModel ):
    itinerary :ItineraryOut 
