from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/components", tags=["Компоненты"])

class NotificationCreate(BaseModel):
    message: str
    type: str = "info"

class ModalData(BaseModel):
    title: str
    content: str

class TableData(BaseModel):
    headers: List[str]
    rows: List[List[str]]

@router.post("/notification")
async def create_notification(notification: NotificationCreate):
    return {
        "success": True,
        "notification": notification.dict()
    }

@router.get("/modal-example")
async def get_modal_example():
    return {
        "title": "Пример модального окна",
        "content": "Это содержимое модального окна",
        "buttons": [
            {"label": "Отмена", "type": "secondary"},
            {"label": "Подтвердить", "type": "primary"}
        ]
    }

@router.get("/table-data")
async def get_table_data():
    return {
        "headers": ["ID", "Имя", "Email", "Статус"],
        "rows": [
            ["1", "Иван Иванов", "ivan@example.com", "Активен"],
            ["2", "Мария Петрова", "maria@example.com", "Ожидание"],
            ["3", "Петр Сидоров", "petr@example.com", "Заблокирован"]
        ]
    }

@router.get("/pagination")
async def get_pagination_data(page: int = 1, per_page: int = 10):
    total_items = 100
    total_pages = (total_items + per_page - 1) // per_page
    
    return {
        "current_page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }
