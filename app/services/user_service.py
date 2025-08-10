from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from app.models.user import UserCreate, UserUpdate
from app.models.db_models import User
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalars().one_or_none()

    async def create_user(self, db: AsyncSession, user_create: UserCreate) -> User:
        # Check if username or email already exists
        if await self.get_user_by_username(db, user_create.username):
            raise HTTPException(
                status_code=400, detail="Username already registered")
        if await self.get_user_by_email(db, user_create.email):
            raise HTTPException(
                status_code=400, detail="Email already registered")

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

    async def update_user(self, db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
        db_user = await self.get_user_by_id(db, user_id)
        if not db_user:
            return None
        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = self.get_password_hash(
                update_data.pop("password"))

        for field, value in update_data.items():
            setattr(db_user, field, value)
        await db.refresh(db_user, ["updated_at"])
        return db_user

    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        user = await self.get_user_by_username(db, username)
        print(user.__dict__)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user


# Global instance
user_service = UserService()
