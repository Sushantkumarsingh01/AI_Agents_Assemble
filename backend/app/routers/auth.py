from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import User
from ..schemas import SignupRequest, LoginRequest, TokenResponse
from ..auth import hash_password, verify_password, create_access_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
	email = decode_token(token)
	if not email:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
	result = await db.execute(select(User).where(User.email == email))
	user = result.scalar_one_or_none()
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
	return user

@router.post("/signup", response_model=TokenResponse)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
	# Ensure email unique
	existing = await db.execute(select(User).where(User.email == payload.email))
	if existing.scalar_one_or_none() is not None:
		raise HTTPException(status_code=400, detail="Email already registered")
	user = User(email=payload.email, password_hash=hash_password(payload.password))
	db.add(user)
	await db.commit()
	access_token = create_access_token(subject=user.email)
	return TokenResponse(access_token=access_token)

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(User).where(User.email == payload.email))
	user = result.scalar_one_or_none()
	if not user or not verify_password(payload.password, user.password_hash):
		raise HTTPException(status_code=400, detail="Invalid email or password")
	access_token = create_access_token(subject=user.email)
	return TokenResponse(access_token=access_token) 