#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: models.py
功能: 数据库的models文件
作者: Yang
创建日期: 2025-07-22
版本号: 1.0
变更说明: 无
"""
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy import JSON, Column, Integer, String, DateTime, ForeignKey, Text, Boolean


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    study_plan_id = Column(Integer, ForeignKey(
        "study_plans.id"), nullable=False)
    actual_study_start_time = Column(DateTime(timezone=True))  # 实际学习开始时间
    planned_study_start_time = Column(DateTime(timezone=True))  # 计划学习开始时间
    study_content = Column(Text, nullable=False)  # 学习内容概要
    detailed_content = Column(Text)  # 详细的学习内容
    note_content = Column(Text)  # 笔记内容
    is_completed = Column(Boolean, default=False)  # 是否完成
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    study_plan = relationship("StudyPlan", back_populates="notes")

class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    goal = Column(Text, nullable=True)
    total_days = Column(Integer)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default='now()')

    # 关系
    user = relationship("User", back_populates="study_plans")
    notes = relationship("Note", back_populates="study_plan")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    study_plans = relationship("StudyPlan", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)  # 会话ID
    user_message = Column(String)  # 用户消息
    ai_message = Column(String)    # AI回复
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    metadata_data = Column(JSON)        # 额外元数据
