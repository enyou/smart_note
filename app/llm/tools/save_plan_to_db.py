#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名: save_plan_to_db.py
功能: 将生成的计划保存到数据库中
作者: Yang
创建日期: 2025-06-18
版本号: 1.0
变更说明: 无
"""

from datetime import datetime, timedelta
import json
from langchain.tools import BaseTool
from app.db.session import get_session
from app.models.note import Note
from app.models.study_plan import StudyPlan
from app.tools.mk_2_json import markdown_to_json


class SavePlanToDBTool(BaseTool):
    name: str = "save_plan_to_db_tool"
    description: str = "将生成的学习计划保存到数据库中"

    def _run(self, input_text: str) -> str:
        """将生成的学习计划保存到数据库中"""
        try:
            data = json.loads(markdown_to_json(input_text))
            total_days = len(data["daily_plans"])
            # 计算时间范围
            start_time = datetime.now()
            end_time = start_time + timedelta(days=total_days)

            # 创建主学习计划
            study_plan = StudyPlan(
                title=data["title"],
                content=data["content"],
                start_time=start_time,
                end_time=end_time,
                user_id=1
            )

            gen = get_session()
            try:
                db = next(gen)
                db.add(study_plan)
                db.flush()
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
                db.commit()
            finally:
                try:
                    next(gen)
                except StopIteration:
                    pass

            return input_text

        except Exception as e:
            raise e
