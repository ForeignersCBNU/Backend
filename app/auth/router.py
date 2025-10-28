from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import User
from .security import hash_password, verify_password, create_access_token
router = APIRouter(prefix="/auth", tags=["auth"])
class RegisterIn(BaseModel):
    email: EmailStr; name: str; password: str
class TokenOut(BaseModel):
    access_token: str; token_type: str = "bearer"
@router.post("/register", response_model=TokenOut)
async def register(body: RegisterIn):
    async with SessionLocal() as s:
        exists = (await s.execute(select(User).where(User.email==body.email))).scalar_one_or_none()
        if exists: raise HTTPException(400, "Email already exists")
        u = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
        s.add(u); await s.commit()
        return TokenOut(access_token=create_access_token(u.id))
class LoginIn(BaseModel):
    email: EmailStr; password: str
@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn):
    async with SessionLocal() as s:
        u = (await s.execute(select(User).where(User.email==body.email))).scalar_one_or_none()
        if not u or not verify_password(body.password, u.password_hash):
            raise HTTPException(401, "Invalid credentials")
        return TokenOut(access_token=create_access_token(u.id))
