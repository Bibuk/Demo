from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime
import hashlib
import mimetypes

router = APIRouter(prefix="/media", tags=["Медиа"])

UPLOAD_DIR = Path("frontend/static/uploads")
ALLOWED_EXTENSIONS = {
    'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'},
    'video': {'.mp4', '.avi', '.mov', '.mkv', '.webm'},
    'audio': {'.mp3', '.wav', '.ogg', '.m4a', '.flac'},
    'document': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'},
    'archive': {'.zip', '.rar', '.7z', '.tar', '.gz'}
}
MAX_FILE_SIZE = 50 * 1024 * 1024

for subdir in ['images', 'videos', 'audio', 'documents', 'archives', 'avatars']:
    (UPLOAD_DIR / subdir).mkdir(parents=True, exist_ok=True)

class GalleryImage(BaseModel):
    id: int
    url: str
    title: str
    description: Optional[str] = None

class VideoData(BaseModel):
    id: int
    title: str
    url: str
    thumbnail: str
    duration: str

class Testimonial(BaseModel):
    id: int
    author: str
    avatar: str
    text: str
    rating: int
    date: str

gallery_db = [
    {"id": 1, "url": "/static/img/gallery/1.jpg", "title": "Изображение 1", "description": "Описание изображения 1"},
    {"id": 2, "url": "/static/img/gallery/2.jpg", "title": "Изображение 2", "description": "Описание изображения 2"},
    {"id": 3, "url": "/static/img/gallery/3.jpg", "title": "Изображение 3", "description": "Описание изображения 3"},
    {"id": 4, "url": "/static/img/gallery/4.jpg", "title": "Изображение 4", "description": "Описание изображения 4"},
    {"id": 5, "url": "/static/img/gallery/5.jpg", "title": "Изображение 5", "description": "Описание изображения 5"},
    {"id": 6, "url": "/static/img/gallery/6.jpg", "title": "Изображение 6", "description": "Описание изображения 6"},
]

videos_db = [
    {"id": 1, "title": "Обзор продукта", "url": "/static/videos/1.mp4", "thumbnail": "/static/img/thumb1.jpg", "duration": "5:30"},
    {"id": 2, "title": "Инструкция", "url": "/static/videos/2.mp4", "thumbnail": "/static/img/thumb2.jpg", "duration": "3:45"},
]

testimonials_db = [
    {
        "id": 1,
        "author": "Анна Смирнова",
        "avatar": "А",
        "text": "Отличный сервис! Все работает быстро и удобно. Рекомендую всем своим знакомым.",
        "rating": 5,
        "date": "2024-01-15",
        "city": "Москва"
    },
    {
        "id": 2,
        "author": "Иван Петров",
        "avatar": "И",
        "text": "Использую уже полгода. Качество на высоте, поддержка всегда на связи.",
        "rating": 5,
        "date": "2024-01-10",
        "city": "Санкт-Петербург"
    },
    {
        "id": 3,
        "author": "Мария Козлова",
        "avatar": "М",
        "text": "Простой и понятный интерфейс. Всё интуитивно, разобралась за 5 минут!",
        "rating": 5,
        "date": "2024-01-05",
        "city": "Казань"
    }
]

@router.get("/gallery")
async def get_gallery(page: int = 1, per_page: int = 12):
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "success": True,
        "images": gallery_db[start:end],
        "total": len(gallery_db),
        "page": page,
        "pages": (len(gallery_db) + per_page - 1) // per_page
    }

@router.get("/gallery/{image_id}")
async def get_image(image_id: int):
    image = next((img for img in gallery_db if img["id"] == image_id), None)
    if not image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    
    return {
        "success": True,
        "image": image
    }

class FileMetadata(BaseModel):
    id: str
    filename: str
    original_name: str
    size: int
    content_type: str
    category: str
    upload_date: str
    url: str
    thumbnail: Optional[str] = None

files_db = {}

def get_file_category(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for category, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return category
    return 'other'

def generate_file_id(filename: str) -> str:
    timestamp = datetime.now().isoformat()
    return hashlib.md5(f"{filename}{timestamp}".encode()).hexdigest()

def format_file_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")
    
    file_ext = Path(file.filename).suffix.lower()
    category = get_file_category(file.filename)
    
    if category == 'other':
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла")
    
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"Размер файла превышает {MAX_FILE_SIZE // (1024*1024)} MB")
    
    file_id = generate_file_id(file.filename)
    safe_filename = f"{file_id}{file_ext}"
    
    category_dir = UPLOAD_DIR / (category + 's' if category != 'audio' else category)
    file_path = category_dir / safe_filename
    
    with open(file_path, 'wb') as f:
        f.write(contents)
    
    file_url = f"/static/uploads/{category_dir.name}/{safe_filename}"
    
    metadata = {
        "id": file_id,
        "filename": safe_filename,
        "original_name": file.filename,
        "size": file_size,
        "size_formatted": format_file_size(file_size),
        "content_type": file.content_type or mimetypes.guess_type(file.filename)[0],
        "category": category,
        "upload_date": datetime.now().isoformat(),
        "url": file_url
    }
    
    files_db[file_id] = metadata
    
    return {
        "success": True,
        "message": "Файл успешно загружен",
        "file": metadata
    }

