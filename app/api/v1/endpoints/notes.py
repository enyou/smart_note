from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_session
from app.models.note import CurrentDayNote, NoteResponse, NoteUpdate
from app.services.note_service import note_service
from app.core.dependencies import method_logger
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@method_logger
@router.get("/study-plan/{study_plan_id}", response_model=List[NoteResponse])
async def get_study_plan_notes(study_plan_id: int, db: AsyncSession = Depends(get_session)):
    """获取该学习计划下面的全部notes"""
    logger.info("获取该学习计划下面的全部notes")
    notes = await note_service.get_study_plan_notes(db, study_plan_id)
    return [NoteResponse.model_validate(note) for note in notes]


@method_logger
@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: AsyncSession = Depends(get_session)):
    """获取笔记的详细信息"""
    logger.info(f"取笔记的详细信息note_id:{note_id}")
    note = await note_service.get_note(db, note_id)
    if note is None:
        logger.info("没有获取note")
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@method_logger
@router.get("/{note_id}/details", response_model=NoteResponse)
async def get_note(note_id: int, db: AsyncSession = Depends(get_session)):
    """获取笔记的具体要学习的内容"""
    logger.info("获取笔记的具体要学习的内容")
    return StreamingResponse(note_service.generate_detailed_content(db, note_id), media_type="text/event-stream")


@method_logger
@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, note: NoteUpdate, db: AsyncSession = Depends(get_session)):
    """更新笔记的详细信息"""
    logger.info(f"更新笔记的详细信息 note_id:{note_id}")
    updated_note = await note_service.update_note(db, note_id, note)
    if updated_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return updated_note


@method_logger
@router.get("/current_day/list", response_model=List[CurrentDayNote])
async def get_current_day_notes(db: AsyncSession = Depends(get_session)):
    """获取该学习计划下面的全部notes"""
    logger.info(f"获取该学习计划下面的全部notes")
    resp = await note_service.get_currend_day_notes(db)
    return resp
