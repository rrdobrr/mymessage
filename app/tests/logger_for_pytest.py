

import logging
import sys

def get_test_logger(name: str = "pytest-visible-logger") -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)  # 👈 вывод в stdout, а не stderr
        handler.setLevel(logging.DEBUG)

        # Простой читаемый формат
        formatter = logging.Formatter("%(levelname)s — %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        # Отключаем bubbling, чтобы не перехватывал pytest
        logger.propagate = False

    return logger

logger = get_test_logger()