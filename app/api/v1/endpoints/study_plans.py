from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from app.db.session import get_session
from app.models.study_plan import StudyPlanCreate, StudyPlanResponse
from app.services.study_plan_service import study_plan_service, AIStudyRequest

router = APIRouter()


@router.get("/user/{user_id}", response_model=List[StudyPlanResponse])
async def get_user_study_plans(user_id: int, db: AsyncSession = Depends(get_session)):
    """获取该用户下面的全部学习计划"""
    return await study_plan_service.get_user_study_plans(db, user_id)


@router.get("/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(plan_id: int, db: AsyncSession = Depends(get_session)):
    """获取某一个计划的详细信息"""
    study_plan = await study_plan_service.get_study_plan(db, plan_id)
    if study_plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return study_plan


@router.post("/generate-stream")
async def generate_study_plan_stream(
    request: AIStudyRequest
):
    """使用AI生成学习计划（流式返回）"""
    async def generate():
        try:
            async for chunk in study_plan_service.generate_study_plan_stream(request):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            import traceback
            yield f"data: {json.dumps({'error': traceback.format_exc()})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/create-with-ai", response_model=StudyPlanResponse)
async def create_study_plan_with_ai(
    request: AIStudyRequest,
    db: AsyncSession = Depends(get_session)
):
    """在页面中新建学习计划对应的API"""
    return await study_plan_service.create_study_plan_with_ai(db, request)


@router.post("/gen_study_plan")
async def gen_study_plan(
    request: AIStudyRequest
):
    """使用AI生成学习计划(非流式返回)"""
    return await study_plan_service.generate_study_plan(request)
