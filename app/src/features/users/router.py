from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.features.auth.dependencies import get_current_user
from src.features.users.crud import (
    get_user,
    get_users,
    create_user,
    update_user,
    delete_user
)
from src.features.users.schemas import UserCreate, UserUpdate, UserInDB

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/list", response_model=list[UserInDB])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    return await get_users(db, skip, limit)

@router.get("/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}/update", response_model=UserInDB)
async def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await update_user(db, user, user_update)

@router.delete("/{user_id}/delete", response_model=UserInDB)
async def delete_user_account(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await delete_user(db, user)