import logging
import sys
from pathlib import Path
from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    # Создаем директорию для логов если её нет
    logs_path = Path("logs")
    logs_path.mkdir(exist_ok=True)

    # Настраиваем логирование
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logger.configure(
        handlers=[
            {"sink": sys.stdout, "level": logging.INFO},
            {"sink": "logs/app.log", "rotation": "500 MB", "level": logging.INFO},
        ]
    )

    # Перехватываем логи uvicorn
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]

    return logger 