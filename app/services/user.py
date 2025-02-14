from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app.schemas import user as user_schemas
from app.core.security import get_password_hash, verify_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: user_schemas.UserCreate) -> models.User:
        """Registers a new user."""
        existing_user_result = await self.db.execute(
            select(models.User).where(models.User.username == user.username)
        )
        existing_user = existing_user_result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def authenticate_user(
        self, form_data: user_schemas.TokenRequestForm
    ) -> models.User:
        """Authenticates a user and returns the user object."""
        result = await self.db.execute(
            select(models.User).where(models.User.username == form_data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def get_user_by_username(self, username: str) -> models.User | None:
        """Retrieves a user by username."""
        result = await self.db.execute(
            select(models.User).where(models.User.username == username)
        )
        return result.scalar_one_or_none()