@router.get("/files")
async def get_files(category: Optional[str] = None, page: int = 1, per_page: int = 20):
    filtered_files = list(files_db.values())
    
    if category:
        filtered_files = [f for f in filtered_files if f['category'] == category]
    
    filtered_files.sort(key=lambda x: x['upload_date'], reverse=True)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "success": True,
        "files": filtered_files[start:end],
        "total": len(filtered_files),
        "page": page,
        "pages": (len(filtered_files) + per_page - 1) // per_page
    }

@router.get("/files/{file_id}")
async def get_file(file_id: str):
    if file_id not in files_db:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return {
        "success": True,
        "file": files_db[file_id]
    }

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    if file_id not in files_db:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    file_meta = files_db[file_id]
    category_dir = UPLOAD_DIR / (file_meta['category'] + 's' if file_meta['category'] != 'audio' else file_meta['category'])
    file_path = category_dir / file_meta['filename']
    
    if file_path.exists():
        file_path.unlink()
    
    del files_db[file_id]
    
    return {
        "success": True,
        "message": "Файл успешно удален"
    }

@router.get("/download/{file_id}")
async def download_file(file_id: str):
    if file_id not in files_db:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    file_meta = files_db[file_id]
    category_dir = UPLOAD_DIR / (file_meta['category'] + 's' if file_meta['category'] != 'audio' else file_meta['category'])
    file_path = category_dir / file_meta['filename']
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден на сервере")
    
    return FileResponse(
        path=file_path,
        filename=file_meta['original_name'],
        media_type=file_meta['content_type']
    )

@router.post("/files/{file_id}/rename")
async def rename_file(file_id: str, new_name: str = Form(...)):
    if file_id not in files_db:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    file_meta = files_db[file_id]
    old_ext = Path(file_meta['original_name']).suffix
    new_ext = Path(new_name).suffix or old_ext
    
    if not new_name.endswith(new_ext):
        new_name += new_ext
    
    file_meta['original_name'] = new_name
    
    return {
        "success": True,
        "message": "Файл переименован",
        "file": file_meta
    }

@router.get("/storage-info")
async def get_storage_info():
    total_size = sum(f['size'] for f in files_db.values())
    category_stats = {}
    
    for category in ['image', 'video', 'audio', 'document', 'archive']:
        category_files = [f for f in files_db.values() if f['category'] == category]
        category_stats[category] = {
            "count": len(category_files),
            "size": sum(f['size'] for f in category_files),
            "size_formatted": format_file_size(sum(f['size'] for f in category_files))
        }
    
    return {
        "success": True,
        "total_files": len(files_db),
        "total_size": total_size,
        "total_size_formatted": format_file_size(total_size),
        "max_size": MAX_FILE_SIZE,
        "max_size_formatted": format_file_size(MAX_FILE_SIZE),
        "used_percent": round((total_size / (MAX_FILE_SIZE * 10)) * 100, 2),
        "categories": category_stats
    }

@router.get("/videos")
async def get_videos():
    return {
        "success": True,
        "videos": videos_db
    }

@router.get("/videos/{video_id}")
async def get_video(video_id: int):
    video = next((v for v in videos_db if v["id"] == video_id), None)
    if not video:
        raise HTTPException(status_code=404, detail="Видео не найдено")
    
    return {
        "success": True,
        "video": video
    }

@router.get("/testimonials")
async def get_testimonials(page: int = 1, per_page: int = 10):
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "success": True,
        "testimonials": testimonials_db[start:end],
        "total": len(testimonials_db)
    }

@router.post("/testimonials")
async def create_testimonial(testimonial: Testimonial):
    new_id = max(t["id"] for t in testimonials_db) + 1
    new_testimonial = {**testimonial.dict(), "id": new_id}
    testimonials_db.append(new_testimonial)
    
    return {
        "success": True,
        "message": "Отзыв успешно добавлен",
        "testimonial": new_testimonial
    }
