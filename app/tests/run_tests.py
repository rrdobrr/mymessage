import pytest
import sys
from pathlib import Path

from .logger_for_pytest import logger

# Добавляем путь к src в PYTHONPATH
root_path = Path(__file__).parent.parent
src_path = root_path / "src"
sys.path.append(str(src_path))

def run_tests():
    """Запуск всех тестов"""
    test_path = Path(__file__).parent
    
    # Запускаем тесты
    exit_code = pytest.main([
        "-v",
        "-x",
        "--tb=short",
        "--maxfail=1",
        "-s",
        str(test_path / "test_auth.py"),
        str(test_path / "test_users.py"),
        str(test_path / "test_chats.py"),
        str(test_path / "test_messages.py"),
        str(test_path / "test_websocket.py")
    ])
    
    if exit_code != 0:
        logger.info("\nТесты остановлены из-за ошибки.")
        sys.exit(exit_code)

if __name__ == "__main__":
    run_tests()