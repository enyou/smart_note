from datetime import datetime
import traceback
from typing import List, Optional
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.messages import CommonMessages, ErrorMessages
from app.llm.prompts.gen_note_detail_prompt import GenNoteDetailPrompt
from app.models.note import NoteUpdate
from app.models.db_models import Note
from app.services.study_plan_service import study_plan_service
from app.llm.ai_service import ai_service
from app.core.dependencies import method_logger
from app.utils.logger import get_logger


logger = get_logger(__name__)


class NoteService:

    @method_logger
    async def get_note(self, db: AsyncSession, note_id: int) -> Optional[Note]:
        """
        获取note信息

        Args:
            self: cls
            db: 数据库连接实例
            note_id: note id

        Retrun:
           Note: node_id对应的note信息
        """
        stm = select(Note).where(Note.id == note_id)
        result = await db.execute(stm)
        note = result.scalars().one_or_none()
        if not note.actual_study_start_time:
            stm = update(Note).where(Note.id == note.id).values(
                actual_study_start_time=datetime.now()).returning(Note)
            result = await db.execute(stm)
            note = result.scalars().one_or_none()
        return note

    @method_logger
    async def get_study_plan_notes(self, db: AsyncSession, study_plan_id: int) -> List[Note]:
        """
        获取某一学习计划下面的全部note

        Args:
            self: cls
            db: 数据库连接实例
            study_plan_id: 学习计划id

        Return:
            List[Note]: study_plan_id下的全部笔记
        """
        stm = select(Note).where(Note.study_plan_id == study_plan_id)
        result = await db.execute(stm)
        return result.scalars().all()

    @method_logger
    async def update_note(self, db: AsyncSession, note_id: int, note_update: NoteUpdate) -> Optional[Note]:
        db_note = await self.get_note(db, note_id)
        if not db_note:
            return None

        update_data = note_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_note, field, value)
        await db.refresh(db_note, ["updated_at"])
        return db_note

    @method_logger
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

    @method_logger
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
            logger.error(traceback.format_exc())
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

    @method_logger
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

    @method_logger
    def _gen_system_prompt(self, previous_notes: List[Note], study_plan) -> str:
        """构建system提示词"""
        # 构建之前学习过的内容摘要
        previous_content = "这是第一天的学习内容"
        knowledge_points = self._get_knowledge_points(previous_notes)
        if knowledge_points:
            previous_content = ",".join(knowledge_points)

        prompt = GenNoteDetailPrompt.SYS_PROMPT.format(study_plan_content=study_plan.content,
                                                       previous_content=previous_content)
        return prompt

    @method_logger
    def _gen_user_prompt(self, current_note) -> str:
        """生成用户提示词"""
        knowledge_points = self._get_knowledge_points([current_note])
        topics = ",".join(knowledge_points)
        prompt = GenNoteDetailPrompt.USER_PROMPT.format(topics=topics)
        return prompt


# Global instance
note_service = NoteService()
