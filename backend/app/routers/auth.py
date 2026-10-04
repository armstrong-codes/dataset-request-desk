from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth import create_access_token, get_current_user, verify_password
from ..db import get_db
from ..models import User
from ..schemas import LoginRequest, Token, UserOut
router = APIRouter()

@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower().strip()))
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_access_token(user), "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
