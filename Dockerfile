FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Создание непривилегированного пользователя
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Установка PYTHONPATH
ENV PYTHONPATH=/app/app

CMD ["uvicorn", "app.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]  