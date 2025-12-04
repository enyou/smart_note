#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: user.py
功能: Pydantic Models
作者: Yang
创建日期: 2025-07-22
版本号: 1.0
变更说明: 无
"""


from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    again_password: str


class UserPwdUpdate(BaseModel):
    user_id: int
    new_password: str
    again_new_password: str


class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    pass


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
