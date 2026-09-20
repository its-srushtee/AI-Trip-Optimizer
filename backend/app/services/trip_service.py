"""Trip CRUD business logic."""
from fastapi import HTTPException 
from sqlalchemy .orm import Session 

from app .models .trip import Trip 
from app .schemas .trip import TripCreate 

def list_trips (db :Session ,user_id :int )->list [Trip ]:
    return (
    db .query (Trip )
    .filter (Trip .user_id ==user_id )
    .order_by (Trip .created_at .desc ())
    .all ()
    )

def create_trip (db :Session ,user_id :int ,body :TripCreate )->Trip :
    if body .end_date <body .start_date :
        raise HTTPException (status_code =400 ,detail ="End date must be after start date")

    trip =Trip (user_id =user_id ,**body .model_dump ())
    db .add (trip )
    db .commit ()
    db .refresh (trip )
    return trip 

def delete_trip (db :Session ,user_id :int ,trip_id :int )->None :
    trip =db .get (Trip ,trip_id )
    if not trip or trip .user_id !=user_id :
        raise HTTPException (status_code =404 ,detail ="Trip not found")
    db .delete (trip )
    db .commit ()
