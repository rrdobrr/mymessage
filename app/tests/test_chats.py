import pytest
from httpx import AsyncClient
from tests.conftest import AUTH_USER_DATA, VALID_USER_DATA

from .logger_for_pytest import logger

pytestmark = pytest.mark.asyncio


async def get_available_user_id(client: AsyncClient, headers: dict) -> int:
    """Получает ID пользователя, с которым еще нет чата"""
    # Получаем список всех пользователей
    users_response = await client.get("/api/v1/users/list", headers=headers)
    all_users = users_response.json()
    
    # Получаем текущего пользователя
    me_response = await client.get("/api/v1/users/me", headers=headers)
    current_user = me_response.json()
    
    # Получаем существующие чаты
    chats_response = await client.get("/api/v1/chats/list", headers=headers)
    existing_chats = chats_response.json()
    
    # Собираем ID пользователей из существующих чатов
    users_with_chats = set()
    for chat in existing_chats:
        if chat.get("members"):  # Проверяем наличие members
            users_with_chats.update(m["id"] for m in chat["members"])
    
    # Ищем пользователя без чата
    for user in all_users:
        if user["id"] != current_user["id"] and user["id"] not in users_with_chats:
            return user["id"]
    
    # Если не нашли свободного пользователя, возвращаем фиксированный ID тестового пользователя
    return 3  # Возвращаем ID тестового пользователя как запасной вариант


async def get_group_chat_id(client: AsyncClient, headers: dict) -> int:
    """Получает ID любого группового чата пользователя или создает новый"""
    # Сначала проверяем существующие чаты
    chats_response = await client.get("/api/v1/chats/list", headers=headers)
    chats = chats_response.json()
    
    # Ищем первый групповой чат
    for chat in chats:
        if chat["chat_type"] == "group":
            return chat["id"]
    
    # Если не нашли, создаем новый групповой чат
    chat_data = {
        "chat_type": "group",
        "name": "Test Group Chat",
        "member_ids": [1]  # Добавляем одного участника для теста
    }
    response = await client.post("/api/v1/chats/create", headers=headers, json=chat_data)
    assert response.status_code == 200, "Не удалось создать групповой чат"
    
    return response.json()["id"]


async def get_chat_and_member_for_removal(client: AsyncClient, headers: dict) -> tuple[int, int]:
    """Возвращает ID группового чата с наибольшим числом участников и ID участника для удаления"""
    # Получаем список чатов
    chats_response = await client.get("/api/v1/chats/list", headers=headers)
    chats = chats_response.json()
    
    # Получаем текущего пользователя
    me_response = await client.get("/api/v1/users/me", headers=headers)
    current_user = me_response.json()
    
    # Ищем групповой чат с наибольшим количеством участников
    group_chats = [
        chat for chat in chats 
        if chat["chat_type"] == "group" and len(chat.get("members", [])) > 1
    ]
    
    if not group_chats:
        # Если нет подходящего чата, создаем новый с двумя участниками
        chat_data = {
            "chat_type": "group",
            "name": "Test Group Chat",
            "member_ids": [1, 3]  # Добавляем двух участников
        }
        response = await client.post("/api/v1/chats/create", headers=headers, json=chat_data)
        assert response.status_code == 200
        chat = response.json()
    else:
        # Берем чат с наибольшим количеством участников
        chat = max(group_chats, key=lambda x: len(x.get("members", [])))
    
    # Выбираем участника для удаления (любого, кроме текущего пользователя)
    member_to_remove = next(
        member["id"] for member in chat["members"] 
        if member["id"] != current_user["id"]
    )
    
    return chat["id"], member_to_remove


