# app/main.py

from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
from app.api.v1.endpoints import router as api_v1_router
from app.config import app_settings
from app.utils.logging import setup_logger

# Загрузка переменных окружения
load_dotenv(dotenv_path=".env", override=True)

# Настройка логгера
logger = setup_logger(__name__)

# Создание приложения
app = FastAPI(
    title=app_settings.app_name,
    debug=app_settings.debug
)

# Подключение роутеров
app.include_router(api_v1_router)

# Корневой эндпоинт
@app.get("/")
async def root():
    """
    Корневой эндпоинт приложения.
    """
    return {
        "name": app_settings.app_name,
        "environment": app_settings.environment,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    logger.info(f"Запуск приложения на {app_settings.host}:{app_settings.port}")
    uvicorn.run(
        "app.main:app",
        host=app_settings.host,
        port=app_settings.port,
        reload=app_settings.reload
    )