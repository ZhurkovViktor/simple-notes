from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_session
from app.database.models import User
from app.schemas.auth import TokenResponse, UserRegister, UserResponse
from app.services.auth import AuthService


router = APIRouter(prefix="/api/v1", tags=["Auth"])


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_session),
) -> User:
    service = AuthService(session)
    return await service.register(user_data)


@router.post("/auth/token", response_model=TokenResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    service = AuthService(session)
    return await service.login(form_data.username, form_data.password)


@router.get("/users/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
