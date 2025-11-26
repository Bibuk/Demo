from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
import re
import random
import httpx

from .security import get_password_hash, verify_password, create_access_token, decode_access_token
from .email_service import send_verification_code, send_welcome_email
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings
from database import get_db, User, Profile

router = APIRouter(prefix="/auth", tags=["Авторизация"])
security = HTTPBearer()

verification_codes = {}
oauth_states = {}

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Имя пользователя должно содержать минимум 3 символа')
        if len(v) > 50:
            raise ValueError('Имя пользователя должно содержать максимум 50 символов')
        if not re.match(r'^[a-zA-Zа-яА-Я0-9_-]+$', v):
            raise ValueError('Имя пользователя может содержать только буквы, цифры, дефис и подчеркивание')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not re.search(r'[a-z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        if not re.search(r'\d', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Пароль должен содержать хотя бы один специальный символ')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyCode(BaseModel):
    email: EmailStr
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))

def generate_oauth_state() -> str:
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    return user

@router.post("/register")
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
    
    code = generate_verification_code()
    verification_codes[user.email] = {
        "code": code,
        "username": user.username,
        "password": user.password,
        "created_at": datetime.utcnow(),
        "attempts": 0
    }
    
    await send_verification_code(user.email, code)
    
    return {
        "success": True,
        "message": "Код верификации отправлен на email",
        "email": user.email
    }

@router.post("/verify")
async def verify_email(verify: VerifyCode, db: AsyncSession = Depends(get_db)):
    if verify.email not in verification_codes:
        raise HTTPException(status_code=400, detail="Код верификации не найден")
    
    stored = verification_codes[verify.email]
    
    if datetime.utcnow() - stored["created_at"] > timedelta(minutes=10):
        del verification_codes[verify.email]
        raise HTTPException(status_code=400, detail="Код верификации истёк")
    
    if stored["attempts"] >= 5:
        del verification_codes[verify.email]
        raise HTTPException(status_code=400, detail="Превышено количество попыток")
    
    if stored["code"] != verify.code:
        verification_codes[verify.email]["attempts"] += 1
        raise HTTPException(status_code=400, detail="Неверный код верификации")
    
    hashed_password = get_password_hash(stored["password"])
    new_user = User(
        email=verify.email,
        username=stored["username"],
        hashed_password=hashed_password,
        is_verified=1
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    new_profile = Profile(user_id=new_user.id)
    db.add(new_profile)
    await db.commit()
    
    del verification_codes[verify.email]
    await send_welcome_email(verify.email, stored["username"])
    
    access_token = create_access_token(data={"sub": new_user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": new_user.id,
            "email": new_user.email,
            "username": new_user.username
        }
    )

@router.post("/login", response_model=Token)
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтверждён"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    )

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_verified": bool(current_user.is_verified),
        "created_at": current_user.created_at.isoformat()
    }

@router.get("/vk")
async def auth_vk():
    """Авторизация через ВКонтакте"""
    if not settings.VK_CLIENT_ID or not settings.VK_CLIENT_SECRET:
        return {"success": False, "error": "VK OAuth не настроен"}
    
    state = generate_oauth_state()
    oauth_states[state] = {"provider": "vk", "created_at": datetime.utcnow()}
    
    redirect_uri = f"{settings.APP_URL}/auth/vk/callback"
    auth_url = f"https://oauth.vk.com/authorize?client_id={settings.VK_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email&response_type=code&state={state}"
    
    return RedirectResponse(url=auth_url)

@router.get("/vk/callback")
async def auth_vk_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Невалидный state")
    
    redirect_uri = f"{settings.APP_URL}/auth/vk/callback"
    
    async with httpx.AsyncClient() as client:
        token_response = await client.get(
            "https://oauth.vk.com/access_token",
            params={
                "client_id": settings.VK_CLIENT_ID,
                "client_secret": settings.VK_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "code": code
            }
        )
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error_description"])
        
        access_token = token_data["access_token"]
        email = token_data.get("email")
        vk_user_id = token_data["user_id"]
        
        if not email:
            raise HTTPException(status_code=400, detail="Email не предоставлен VK")
        
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            username = f"vk_{vk_user_id}"
            user = User(
                email=email,
                username=username,
                hashed_password=get_password_hash(f"vk_oauth_{vk_user_id}"),
                is_verified=1
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            profile = Profile(user_id=user.id)
            db.add(profile)
            await db.commit()
        
        jwt_token = create_access_token(data={"sub": user.email})
        
        del oauth_states[state]
        
        return RedirectResponse(url=f"/profile?token={jwt_token}")

@router.get("/google")
async def auth_google():
    """Авторизация через Google"""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return {"success": False, "error": "Google OAuth не настроен"}
    
    state = generate_oauth_state()
    oauth_states[state] = {"provider": "google", "created_at": datetime.utcnow()}
    
    redirect_uri = f"{settings.APP_URL}/api/auth/google/callback"
    print(f"\n[GOOGLE OAUTH DEBUG]")
    print(f"Client ID: {settings.GOOGLE_CLIENT_ID}")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Full Auth URL: https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email%20profile&response_type=code&state={state}\n")
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email%20profile&response_type=code&state={state}"
    
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def auth_google_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Невалидный state")
    
    redirect_uri = f"{settings.APP_URL}/api/auth/google/callback"
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
                "grant_type": "authorization_code"
            }
        )
        token_data = token_response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error_description"])
        
        access_token = token_data["access_token"]
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_data = user_response.json()
        
        email = user_data["email"]
        google_id = user_data["id"]
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            username = f"google_{google_id}"
            user = User(
                email=email,
                username=username,
                hashed_password=get_password_hash(f"google_oauth_{google_id}"),
                is_verified=1
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            profile = Profile(user_id=user.id)
            db.add(profile)
            await db.commit()
        jwt_token = create_access_token(data={"sub": user.email})
        
        del oauth_states[state]
        
        return RedirectResponse(url=f"/profile?token={jwt_token}")