class TestChats:
    """Тесты для работы с чатами"""

    async def test_get_user_chats(self, client: AsyncClient):
        """Тест получения списка чатов пользователя"""
        # Логинимся
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Получаем список чатов
        response = await client.get("/api/v1/chats/list", headers=headers)
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Ответ должен быть списком"
        # Проверяем структуру данных, даже если список пустой
        if len(data) > 0:
            chat = data[0]
            assert all(key in chat for key in ["id", "chat_type", "members"]), \
                "Отсутствуют обязательные поля в объекте чата"


    async def test_create_personal_chat(self, client: AsyncClient):
        """Тест создания личного чата"""
        # Логинимся
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Находим пользователя для создания чата

        participant_id = 3

        # Создаем личный чат
        chat_data = {
            "name": "Test Personal Chat",
            "chat_type": "personal",
            "member_ids": [participant_id]
        }
        response = await client.post("/api/v1/chats/create", headers=headers, json=chat_data)
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()
        assert data["chat_type"] == "personal", "Неверный тип чата"
        assert data["participant_id"] == participant_id, "Неверный ID участника"

    async def test_create_group_chat(self, client: AsyncClient):
        """Тест создания группового чата"""
        # Логинимся
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Находим пользователя для добавления в групповой чат


        # Создаем групповой чат
        chat_data = {
            "chat_type": "group",
            "name": "Test Group Chat",
            "member_ids": [1, 3]  # ID других пользователей
        }
        response = await client.post("/api/v1/chats/create", headers=headers, json=chat_data)
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()

        assert data["chat_type"] == "group", "Неверный тип чата"
        assert data["name"] == "Test Group Chat", "Неверное название чата"
        assert len(data["members"]) >= 3, "В групповом чате должно быть минимум 3 участника"
        assert all(user_id in [p["id"] for p in data["members"]] for user_id in [2, 3]), \
            "Не все участники найдены в созданном чате"

    async def test_add_participant(self, client: AsyncClient):
        """Тест добавления участника в групповой чат"""
        # Логинимся
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Получаем ID группового чата
        chat_id = await get_group_chat_id(client, headers)

        # Получаем ID доступного пользователя
        new_member_id = await get_available_user_id(client, headers)

        # Добавляем участника
        add_data = [new_member_id]

        response = await client.post(
            f"/api/v1/chats/{chat_id}/members/add",
            headers=headers,
            json=add_data
        )

        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()
        assert new_member_id in [m["id"] for m in data["members"]], \
            "Добавленный участник не найден в списке участников"

    @pytest.mark.skipif(True, reason="Отключено для отладки")
    async def test_remove_participant(self, client: AsyncClient):
        """Тест удаления участника из группового чата"""
        # Логинимся
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Получаем ID чата и участника для удаления
        chat_id, member_id = await get_chat_and_member_for_removal(client, headers)
        logger.info(f"Chat ID: {chat_id}")
        logger.info(f"Member ID: {member_id}")
        # Удаляем участника
        response = await client.post(
            f"/api/v1/chats/{chat_id}/members/remove",
            headers=headers,
            json=[member_id]
        )
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()
        assert member_id not in [m["id"] for m in data["members"]], \
            "Удаленный участник все еще находится в списке участников"

    async def test_access_rights(self, client: AsyncClient):
        """Тест прав доступа к чату"""
        # Логинимся от имени первого пользователя
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Получаем список чатов пользователя
        chats_response = await client.get("/api/v1/chats/list", headers=headers)
        chats = chats_response.json()

        # Находим первый групповой чат
        group_chat = next(
            (chat for chat in chats if chat["chat_type"] == "group"),
            None
        )
        
        if not group_chat:
            # Если нет группового чата, создаем новый
            chat_data = {
                "chat_type": "group",
                "name": "Test Group Chat",
                "member_ids": [3]  # Добавляем одного участника
            }
            response = await client.post("/api/v1/chats/create", headers=headers, json=chat_data)
            assert response.status_code == 200
            group_chat = response.json()

        # Получаем ID всех участников чата
        chat_member_ids = {member["id"] for member in group_chat["members"]}
        
        # Получаем список всех пользователей
        users_response = await client.get("/api/v1/users/list", headers=headers)
        all_users = users_response.json()
        
        # Находим пользователя, который не является участником чата
        non_member = next(
            user for user in all_users 
            if user["id"] not in chat_member_ids
        )
        logger.info(f"Non member: {non_member}")
        # Логинимся от имени найденного пользователя
        login_response = await client.post("/api/v1/auth/token", data={
            "username": non_member["email"],
            "password": "testpass123"
        })
        if login_response.status_code != 200:
            login_response = await client.post("/api/v1/auth/token", data={
            "username": non_member["email"],
            "password": "testotest"
        })
            
        logger.info(f"Login response: {login_response}")
        tokens = login_response.json()
        logger.info(f"Tokens: {tokens}")
        test_user_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Пробуем получить доступ к чату от имени пользователя не из чата
        response = await client.get(f"/api/v1/chats/{group_chat['id']}", headers=test_user_headers)
        assert response.status_code == 403, "Должен быть запрещен доступ к чужому чату" 