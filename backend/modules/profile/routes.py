from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from PIL import Image
import os
import uuid
from pathlib import Path

from database import get_db, User, Profile
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from modules.auth.routes import get_current_user

router = APIRouter(prefix="/profile", tags=["Профиль"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "frontend" / "static" / "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None

@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    
    return ProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=profile.full_name,
        avatar_url=profile.avatar_url,
        phone=profile.phone,
        address=profile.address,
        bio=profile.bio
    )

@router.put("/me")
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден"
        )
    
    if profile_update.full_name is not None:
        profile.full_name = profile_update.full_name
    if profile_update.phone is not None:
        profile.phone = profile_update.phone
    if profile_update.address is not None:
        profile.address = profile_update.address
    if profile_update.bio is not None:
        profile.bio = profile_update.bio
    
    await db.commit()
    await db.refresh(profile)
    
    return {
        "success": True,
        "message": "Профиль обновлён",
        "profile": {
            "full_name": profile.full_name,
            "phone": profile.phone,
            "address": profile.address,
            "bio": profile.bio
        }
    }

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый формат файла. Разрешены: JPEG, PNG, GIF, WEBP"
        )
    
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл слишком большой. Максимальный размер: 5MB"
        )
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        image = Image.open(file.file)
        
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = background
        
        image.thumbnail((400, 400), Image.Resampling.LANCZOS)
        image.save(file_path, quality=85, optimize=True)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка обработки изображения: {str(e)}"
        )
    
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден"
        )
    
    if profile.avatar_url:
        old_file = UPLOAD_DIR / profile.avatar_url.split("/")[-1]
        if old_file.exists():
            old_file.unlink()
    
    profile.avatar_url = f"/static/uploads/avatars/{unique_filename}"
    await db.commit()
    
    return {
        "success": True,
        "message": "Аватар загружен",
        "avatar_url": profile.avatar_url
    }

@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile or not profile.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аватар не найден"
        )
    
    file_path = UPLOAD_DIR / profile.avatar_url.split("/")[-1]
    if file_path.exists():
        file_path.unlink()
    
    profile.avatar_url = None
    await db.commit()
    
    return {
        "success": True,
        "message": "Аватар удалён"
    }

@router.get("/stats")
async def get_profile_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat(),
        "is_verified": bool(current_user.is_verified)
    }
