from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from src.features.messages.services import MessageService
from src.features.messages.dependencies import get_message_service

router = APIRouter()

@router.websocket("/ws/chat/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    message_service: MessageService = Depends(get_message_service)
):
    # Здесь будет реализована WebSocket логика
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Обработка входящих сообщений
    except WebSocketDisconnect:
        # Обработка отключения
        pass 