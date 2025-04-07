import logging
import sys
from pathlib import Path

from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """Настройка логирования для приложения"""
    # Удаляем все существующие обработчики
    loguru_logger.remove()
    
    # Создаем директорию для логов если её нет
    logs_path = Path("logs")
    logs_path.mkdir(exist_ok=True)

    # Настраиваем loguru с одним обработчиком
    loguru_logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": logging.INFO,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
            }
        ]
    )

    # Полностью отключаем все логи SQLAlchemy
    for logger_name in [
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.base.Engine",
        "sqlalchemy.dialects",
        "sqlalchemy.pool",
        "sqlalchemy.orm",
        "sqlalchemy.engine.Engine"
    ]:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        logging.getLogger(logger_name).propagate = False
        logging.getLogger(logger_name).handlers = []

    # # Отключаем логи uvicorn access
    # logging.getLogger("uvicorn.access").handlers = []
    # logging.getLogger("uvicorn.access").propagate = False

    # Перехватываем нужные логи
    for _log in ["uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False


# Экспортируем настроенный логгер
logger = loguru_logger

__all__ = ["logger", "setup_logging"]