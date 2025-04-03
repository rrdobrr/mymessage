from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import get_settings

settings = get_settings()

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Логирование SQL запросов
    future=True  # Использование новых функций SQLAlchemy
)

# Создаем фабрику сессий
AsyncSessionFactory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Функция для получения сессии БД
async def get_db() -> AsyncSession:
    """
    Генератор асинхронной сессии БД.
    Используется как зависимость в FastAPI эндпоинтах.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 