from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db.session import get_session
from app.models.user import UserCreate, UserResponse, UserUpdate, UserLogin, Token
from app.models.db_models import User
from app.services.user_service import user_service
from app.services.auth_service import auth_service
from app.core.config import settings
from app.core.dependencies import get_current_user

from app.core.dependencies import method_logger
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


@method_logger
@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_session)):
    return await user_service.create_user(db, user)


@method_logger
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_session)):
    db_user = await user_service.get_user_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@method_logger
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, db: AsyncSession = Depends(get_session)):
    db_user = await user_service.update_user(db, user_id, user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@method_logger
@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_session)):
    user = await auth_service.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@method_logger
@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In a stateless JWT system, logout is typically handled client-side by removing the token
    # However, we can implement a token blacklist or simply return a success message
    return {"message": "Successfully logged out"}


@method_logger
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
