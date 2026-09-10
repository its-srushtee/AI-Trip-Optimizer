"""AI Trip Optimizer — FastAPI application entry point.

Run from the backend/ directory:

    uvicorn app.main:app --reload --port 8000

Interactive docs: http://localhost:8000/docs
"""
import os 
from contextlib import asynccontextmanager 

from fastapi import FastAPI 
from fastapi .middleware .cors import CORSMiddleware 
from fastapi .staticfiles import StaticFiles 

from app .api .router import api_router 
from app .core .config import settings 
from app .database .base import Base ,SessionLocal ,engine 

from app .models import image_cache as _image_cache 
from app .services .destination_service import seed_destinations 

Base .metadata .create_all (bind =engine )

@asynccontextmanager 
async def lifespan (app :FastAPI ):
    db =SessionLocal ()
    try :
        seed_destinations (db )
    finally :
        db .close ()
    yield 

app =FastAPI (title ="AI Trip Optimizer API",version ="0.1.0",lifespan =lifespan )

app .add_middleware (
CORSMiddleware ,
allow_origins =settings .CORS_ORIGINS ,
allow_credentials =True ,
allow_methods =["*"],
allow_headers =["*"],
)

app .include_router (api_router )

@app .get ("/health",tags =["meta"])
def health ():
    return {"status":"ok"}

_IMAGES_DIR =os .path .abspath (
os .path .join (os .path .dirname (__file__ ),"..","..","frontend","public","images")
)
if os .path .isdir (_IMAGES_DIR ):
    app .mount ("/images",StaticFiles (directory =_IMAGES_DIR ),name ="images")
