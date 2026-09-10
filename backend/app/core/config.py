"""Application settings loaded from environment / .env file."""
import os 

from dotenv import load_dotenv 

load_dotenv ()

class Settings :

    DATABASE_URL =os .getenv (
    "DATABASE_URL","postgresql+psycopg://tripopt:tripopt@localhost:5432/tripopt"
    )

    SECRET_KEY =os .getenv ("SECRET_KEY","dev-secret-change-me-in-production")
    ALGORITHM ="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES =int (os .getenv ("ACCESS_TOKEN_EXPIRE_MINUTES","10080"))

    CORS_ORIGINS =[
    o .strip ()
    for o in os .getenv ("CORS_ORIGINS","http://localhost:3000,http://localhost:5173").split (",")
    if o .strip ()
    ]

    GOOGLE_PLACES_API_KEY =os .getenv ("GOOGLE_PLACES_API_KEY","")
    OPENWEATHERMAP_API_KEY =os .getenv ("OPENWEATHERMAP_API_KEY","")
    AMADEUS_API_KEY =os .getenv ("AMADEUS_API_KEY","")
    AMADEUS_API_SECRET =os .getenv ("AMADEUS_API_SECRET","")
    OPENAI_API_KEY =os .getenv ("OPENAI_API_KEY","")

    UNSPLASH_ACCESS_KEY =os .getenv ("UNSPLASH_ACCESS_KEY","")
    PEXELS_API_KEY =os .getenv ("PEXELS_API_KEY","")

settings =Settings ()
