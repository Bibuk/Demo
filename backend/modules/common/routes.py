from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/common", tags=["Общие компоненты"])

class BreadcrumbItem(BaseModel):
    label: str
    url: Optional[str] = None

class NavigationItem(BaseModel):
    label: str
    url: str
    icon: Optional[str] = None
    children: Optional[List['NavigationItem']] = None

navigation = [
    {"label": "Главная", "url": "/", "icon": "home"},
    {"label": "Авторизация", "url": "/auth", "icon": "lock"},
    {"label": "Профиль", "url": "/profile", "icon": "user"},
    {"label": "Компоненты", "url": "/components", "icon": "grid"},
    {"label": "Магазин", "url": "/shop", "icon": "shop"},
    {"label": "Медиа", "url": "/media", "icon": "image"},
]

footer_links = {
    "company": [
        {"label": "О нас", "url": "/about"},
        {"label": "Контакты", "url": "/contacts"},
        {"label": "Вакансии", "url": "/careers"}
    ],
    "products": [
        {"label": "Каталог", "url": "/shop"},
        {"label": "Цены", "url": "/pricing"},
        {"label": "API", "url": "/api"}
    ],
    "support": [
        {"label": "Документация", "url": "/docs"},
        {"label": "FAQ", "url": "/faq"},
        {"label": "Техподдержка", "url": "/support"}
    ],
    "legal": [
        {"label": "Условия использования", "url": "/terms"},
        {"label": "Политика конфиденциальности", "url": "/privacy"},
        {"label": "Лицензия", "url": "/license"}
    ]
}

social_links = [
    {"name": "VK", "url": "https://vk.com", "icon": "vk"},
    {"name": "Telegram", "url": "https://t.me", "icon": "telegram"},
    {"name": "YouTube", "url": "https://youtube.com", "icon": "youtube"},
    {"name": "GitHub", "url": "https://github.com", "icon": "github"}
]

@router.get("/navigation")
async def get_navigation():
    return {
        "success": True,
        "navigation": navigation
    }

@router.get("/footer")
async def get_footer():
    return {
        "success": True,
        "footer": {
            "links": footer_links,
            "social": social_links,
            "copyright": "© 2024 Demo Company. Все права защищены."
        }
    }

@router.post("/breadcrumbs")
async def generate_breadcrumbs(items: List[BreadcrumbItem]):
    return {
        "success": True,
        "breadcrumbs": items
    }

@router.get("/search")
async def search(query: str, category: Optional[str] = None):
    return {
        "success": True,
        "query": query,
        "category": category,
        "results": [
            {"type": "page", "title": "Главная страница", "url": "/"},
            {"type": "product", "title": "Товар 1", "url": "/shop/1"},
        ]
    }

@router.get("/stats")
async def get_stats():
    return {
        "success": True,
        "stats": {
            "users": 1234,
            "products": 56,
            "orders": 789,
            "reviews": 123
        }
    }

@router.get("/seo")
async def get_seo_data(page: str):
    seo_data = {
        "/": {
            "title": "Главная - Demo Company",
            "description": "Демонстрационный сайт с умениями компании",
            "keywords": "demo, веб-разработка, компоненты"
        },
        "/auth": {
            "title": "Авторизация - Demo Company",
            "description": "Вход и регистрация на сайте",
            "keywords": "вход, регистрация, авторизация"
        }
    }
    
    return {
        "success": True,
        "seo": seo_data.get(page, {
            "title": "Demo Company",
            "description": "Демонстрационный сайт",
            "keywords": "demo"
        })
    }

@router.get("/contacts")
async def get_contacts():
    return {
        "success": True,
        "contacts": {
            "email": "info@democompany.ru",
            "phone": "+7 (495) 123-45-67",
            "address": "г. Москва, ул. Примерная, д. 1",
            "working_hours": "Пн-Пт: 9:00-18:00"
        }
    }
