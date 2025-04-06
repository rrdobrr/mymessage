import sys
from pathlib import Path


# Добавляем родительскую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.api_v1.routers import api_router
from src.core.logging import setup_logging, logger
from src.core.exceptions import setup_exception_handlers
from src.core.relationships import setup_relationships
from src.core.db import Base, engine, setup_db_relationships

# Инициализируем настройки
settings = get_settings()

# Инициализируем логгер
setup_logging()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API для мессенджера MyMessage",
    version=settings.VERSION,
    # Добавляем настройку безопасности для Swagger UI
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    }
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Инициализация приложения"""
    # Создаем таблицы в БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Устанавливаем отношения между моделями
    setup_relationships()

# Регистрируем обработчики исключений
setup_exception_handlers(app)

# Подключаем все роуты через единый роутер
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Welcome to MyMessage API"}

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
