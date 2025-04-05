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
    # Создаем директорию для логов если её нет
    logs_path = Path("logs")
    logs_path.mkdir(exist_ok=True)

    # Настраиваем логирование
    loguru_logger.configure(
        handlers=[
            {"sink": sys.stdout, "level": logging.INFO},
            {"sink": "logs/app.log", "rotation": "500 MB", "level": logging.INFO},
        ]
    )

    # Перехватываем логи uvicorn и fastapi
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.setLevel(logging.INFO)  # Устанавливаем уровень логирования


# Экспортируем настроенный логгер
logger = loguru_logger

__all__ = ["logger", "setup_logging"] 