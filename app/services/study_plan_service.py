import json
from typing import List, Optional, AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.study_plan import  StudyPlanCreate
from app.models.db_models import Note, StudyPlan
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.llm.ai_service import ai_service
from app.tools.mk_2_json import markdown_to_json


class AIStudyRequest(BaseModel):
    subject: str
    total_days: int
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced
    prior_knowledge: str = ""
    specific_goals: str = ""
    user_id: int


class StudyPlanService:

    def _generate_system_prompt(self) -> str:
        """生成系统提示词"""
        system_prompt = """
            你是一个专业的教育顾问，请根据用户输入的内容（包括主题、计划天数、难度级别、已有知识背景、具体学习目标），制定一个学习计划。
            请确保：
            1. 知识点循序渐进，由浅入深
            2. 每天的学习内容适量，考虑学习者的接受能力
            3. 知识点之间有合理的联系
            4. 每天的主题明确，知识点具体
            5. 知识点应当可操作和可实践
            
            
            """
        return system_prompt

    def _generate_user_prompt(self, request: AIStudyRequest) -> str:
        """生成用户提示词"""

        user_prompt = f"""
            主题：{request.subject}
            计划天数：{request.total_days}天
            难度级别：{request.difficulty_level}
            已有知识背景：{request.prior_knowledge}
            具体学习目标：{request.specific_goals}
            我是一个中文用户，请用中文回答我的问题。
            请根据以上内容，为我设定一个学习计划。
            在输出时，请按照以下格式提供学习计划,其他无关内容不要输出：
            
            ### 学习主题: 学习的主题
            ### 学习计划描述:
                总体学习概述
            ### 学习计划大纲
            **第n天(n从1开始)**
            * 学习内容:当天主要学习主题 
            * 学习知识点:
            1 关键知识点1
            2 关键知识点2
            3 关键知识点3
            4 ......
  
        """
        return user_prompt

    async def generate_study_plan(self, request: AIStudyRequest) -> str:
        """使用AI生成学习计划"""
        system_prompt = self._generate_system_prompt()
        user_prompt = self._generate_user_prompt(request)
        response = await ai_service.generate_response(system_prompt, user_prompt)
        return response.content

    async def generate_study_plan_stream(self, request: AIStudyRequest) -> AsyncGenerator[str, None]:
        """使用AI生成学习计划（流式返回）"""
        system_prompt = self._generate_system_prompt()
        user_prompt = self._generate_user_prompt(request)
        async for chunk in ai_service.generate_stream_response(system_prompt, user_prompt):
            yield chunk

    async def create_study_plan_with_ai(
        self,
        db: AsyncSession,
        request: AIStudyRequest
    ) -> StudyPlan:
        """使用AI生成并创建学习计划"""
        ai_response = await self.generate_study_plan(request)
        ai_json_output = markdown_to_json(ai_response)
        return await self.create_study_plan_from_ai_response(db, ai_json_output, request)

    async def create_study_plan_from_ai_response(
        self,
        db: AsyncSession,
        ai_response: str,
        request: AIStudyRequest
    ) -> StudyPlan:
        """从AI响应创建学习计划"""
        try:
            data = json.loads(ai_response)

            # 计算时间范围
            start_time = datetime.now()
            end_time = start_time + timedelta(days=request.total_days)

            # 创建主学习计划
            study_plan = StudyPlan(
                title=data["title"],
                content=data["content"],
                goal=request.specific_goals,
                total_days=request.total_days,
                start_time=start_time,
                end_time=end_time,
                user_id=request.user_id
            )

            
            db.add(study_plan)
            await db.flush()

            # 为每天创建笔记模板

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
            

            return study_plan
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            raise HTTPException(
                status_code=400, detail=f"Error parsing AI response: {str(e)}")

    def create_study_plan(self, db: AsyncSession, study_plan: StudyPlanCreate, user_id: int) -> StudyPlan:
        db_study_plan = StudyPlan(
            title=study_plan.title,
            content=study_plan.content,
            start_time=study_plan.start_time,
            end_time=study_plan.end_time,
            user_id=user_id
        )
        try:
            db.add(db_study_plan)
            db.commit()
            db.refresh(db_study_plan)
            return db_study_plan
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400, detail="Error creating study plan")

    async def get_user_study_plans(self, db: AsyncSession, user_id: int) -> List[StudyPlan]:
        stm = select(StudyPlan).where(StudyPlan.user_id == user_id)
        result = await db.execute(stm)
        return result.scalars().all()

    async def get_study_plan(self, db: AsyncSession, plan_id: int) -> Optional[StudyPlan]:
        stm = select(StudyPlan).where(StudyPlan.id == plan_id)
        result = await db.execute(stm)
        return result.scalars().one_or_none()


# Global instance
study_plan_service = StudyPlanService()
