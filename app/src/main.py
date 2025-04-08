import sys
import asyncio
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
from src.core.wait_for_postgres import wait_for_postgres


# Инициализируем настройки
settings = get_settings()

# Инициализируем логгер
setup_logging()


# Создаём FastAPI приложение
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API для мессенджера MyMessage",
    version=settings.VERSION,
    swagger_ui_init_oauth={"usePkceWithAuthorizationCodeGrant": True}
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

    await wait_for_postgres(settings.DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    setup_relationships()

# Регистрируем обработчики исключений
setup_exception_handlers(app)

# Подключаем все роуты через единый роутер
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

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
