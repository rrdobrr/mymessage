from typing import Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime

from src.core.logging import logger
from src.features.users.schemas import UserInDB
from src.core.exceptions import InvalidTokenException
from src.features.messages.schemas import WebSocketMessage, WebSocketResponse, MessageCreate
from src.features.messages.services import MessageService
from src.features.users.repositories import UserRepository
from src.core.db import AsyncSession
from fastapi import WebSocketDisconnect
from pydantic import ValidationError

from src.core.security import get_token_from_websocket

class WebSocketService:
    def __init__(self):
        logger.info("СМОТРИИИ! WebSocketService initialized")
        self._active_connections: Dict[int, Set[WebSocket]] = {}
        self._user_connections: Dict[int, Set[WebSocket]] = {}
        logger.info(f"WebSocketService initialized with id {id(self)}")

    async def connect(self, websocket: WebSocket, chat_id: int, user: UserInDB):
        """Подключение нового WebSocket соединения"""
        try:
            connection_id = id(websocket)
            logger.debug(f"New connection attempt - WebSocket ID: {connection_id}")
            logger.debug(f"Connection state before accept: {websocket.client_state}")
            
            # Проверяем, нет ли уже такого соединения
            if chat_id in self._active_connections and websocket in self._active_connections[chat_id]:
                logger.warning(f"WebSocket {connection_id} already exists in chat {chat_id}")
                return
                
            await websocket.accept()
            logger.debug(f"Connection state after accept: {websocket.client_state}")
            
            if chat_id not in self._active_connections:
                self._active_connections[chat_id] = set()
            self._active_connections[chat_id].add(websocket)
            
            if user.id not in self._user_connections:
                self._user_connections[user.id] = set()
            self._user_connections[user.id].add(websocket)
            
            logger.info(f"WebSocket {connection_id} connected: chat_id={chat_id}, user_id={user.id}")
            logger.debug(f"Active connections for chat {chat_id}: {len(self._active_connections[chat_id])}")
            
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {str(e)}")
            raise

    async def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Отключение WebSocket соединения"""
        try:
            connection_id = id(websocket)
            logger.debug(f"Disconnecting WebSocket {connection_id}")
            
            if chat_id in self._active_connections:
                was_removed = websocket in self._active_connections[chat_id]
                self._active_connections[chat_id].remove(websocket)
                logger.debug(f"Connection removed from chat {chat_id}: {was_removed}")
            
            if user_id in self._user_connections:
                was_removed = websocket in self._user_connections[user_id]
                self._user_connections[user_id].remove(websocket)
                logger.debug(f"Connection removed from user {user_id}: {was_removed}")
                
            logger.info(f"WebSocket {connection_id} disconnected: chat_id={chat_id}, user_id={user_id}")
            
        except KeyError:
            logger.warning(f"Attempted to disconnect non-existent WebSocket {id(websocket)}")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")

    async def broadcast_message(
        self, 
        chat_id: int, 
        message: dict, 
        exclude_websocket: Optional[WebSocket] = None
    ):
        """Отправка сообщения всем подключенным клиентам в чате"""
        if chat_id in self._active_connections:
            for connection in self._active_connections[chat_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting message: {str(e)}")

    async def send_user_connected_message(
        self, 
        chat_id: int, 
        user: UserInDB, 
        exclude_websocket: Optional[WebSocket] = None
    ):
        """Отправка уведомления о подключении пользователя"""
        message = {
            "type": "user_connected",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_message(chat_id, message, exclude_websocket)

    async def send_user_disconnected_message(
        self, 
        chat_id: int, 
        user: UserInDB
    ):
        """Отправка уведомления об отключении пользователя"""
        message = {
            "type": "user_disconnected",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_message(chat_id, message)

    async def send_read_status(
        self, 
        chat_id: int, 
        message_id: int, 
        user_id: int
    ):
        """Отправка статуса прочтения сообщения"""
        status_message = {
            "type": "read_status",
            "message_id": message_id,
            "user_id": user_id,
            "chat_id": chat_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_message(chat_id, status_message)

    async def handle_connection(
        self, 
        websocket: WebSocket, 
        chat_id: int,
        db: AsyncSession,
        message_service: MessageService
    ):
        """Обработка WebSocket соединения"""
        connection_id = id(websocket)
        current_user = None
        
        try:
            # Аутентификация
            try:
                token = await get_token_from_websocket(websocket)
                user_repo = UserRepository(db)
                current_user = await user_repo.get_current_user_websocket(token)
                logger.debug(f"User {current_user.id} authenticated for connection {connection_id}")
            except InvalidTokenException:
                logger.warning(f"Invalid token for connection {connection_id}")
                await websocket.close(code=4003)
                return
            
            # Подключаем WebSocket
            await self.connect(websocket, chat_id, current_user)
            logger.info(f"WebSocket {connection_id} established for chat {chat_id}")
            
            # Отправляем сообщение о подключении пользователя
            await self.send_user_connected_message(chat_id, current_user, websocket)
            
            while True:
                try:
                    # Получаем и валидируем входящее сообщение
                    raw_data = await websocket.receive_json()
                    message = WebSocketMessage.model_validate(raw_data)
                    logger.debug(f"Received message from client: {message}")
                    
                    # Создаем сообщение в базе данных
                    message_data = MessageCreate(
                        chat_id=chat_id,
                        text=message.text
                    )
                    db_message = await message_service.create_message(message_data, current_user)
                    logger.info(f"Created message in database: {db_message.id}")
                    
                    # Формируем и отправляем ответ всем участникам чата
                    response = WebSocketResponse(
                        type="message",
                        text=message.text,
                        timestamp=db_message.created_at,
                        user_id=current_user.id,
                        message_id=db_message.id
                    )
                    # Отправляем сообщение всем подключенным клиентам в чате
                    await self.broadcast_message(chat_id, response.model_dump(mode='json'))
                    
                except WebSocketDisconnect:
                    logger.info(f"Client {current_user.id} disconnected normally from chat {chat_id}")
                    break
                except ValidationError as e:
                    logger.error(f"Invalid message format: {str(e)}")
                    error_response = WebSocketResponse(
                        type="error",
                        text="Invalid message format",
                        timestamp=datetime.utcnow(),
                        user_id=current_user.id
                    )
                    await websocket.send_json(error_response.model_dump(mode='json'))
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {str(e)}")
                    break
                
        except Exception as e:
            logger.exception("Unexpected WebSocket error")
            if not websocket.client_state.DISCONNECTED:
                await websocket.close(code=4000)
        finally:
            if current_user:
                # Отключаем WebSocket и отправляем сообщение об отключении
                await self.disconnect(websocket, chat_id, current_user.id)
                await self.send_user_disconnected_message(chat_id, current_user) 