import asyncio
import json
import re
import traceback
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from langchain_core.messages import AIMessage

from app.utils.logger import get_logger
from app.utils.mk_2_json import markdown_to_json
from app.models.db_models import Note, StudyPlan
from app.core.dependencies import method_logger


logger = get_logger(__name__)


class StudyPlanService:

    @method_logger
    async def create_study_plan_from_ai_response(
        self,
        db: AsyncSession,
        ai_response: str,
    ) -> StudyPlan:
        """
        创建学习计划

        Args:
            self: cls
            db: 数据库连接实例
            ai_response: 大模型返回的内容

        Retrun:
            StudyPlan: 创建好的学习计划
        """

        try:
            logger.info("从AI的响应结果提取信息并输出成json")
            ai_json_output = markdown_to_json(ai_response)
            data = json.loads(ai_json_output)
            # 计算时间范围
            total_days = data["total_days"]
            if re.match(r"\d+天", data["total_days"]):
                total_days = int(data["total_days"].replace("天", "").strip())
            start_time = datetime.now()
            end_time = start_time + timedelta(days=total_days)

            # 创建主学习计划
            logger.info("创建学习计划")
            study_plan = StudyPlan(
                title=data["title"],
                content=data["content"],
                goal=data["specific_goals"],
                total_days=total_days,
                start_time=start_time,
                end_time=end_time,
                user_id=1
            )

            db.add(study_plan)
            await db.flush()
            logger.info("创建学习计划完成")
            logger.info("为每天创建笔记模板")
            for day_plan in data["daily_plans"]:
                day_start = start_time + timedelta(days=day_plan["day"]-1)
                note_create = Note(
                    study_plan_id=study_plan.id,
                    study_content=f"# {day_plan['topic']}\n\n## 今日学习要点：\n" +
                    "\n".join(
                        [f"- {point}" for point in day_plan["key_points"]]),
                    detailed_content="",  # 留空供用户填写笔记
                    note_content="",  # 留空供用户填写笔记
                    planned_study_start_time=day_start,
                    actual_study_start_time=None,
                    is_completed=False
                )
                db.add(note_create)
            logger.info("笔记模板创建完成")
            return study_plan
        except Exception as e:
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=400, detail=f"Error parsing AI response: {str(e)}")

    @method_logger
    async def get_user_study_plans(self, db: AsyncSession, user_id: int) -> List[StudyPlan]:
        """
        获取某用户下面的全部学习计划

        Args:
            self: cls
            db: 数据库连接实例
            user_id: 用户id

        Return
            List[StudyPlan] : 学习计划的List
        """
        stm = select(StudyPlan).where(StudyPlan.user_id == user_id)
        result = await db.execute(stm)
        return result.scalars().all()

    @method_logger
    async def get_study_plan(self, db: AsyncSession, plan_id: int) -> Optional[StudyPlan]:
        """
        获取学习计划

        Args:
            self: cls
            db: 数据库连接实例
            plan_id: 要获取的学习计划的ID

        Returs:
            StudyPlan|None : plan_id对应的StudyPlan。如果没有获取到，返回None。
        """
        stm = select(StudyPlan).where(StudyPlan.id == plan_id)
        result = await db.execute(stm)
        return result.scalars().one_or_none()

    @method_logger
    async def ge_study_plan_event_stream(self, state, graph, db, sessions, session_id, vector_store, chroma):
        """
        生成学习计划

        Args:
            self: cls
            state: graph中的state
            graph: graph实例
            db: 数据库连接实例
            sessions: fastapi的全局变量sessions
            ession_id: 代表当前回话的唯一的ID
            vector_store: 向量存储的实例
            chroma: chroma的实例

        """
        # 边运行边 yield 事件
        config = {"configurable": {"thread_id": session_id,
                                   "db_session": db,
                                   "vector_store": vector_store,
                                   "chroma": chroma}}
        output_text = ""

        # 让 checkpointer 自动处理状态恢复，我们只需要传递新消息
        logger.info(
            f"开始执行，当前状态: {state.get('status', 'unknown')}", session_id=session_id)
        # 使用 astream 执行，checkpointer 会自动从检查点恢复状态
        async for event in graph.astream(state, config=config):
            for node_name, partial_state in event.items():
                logger.info(f"执行节点名称:{node_name}", session_id=session_id)
                if "messages" in partial_state and isinstance(partial_state["messages"][-1], AIMessage):
                    output_text = partial_state["messages"][-1].content

            logger.info("实时保存状态")
            try:
                await asyncio.sleep(0.1)
                current_state = graph.get_state(config)
                if current_state.values:
                    sessions[session_id] = current_state.values
                    logger.info(f"保存状态: {current_state.values.get('status')}")
            except Exception as e:
                logger.info(f"状态保存失败: {e}")

            if output_text:
                yield output_text
                break


# Global instance
study_plan_service = StudyPlanService()
