"""POST /auth/signup, POST /auth/login"""
from fastapi import APIRouter ,Depends 
from sqlalchemy .orm import Session 

from app .core .deps import get_db 
from app .schemas .auth import (
GoogleAuthRequest ,
LoginRequest ,
SignupRequest ,
TokenResponse ,
)

from app .services .auth_service import login as login_service 
from app .services .auth_service import signup as signup_service 
from app .services .auth_service import google_login as google_login_service 

router =APIRouter (prefix ="/auth",tags =["auth"])

@router .post ("/signup",response_model =TokenResponse ,status_code =201 )
def signup (body :SignupRequest ,db :Session =Depends (get_db )):
    return signup_service (db ,body )

@router .post ("/login",response_model =TokenResponse )
def login (body :LoginRequest ,db :Session =Depends (get_db )):
    return login_service (db ,body )

@router .post ("/google",response_model =TokenResponse )
def google_auth (
body :GoogleAuthRequest ,
db :Session =Depends (get_db ),
):
    return google_login_service (db ,body )