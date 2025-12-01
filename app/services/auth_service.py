from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.services.user_service import user_service
from app.core.dependencies import method_logger
from app.utils.logger import get_logger


logger = get_logger(__name__)

security = HTTPBearer()


class AuthService:

    @method_logger
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @method_logger
    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY,
                                 algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None

    @method_logger
    async def authenticate_user(self, db: AsyncSession, username: str, password: str):
        user = await user_service.authenticate_user(db, username, password)
        if not user:
            return None
        return user

    @method_logger
    async def get_current_user(self, db: AsyncSession, token: str):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        username = self.verify_token(token)
        if username is None:
            raise credentials_exception
        user = await user_service.get_user_by_username(db, username)
        if user is None:
            raise credentials_exception
        return user


# Global instance
auth_service = AuthService()
