from fastapi import APIRouter, Depends
from src.features.auth.dependencies import get_current_user
from src.features.users.schemas import UserInDB

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user