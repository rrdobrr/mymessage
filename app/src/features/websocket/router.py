from fastapi import APIRouter, WebSocket, Depends
from .controller import WebSocketController
from .dependencies import get_websocket_controller, get_current_user_ws
from src.features.users.schemas import UserInDB

router = APIRouter()

@router.websocket("/chat/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    controller: WebSocketController = Depends(get_websocket_controller),
    current_user: UserInDB = Depends(get_current_user_ws)
):
    await controller.process_chat_connection(websocket, chat_id, current_user) 