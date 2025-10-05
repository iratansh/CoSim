from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from co_sim.api.dependencies import get_current_user
from co_sim.db.session import get_db
from co_sim.models.user import User
from co_sim.schemas.auth import TokenResponse
from co_sim.schemas.user import UserCreate, UserRead
from co_sim.services import auth as auth_service
from co_sim.services.auth0 import get_current_user_auth0
from co_sim.services.token import create_access_token

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


@router.post("/auth0/exchange", response_model=TokenResponse)
async def exchange_auth0_token(
    auth0_user: Annotated[dict, Depends(get_current_user_auth0)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Exchange an Auth0 JWT for a CoSim backend JWT.
    Creates a new user in the database if one doesn't exist.
    """
    auth0_id = auth0_user.get("sub")
    email = auth0_user.get("email")
    
    if not auth0_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Auth0 token: missing sub or email",
        )
    
    # Look for existing user by Auth0 ID (stored in email or a dedicated field)
    # For now, we'll use email as the lookup
    result = await session.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    
    # Create user if doesn't exist
    if not user:
        user = User(
            email=email.lower(),
            full_name=auth0_user.get("name") or auth0_user.get("nickname"),
            hashed_password="",  # Auth0 users don't have passwords in our system
            is_active=True,
            plan="free",  # Default plan for new Auth0 users
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    # Generate our backend JWT
    token, expires_in = create_access_token(subject=user.id)
    
    return TokenResponse(access_token=token, expires_in=expires_in)
