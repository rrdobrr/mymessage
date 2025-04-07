# MyMessage Backend (FastAPI + WebSocket)    
Асинхронный backend для мессенджера с REST и WebSocket API


## Запуск проекта через Docker

```bash
git clone https://github.com/yourname/mymessage.git
cd mymessage
docker-compose up --build
```
Swagger-документация будет доступна по адресу:
📍 http://localhost:8000/docs


## Запуск тестов:
- docker compose exec web python -m tests.run_tests -s 
- Запускается 25 тестов в 5 логических блоках (app/tests/)
- Два теста проверены и отключены во избежание конфликтов:
    - Тест удаления пользователя
    - Тест удаления участника чата


## Особенности реализованного функционала:
- Хэширование паролей;
- Авторизация через JWT токены;
- WebSocket-подключения с нескольких устройств;
- Уведомления о новых сообщениях;
- Уведомления о прочтении сообщений;
- Уведомления об онлайне/офлайне участников чата;
- Swagger по умолчаниюу:
    - http://localhost:8000/docs



## Стек
- Python 3.12-slim
- FastAPI
- PostgreSQL (через asyncpg)
- SQLAlchemy (Async)
- WebSocket (starlette.websockets)
- Pytest
- Docker / Docker Compose