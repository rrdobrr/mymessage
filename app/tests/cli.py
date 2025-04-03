import asyncio
import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent.parent))

from src.core.db import AsyncSessionFactory
from tests.conftest import create_test_data

async def load_test_data():
    """Загрузка тестовых данных в базу"""
    async with AsyncSessionFactory() as session:
        await create_test_data(session)
    print("Тестовые данные успешно загружены!")

if __name__ == "__main__":
    asyncio.run(load_test_data()) 