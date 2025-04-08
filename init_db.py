import asyncio
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from src.core.db import AsyncSessionFactory
from src.features.auth.services import AuthService
from src.features.auth.dependencies import get_current_user
from src.features.users.schemas import UserCreate
from src.features.chats.services import ChatService
from src.features.chats.schemas import ChatCreate, ChatType


def run_migrations():
    """Применение миграций с проверкой текущей версии"""
    print("⚙️  Проверка и применение миграций...")
    alembic_cfg = Config("alembic.ini")
    
    try:
        # Получаем информацию о миграциях
        script = ScriptDirectory.from_config(alembic_cfg)
        head_revision = script.get_current_head()
        
        # Получаем текущую версию БД
        current = command.current(alembic_cfg)
        
        if current == head_revision:
            print("✅ База данных уже находится в актуальном состоянии")
            return
            
        print("⚙️  Применение миграций...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Миграции успешно применены")
        
    except Exception as e:
        if "relation" in str(e) and "already exists" in str(e):
            print("⚠️  Таблицы уже существуют, пропускаем миграции")
            return
        raise e


async def create_test_data():
    print("👤 Создание тестовых данных...")
    async with AsyncSessionFactory() as session:
        try:
            auth_service = AuthService(session)
            chat_service = ChatService(session)

            # Создаем тестовых пользователей
            test_users = [
                UserCreate(
                    email="additional_user@user.com",
                    username="Additional",
                    password="testotest"
                ),
                UserCreate(
                    email="test@test.com",
                    username="Testosterone",
                    password="testotest"
                ),
                UserCreate(
                    email="just@just.com",
                    username="Justin",
                    password="testotest"
                )
            ]

            created_users = []
            for user_data in test_users:
                try:
                    user = await auth_service.register(user_data)
                    created_users.append(user)
                    print(f"✅ Создан пользователь: {user.email}")
                except Exception as e:
                    print(f"❌ Ошибка при создании пользователя {user_data.email}: {str(e)}")

            if len(created_users) >= 2:
                try:
                    # Авторизуемся первым пользователем
                    form_data = OAuth2PasswordRequestForm(
                        username=test_users[1].email,
                        password=test_users[1].password,
                        scope=""
                    )
                    tokens = await auth_service.login(form_data)
                    
                    # Получаем текущего пользователя через dependency
                    current_user = await get_current_user(tokens.access_token, session)
                    
                    # Создаем тестовый групповой чат
                    chat_data = ChatCreate(
                        name="Test Chat",
                        chat_type=ChatType.GROUP,
                        member_ids=[created_users[0].id, created_users[2].id]
                    )
                    
                    chat = await chat_service.create_chat(
                        chat_data=chat_data,
                        current_user=current_user
                    )
                    print(f"✅ Создан тестовый чат: {chat.name}")
                except Exception as e:
                    print(f"❌ Ошибка при создании чата: {str(e)}")
            
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


if __name__ == "__main__":
    try:
        run_migrations()
        asyncio.run(create_test_data())
    except Exception as e:
        print(f"❌ Произошла ошибка: {str(e)}")
        raise
