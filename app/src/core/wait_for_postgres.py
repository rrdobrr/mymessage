# src/core/wait_for_postgres.py

import asyncio
import asyncpg
from src.core.logging import logger
from urllib.parse import urlparse

async def wait_for_postgres(dsn: str, attempts: int = 10, delay: float = 1.0):
    # Преобразуем SQLAlchemy URL в формат для asyncpg
    parsed = urlparse(dsn)
    user = parsed.username
    password = parsed.password
    database = parsed.path[1:]  # убираем начальный '/'
    host = parsed.hostname
    port = parsed.port or 5432

    for i in range(attempts):
        try:
            conn = await asyncpg.connect(
                user=user,
                password=password,
                database=database,
                host=host,
                port=port
            )
            await conn.close()
            logger.info("✅ PostgreSQL is ready")
            return
        except Exception as e:
            logger.warning(f"⏳ Waiting for PostgreSQL... ({i+1}/{attempts})")
            await asyncio.sleep(delay)
    raise RuntimeError("❌ PostgreSQL did not become ready in time")
