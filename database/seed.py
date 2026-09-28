"""Standalone seeder — inserts the destination catalogue.

Run from the repo root (requires backend deps installed):

    python database/seed.py

Uses the same DATABASE_URL as the backend (backend/.env).
"""
import os 
import sys 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..","backend"))

from app .database .base import SessionLocal 
from app .services .destination_service import seed_destinations 

if __name__ =="__main__":
    db =SessionLocal ()
    try :
        created =seed_destinations (db )
        print (f"Seeded {created } destinations."if created else "Destinations already present.")
    finally :
        db .close ()
