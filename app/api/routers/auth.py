from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.database.models import User
from app.schemas.auth import UserResponse


router = APIRouter(prefix="/api/v1", tags=["Users"])


@router.get("/users/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
