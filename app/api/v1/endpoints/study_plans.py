from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage
from app.db.session import get_session
from app.models.study_plan import StudyPlanResponse
from app.services.study_plan_service import study_plan_service
from app.core.dependencies import method_logger
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@method_logger
@router.get("/user/{user_id}", response_model=List[StudyPlanResponse])
async def get_user_study_plans(user_id: int, db: AsyncSession = Depends(get_session)):
    """
    获取该用户下面的全部学习计划

    Args:
        user_id: 登陆的用户ID
        db: 数据库连接实例

    Return:
        list: 该用户下的全部学习计划list

    """
    return await study_plan_service.get_user_study_plans(db, user_id)


@method_logger
@router.get("/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(plan_id: int, db: AsyncSession = Depends(get_session)):
    """
    获取某一个计划的详细信息

    Args:
        plan_id: 学习计划的ID
        db: 数据库连接实例

    Retrun:
       StudyPlan:  学习计划信息
    """
    study_plan = await study_plan_service.get_study_plan(db, plan_id)
    if study_plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return study_plan


@method_logger
@router.post("/gen_plan_by_graph")
async def gen_plan_by_graph(request: Request, session_id: str, text: str, db: AsyncSession = Depends(get_session)):
    """
    通过多轮对话，生成学习计划

    Args:
        request: request请求
        session_id: 当前回话的唯一表示（前端生成的）
        text: 用户输入的聊天内容
        db: 数据库连接实例
    Retrun:
        StreamingResponse: AI回复的内容的流
    """
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

    return StreamingResponse(study_plan_service.ge_study_plan_event_stream(state, graph, db, sessions, session_id, vector_store, chroma), media_type="text/event-stream")
