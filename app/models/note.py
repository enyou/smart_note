from pydantic import BaseModel, computed_field
from datetime import date, datetime
from typing import Optional

from app.models.study_plan import StudyPlanTitle

# Pydantic Models


class NoteBase(BaseModel):
    study_content: str
    detailed_content: Optional[str] = None
    note_content: Optional[str] = None
    actual_study_start_time: Optional[datetime] = None
    planned_study_start_time: Optional[datetime] = None
    is_completed: Optional[bool] = False


class NoteCreate(NoteBase):
    study_plan_id: int


class NoteUpdate(NoteBase):
    pass


class NoteInDB(NoteBase):
    id: int
    study_plan_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NoteResponse(BaseModel):
    id: int
    study_plan_id: int
    study_content: str
    planned_study_start_time: Optional[datetime] = None
    actual_study_start_time: Optional[datetime] = None
    is_completed: bool
    
    @computed_field
    def summary(self) -> str:
        return self.study_content.split('##')[0].replace('#','').strip()

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.strftime('%Y-%m-%d'),
        }


class CurrentDayNote(BaseModel):
    id: int
    study_plan_id: int
    study_content: str
    planned_study_start_time: Optional[datetime] = None
    study_plan: StudyPlanTitle

    class Config:

        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.strftime("%Y-%m-%d")
        }
