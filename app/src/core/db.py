from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv
from src.config import get_settings

# Явно загружаем .env файл перед получением настроек
load_dotenv()
settings = get_settings()

print(f"Using database: {settings.DATABASE_URL}")  # Добавим для отладки

# Создаем базовый класс для моделей
class Base(DeclarativeBase):
    pass

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

def setup_db_relationships():
    from src.core.relationships import setup_relationships
    setup_relationships() 