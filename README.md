# MyMessage Backend (FastAPI + WebSocket)    
Асинхронный backend для мессенджера с REST и WebSocket API


## Скачайте и запустите проект через Docker

```bash
git clone https://github.com/rrdobrr/mymessage.git
cd mymessage
docker-compose up --build
```

## Инициализируйте базу данных для тестов
- docker compose exec web python init_db.py

## Запуск тестов:
- docker compose exec web python -m tests.run_tests -s 
- Запускается 25 тестов в 5 логических блоках (app/tests/)
- Два теста проверены и отключены во избежание конфликтов:
    - Тест удаления пользователя
    - Тест удаления участника чата

## Подключение к базе данных:
- docker compose exec db psql -U postgres mymessage



## Особенности реализованного функционала:
- Хэширование паролей;
- Авторизация через JWT токены;
- WebSocket-подключения с нескольких устройств;
- Уведомления о новых сообщениях;
- Уведомления о прочтении сообщений;
- Уведомления об онлайне/офлайне участников чата;
- Swagger-документация:
    - http://localhost:8000/docs



## Стек
- Python 3.12-slim
- FastAPI
- PostgreSQL (через asyncpg)
- SQLAlchemy (Async)
- WebSocket (starlette.websockets)
- Pytest
- Docker / Docker Compose

