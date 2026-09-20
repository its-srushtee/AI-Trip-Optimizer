"""Aggregates all API routers under one router."""
from fastapi import APIRouter 

from app .api import auth ,destinations ,itinerary ,trips ,users 

api_router =APIRouter ()
api_router .include_router (auth .router )
api_router .include_router (users .router )
api_router .include_router (trips .router )
api_router .include_router (destinations .router )
api_router .include_router (itinerary .router )
