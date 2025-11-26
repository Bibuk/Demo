import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    
    VK_CLIENT_ID: str = ""
    VK_CLIENT_SECRET: str = ""
    VK_REDIRECT_URI: str = "http://localhost:8000/api/auth/vk/callback"
    
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    
    APP_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
