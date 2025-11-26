from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os

from database import init_db, User, Profile, async_session_maker, get_db
from modules.auth.security import get_password_hash

from modules.auth.routes import router as auth_router
from modules.profile.routes import router as profile_router
from modules.components.routes import router as components_router
from modules.shop.routes import router as shop_router
from modules.media.routes import router as media_router
from modules.common.routes import router as common_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "test@demo.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            test_user = User(
                email="test@demo.com",
                username="demo_user",
                hashed_password=get_password_hash("Test1234!"),
                is_verified=1
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            test_profile = Profile(
                user_id=test_user.id,
                full_name="Тестовый Пользователь",
                phone="+7 (999) 123-45-67",
                bio="Это демонстрационный профиль"
            )
            session.add(test_profile)
            await session.commit()
            
            print(f"\n[+] Тестовый пользователь создан:")
            print(f"    Email: test@demo.com")
            print(f"    Пароль: Test1234!\n")
        
        support_result = await session.execute(select(User).where(User.email == "support@demo.com"))
        support_user = support_result.scalar_one_or_none()
        
        if not support_user:
            support_user = User(
                email="support@demo.com",
                username="support",
                hashed_password=get_password_hash("Support1234!"),
                is_verified=1
            )
            session.add(support_user)
            await session.commit()
            await session.refresh(support_user)
            
            support_profile = Profile(
                user_id=support_user.id,
                full_name="Служба поддержки",
                phone="+7 (800) 555-35-35",
                bio="Техническая поддержка магазина"
            )
            session.add(support_profile)
            await session.commit()
            
            print(f"[+] Пользователь поддержки создан:")
            print(f"    Email: support@demo.com")
            print(f"    Пароль: Support1234!\n")
    
    yield
    print("\n[!] Остановка приложения...")

app = FastAPI(title="Демонстрационный сайт компонентов", lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(components_router, prefix="/api")
app.include_router(shop_router, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(common_router, prefix="/api")

@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools():
    return {}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/auth", response_class=HTMLResponse)
def auth_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/components", response_class=HTMLResponse)
def components_page(request: Request):
    return templates.TemplateResponse("components.html", {"request": request})

@app.get("/shop", response_class=HTMLResponse)
def shop_page(request: Request):
    return templates.TemplateResponse("shop.html", {"request": request})

@app.get("/media", response_class=HTMLResponse)
def media_page(request: Request):
    return templates.TemplateResponse("media.html", {"request": request})

@app.get("/common", response_class=HTMLResponse)
def common_page(request: Request):
    return templates.TemplateResponse("common.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
def terms_page(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/support-dashboard", response_class=HTMLResponse)
def support_dashboard_page(request: Request):
    return templates.TemplateResponse("support_dashboard.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
