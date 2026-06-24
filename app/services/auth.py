from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.database.models import User
from app.repositories.users import UserRepository
from app.schemas.auth import TokenResponse, UserRegister
from app.unit_of_work import UnitOfWork


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register(self, user_data: UserRegister) -> User:
        async with UnitOfWork(self.session) as uow:
            email = user_data.email.lower()
            existing_user = await uow.users.get_by_email(email)

            if existing_user is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )

            user = User(
                email=email,
                password_hash=hash_password(user_data.password),
            )
            user = await uow.users.add(user)
            await uow.commit()

            return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email.lower())

        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.authenticate(email, password)
        token = create_access_token(user.id)

        return TokenResponse(access_token=token, token_type="bearer")
