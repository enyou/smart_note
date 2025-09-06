#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: study_plan.py
功能: 学习计划的Pydantic Models
作者: Yang
创建日期: 2025-07-22
版本号: 1.0
变更说明: 无
"""


from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Pydantic Models
class StudyPlanBase(BaseModel):
    title: str
    content: str
    goal: Optional[str]
    total_days: int
    start_time: datetime
    end_time: datetime

# Pydantic Models
class GenStudyPlanBase(BaseModel):
    msg: str
    user_id: str

class StudyPlanCreate(StudyPlanBase):
    pass


class StudyPlanInDB(StudyPlanBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StudyPlanResponse(StudyPlanInDB):
    pass


class StudyPlanTitle(BaseModel):
    id: int
    title: str

# Pydantic Models
class StudyPlanAiResp(BaseModel):
    ai_response: str