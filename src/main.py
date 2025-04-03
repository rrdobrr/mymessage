from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.api_v1.routers import api_router as api_v1_router
from src.core.logging import setup_logging
from src.core.exceptions import AppException, app_exception_handler

# Инициализируем логгер
logger = setup_logging()
settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрируем обработчик исключений
app.add_exception_handler(AppException, app_exception_handler)

# Подключаем роутеры API v1
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

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
