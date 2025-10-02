from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.api.dependencies import get_current_user
from co_sim.db.session import get_db
from co_sim.models.user import User
from co_sim.schemas.auth import TokenResponse
from co_sim.schemas.user import UserCreate, UserRead
from co_sim.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, session: Annotated[AsyncSession, Depends(get_db)]) -> UserRead:
    try:
        return await auth_service.register_user(session, payload)
    except auth_service.UserAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user_data = await auth_service.authenticate_user(session, form_data.username, form_data.password)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    _, token, expires_in = user_data
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return UserRead.model_validate(current_user)
