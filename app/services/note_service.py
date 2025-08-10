import asyncio
from copy import deepcopy
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.messages import CommonMessages, ErrorMessages
from app.models.note import NoteUpdate
from app.models.db_models import Note
from app.services.study_plan_service import study_plan_service
from app.llm.ai_service import ai_service


class NoteService:

    async def get_note(self, db: AsyncSession, note_id: int) -> Optional[Note]:
        """获取点击的note"""
        stm = select(Note).where(Note.id == note_id)
        result = await db.execute(stm)
        note = result.scalars().one_or_none()
        if not note.actual_study_start_time:
            stm = update(Note).where(Note.id == note.id).values(
                actual_study_start_time=datetime.now()).returning(Note)
            result = await db.execute(stm)
            note = result.scalars().one_or_none()
        return note

        # return await self.generate_detailed_content(db, note)

    async def get_study_plan_notes(self, db: AsyncSession, study_plan_id: int) -> List[Note]:
        """获取该学习计划下面的全部notes"""
        stm = select(Note).where(Note.study_plan_id == study_plan_id)
        result = await db.execute(stm)
        return result.scalars().all()

    async def update_note(self, db: AsyncSession, note_id: int, note_update: NoteUpdate) -> Optional[Note]:
        db_note = await self.get_note(db, note_id)
        if not db_note:
            return None

        update_data = note_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_note, field, value)
        await db.refresh(db_note, ["updated_at"])
        return db_note

    async def get_currend_day_notes(self, db: AsyncSession) -> List[Note]:
        """获取当天应该要学习的笔记"""
        cte = select(Note,
                     func.row_number().over(
                         partition_by=Note.study_plan_id,
                         order_by=Note.planned_study_start_time
                     ).label("row_num")
                     ).where(Note.actual_study_start_time.is_(None)
                             ).cte("numbers_notes")
        stm = select(Note).select_from(cte).where(cte.c.id == Note.id).where(
            cte.c.row_num == 1).options(selectinload(Note.study_plan))
        result = await db.execute(stm)
        notes = result.scalars().all()
        return notes

    async def generate_detailed_content(self, db: AsyncSession, note_id: int):
        """生成笔记的详细学习内容"""
        gen_success_flg = True
        try:
            stm = select(Note).where(Note.id == note_id)
            result = await db.execute(stm)
            note = result.scalars().one_or_none()
            # 获取该学习计划的所有笔记，用于构建学习上下文
            all_notes = await self.get_study_plan_notes(db, note.study_plan_id)
            previous_notes = [
                n for n in all_notes if n.planned_study_start_time < note.planned_study_start_time]
            # 获取学习计划信息
            study_plan = await study_plan_service.get_study_plan(db, note.study_plan_id)
            # 构建提示词
            if len(previous_notes) > 5:
                sys_prompt = self._gen_system_prompt(
                    previous_notes[-5::], study_plan)
            else:
                sys_prompt = self._gen_system_prompt(
                    previous_notes, study_plan)
            user_prompt = self._gen_user_prompt(note)

            # 调用AI生成详细内容
            chunks = []
            async for chunk in ai_service.generate_stream_response(sys_prompt, user_prompt):
                chunks.append(chunk)
                yield chunk
            
        except Exception as e:
            gen_success_flg = False
            yield ErrorMessages.LLM_CALLING_ERROR
        finally:
            if gen_success_flg:
                # 更新笔记的详细内容
                stm = update(Note).where(Note.id == note.id).values(detailed_content="".join(chunks),
                                                                    actual_study_start_time=datetime.now(),
                                                                    is_completed=True).returning(Note)
                result = await db.execute(stm)
                yield CommonMessages.LLM_PROCESS_FINISH

    def _get_knowledge_points(self, previous_notes: List[Note]):
        """获取之前每日学习的知识点
            从格式化的文本中提取每日学习要点
            返回知识点列表
        """

        knowledge_points = []
        for note in previous_notes:
            if not note.study_content:
                continue
            text = note.study_content
            # 按行分割文本
            lines = text.split('\n')
            for line in lines:
                # 如果处于知识点区域且是知识点行
                if line.strip().startswith("-"):
                    # 去除开头的"- "和可能的空格
                    point = line.strip()[2:].strip()
                    knowledge_points.append(point)
        return knowledge_points

    def _gen_system_prompt(self, previous_notes: List[Note], study_plan) -> str:
        """构建system提示词"""
        # 构建之前学习过的内容摘要
        previous_content = "这是第一天的学习内容"
        knowledge_points = self._get_knowledge_points(previous_notes)
        if knowledge_points:
            previous_content = ",".join(knowledge_points)

        prompt = f"""作为一个专业的教育顾问，为了能够达到学习计划的总体目标，请为今天要学习的知识点生成详细的学习指南。
                    同时请根据之前学习过的内容，在本内容开始之前，对之前学习过的内容展开简要的复习。
                    学习计划总体目标：
                    {study_plan.content}

                    之前已学习的内容：
                    {previous_content}

                    请按照以下结构提供详细的学习内容：

                    1. 知识点复习
                    - 针对每个要复习的知识点，给出简要的说明
                    - 针对说明给出实例的例子

                    2. 核心概念详解
                    - 为每个知识点提供清晰的定义和解释
                    - 包含实际的例子和应用场景
                    - 指出常见的误解和注意事项

                    3. 实践练习
                    - 针对每个知识点设计练习题
                    - 提供实际操作的小项目或任务
                    - 包含练习的参考答案或解决方案

                    4. 知识点关联
                    - 说明与之前学习内容的联系
                    - 解释知识点之间的关系
                    - 指出在未来学习中的应用

                    5. 今日复习重点
                    - 总结当天的关键知识点
                    - 提供快速复习的方法
                    - 设计复习检查清单

                    6. 扩展资源
                    - 推荐进一步学习的材料
                    - 相关的在线资源或工具
                    - 补充阅读建议

                    请确保内容具体、实用，并且易于理解和操作。重点关注知识的实际应用和与之前学习内容的联系。
             """

        return prompt

    def _gen_user_prompt(self, current_note) -> str:
        """生成用户提示词"""
        knowledge_points = self._get_knowledge_points([current_note])
        topics = ",".join(knowledge_points)
        prompt = f"""
                今天将要学习的知识点如下：
                   {topics}

                请用中文给我一个详细的学习指南。
                """
        return prompt


# Global instance
note_service = NoteService()
