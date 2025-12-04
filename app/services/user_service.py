from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from fastapi import HTTPException
from app.core.dependencies import method_logger
from app.core.messages import UserMessages
from app.models.user import UserCreate, UserPwdUpdate
from app.models.db_models import User
from app.utils.logger import get_logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger(__name__)


class UserService:

    @method_logger()
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    @method_logger()
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @method_logger()
    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalars().first()

    @method_logger()
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    @method_logger()
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalars().one_or_none()

    @method_logger()
    async def create_user(self, db: AsyncSession, user_create: UserCreate) -> User:
        # Check if username or email already exists
        if user_create.password != user_create.again_password:
            raise (HTTPException(status_code=400, detail=UserMessages.PWD_DIFF))
        if await self.get_user_by_username(db, user_create.username):
            raise HTTPException(
                status_code=400, detail=UserMessages.USERNAME_EXIST)
        if await self.get_user_by_email(db, user_create.email):
            raise HTTPException(
                status_code=400, detail=UserMessages.EMAIL_EXIST)

        hashed_password = self.get_password_hash(user_create.password)
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=hashed_password
        )

        db.add(db_user)
        await db.flush()
        return db_user

    @method_logger()
    async def update_user_pwd(self, db: AsyncSession, user_pwd_upt: UserPwdUpdate) -> Optional[User]:
        db_user = await self.get_user_by_id(db, user_pwd_upt.user_id)
        if not db_user:
            return None

        hashed_pwd = self.get_password_hash(user_pwd_upt.new_password)
        db_user.hashed_password = hashed_pwd

        await db.commit()
        await db.refresh(db_user)
        return db_user

    @method_logger()
    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        user = await self.get_user_by_username(db, username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user


# Global instance
user_service = UserService()
