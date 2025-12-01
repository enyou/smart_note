from typing import List
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage
from app.db.session import get_session
from app.models.study_plan import GenStudyPlanBase, StudyPlanAiResp, StudyPlanResponse
from app.services.study_plan_service import study_plan_service, AIStudyRequest
from app.core.dependencies import method_logger
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()
sessions = {}


@method_logger
@router.get("/user/{user_id}", response_model=List[StudyPlanResponse])
async def get_user_study_plans(user_id: int, db: AsyncSession = Depends(get_session)):
    """获取该用户下面的全部学习计划"""
    return await study_plan_service.get_user_study_plans(db, user_id)


@method_logger
@router.get("/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(plan_id: int, db: AsyncSession = Depends(get_session)):
    """获取某一个计划的详细信息"""
    study_plan = await study_plan_service.get_study_plan(db, plan_id)
    if study_plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return study_plan


@router.post("/generate-stream")
async def generate_study_plan_stream(
    plan_needs: GenStudyPlanBase
):
    """使用AI生成学习计划（流式返回）"""
    "计划废止"
    # 信息提取
    info = await study_plan_service.get_import_infor(plan_needs.msg)
    info["user_id"] = 1
    request = AIStudyRequest.model_validate(info)

    async def generate():
        try:
            async for chunk in study_plan_service.generate_study_plan_stream(request):
                yield chunk
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
    "计划废止"
    return await study_plan_service.create_study_plan_with_ai(db, request)


@router.post("/gen_study_plan")
async def gen_study_plan(
    request: AIStudyRequest
):
    """使用AI生成学习计划(非流式返回)"""
    "计划废止"
    return await study_plan_service.generate_study_plan(request)


@router.post("/save_plan", response_model=StudyPlanResponse)
async def save_plan(
    ai_response: StudyPlanAiResp,
    db: AsyncSession = Depends(get_session)
):
    """在页面中新建学习计划对应的API"""
    "计划废止"
    return await study_plan_service.create_study_plan_from_ai_response(db, ai_response.ai_response)


@method_logger
@router.post("/gen_plan_by_graph")
async def gen_plan_by_graph(request: Request, session_id: str, text: str, db: AsyncSession = Depends(get_session)):
    # 获取或初始化 state
    logger.info("获取或初始化state")
    logger.info(f"当前的session id:{session_id}")
    sessions = request.app.state.sessions
    graph = request.app.state.graph
    vector_store = request.app.state.vector_store
    chroma = request.app.state.chroma
    state = {}
    if session_id not in sessions:
        logger.info(f"这是一个新的会话")
        state = {
            "learned_before": None,
            "want_deep_learn": None,
            "learning_plan": None,
            "is_satisfied": None,
            "input_completeness": None,
            "status": "start",
            "subject": text,
            "messages": [HumanMessage(content=text)],
        }
        logger.info(f"当前status:start")
    else:
        state = sessions.get(session_id)
        logger.info(f"当前status:{state.get("status", "未获取")}")
        if not state["input_completeness"]:
            state["subject"] = text
        state["messages"].append(HumanMessage(content=text))

    return StreamingResponse(study_plan_service.event_stream(state, graph, db, sessions, session_id, vector_store, chroma), media_type="text/event-stream")
