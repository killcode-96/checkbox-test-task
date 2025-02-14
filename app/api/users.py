from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import db
from app.schemas import user as user_schemas
from app.core.security import (
    create_access_token,
    decode_token,
)
from app.core.config import settings
from app.services.user import UserService

router = APIRouter()
oauth2_scheme = HTTPBearer()


def get_user_service(db: AsyncSession = Depends(db.get_db)) -> UserService:
    return UserService(db)


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token.credentials)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


@router.post(
    "/signup/",
    response_model=user_schemas.User,
    summary="Реєстрація користувача",
    description="Реєстрація користувача вказавши ім'я, логін та пароль",
)
async def create_user(
    user: user_schemas.UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.create_user(user)


@router.post(
    "/signin/",
    response_model=user_schemas.Token,
    summary="Вхід користувача",
    description="Вхід користувача вказавши логін та пароль для отримання JWT токена",
)
async def login_for_access_token(
    form_data: user_schemas.TokenRequestForm,
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.authenticate_user(form_data)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return user_schemas.Token(access_token=access_token, token_type="bearer")
