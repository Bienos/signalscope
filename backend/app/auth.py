from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User
hashing=PasswordHash.recommended(); oauth=OAuth2PasswordBearer(tokenUrl="/api/auth/token")
def token(user:User)->str: return jwt.encode({"sub":user.email,"role":user.role,"exp":datetime.now(timezone.utc)+timedelta(hours=8)},settings().app_secret,algorithm="HS256")
def current_user(value:str=Depends(oauth),db:Session=Depends(get_db))->User:
    try: email=jwt.decode(value,settings().app_secret,algorithms=["HS256"])["sub"]
    except Exception as e: raise HTTPException(401,"Invalid or expired session") from e
    user=db.scalar(select(User).where(User.email==email,User.active==True))
    if not user: raise HTTPException(401,"Inactive user")
    return user
def admin(user:User=Depends(current_user))->User:
    if user.role!="admin": raise HTTPException(403,"Administrator role required")
    return user

