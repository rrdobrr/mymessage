from fastapi import APIRouter, Depends, status
from src.features.users.dependencies import get_user_service
from src.features.users.schemas import UserCreate, UserUpdate, UserInDB
from src.features.auth.dependencies import get_current_user

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserInDB)
async def read_current_user(
    current_user: UserInDB = Depends(get_current_user)
):
    """Получение информации о текущем пользователе"""
    return current_user


@router.get("/list", response_model=list[UserInDB])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    user_service = Depends(get_user_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Получение списка пользователей"""
    return await user_service.get_users(skip, limit)


@router.get("/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: int,
    user_service = Depends(get_user_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Получение информации о пользователе"""
    return await user_service.get_user(user_id)


@router.patch("/{user_id}/update", response_model=UserInDB)
async def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    user_service = Depends(get_user_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Обновление данных пользователя"""
    return await user_service.update_user(user_id, user_update, current_user)


@router.delete("/{user_id}/delete", response_model=UserInDB)
async def delete_user_account(
    user_id: int,
    user_service = Depends(get_user_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Удаление пользователя"""
    return await user_service.delete_user(user_id, current_user)