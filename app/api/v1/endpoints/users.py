from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import UserMessages
from app.db.session import get_session
from app.models.user import UserCreate, UserResponse, UserPwdUpdate, UserLogin, Token
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
@router.post("/", response_model=UserResponse, include_in_schema=False)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_session)):
    """
    注册用户

    Args:
        user: 注册的用户信息
        db: 数据库实例连接

    Return:
        User: 注册的用户对象实例
    """
    return await user_service.create_user(db, user)


@method_logger
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_session)):
    """
    获取登陆的用户信息

    Args:
        user_id: 用户ID
        db: 数据库实例连接

    Return:
        User: 这个用户ID的对象实例
    """
    db_user = await user_service.get_user_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(
            status_code=401, detail=UserMessages.USER_NOT_FOUND)
    return db_user


@method_logger
@router.put("/{user_id}", response_model=UserResponse)
async def update_user_pwd(user_pwd_upt: UserPwdUpdate, db: AsyncSession = Depends(get_session)):
    """
    更新用户密码

    Args:
        user_pwd_upt: 包含输入用户id和新密码的UserPwdUpdate实例
        db: 数据库实例连接

    Return:
        User:  更新后的用户

    """
    if user_pwd_upt.new_password != user_pwd_upt.again_new_password:
        raise (HTTPException(status_code=400, detail=UserMessages.PWD_DIFF))
    db_user = await user_service.update_user_pwd(db, user_pwd_upt)
    if db_user is None:
        raise HTTPException(
            status_code=401, detail=UserMessages.USER_NOT_FOUND)
    return db_user


@method_logger
@router.post("/login", response_model=Token, include_in_schema=False)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_session)):
    """
    用户登陆

    Argas:
        user_credentials: 用户名和密码信息
        db: 数据库实例

    Return:
        dict: token
    """
    user = await auth_service.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UserMessages.USER_OR_PWD_INCORRECT,
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
    """
    用户退出登陆

    Args:
        credentials: token

    Retrun:
        dict: 退出成功的消息
    """
    # In a stateless JWT system, logout is typically handled client-side by removing the token
    # However, we can implement a token blacklist or simply return a success message
    return {"message": "Successfully logged out"}


@method_logger
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取跟人信息

    Args:
        current_user: 用户信息

    Retrun:
        User: 用户信息
    """
    return current_user
