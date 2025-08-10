from fastapi import APIRouter
from app.api.v1.endpoints import notes, users, study_plans, chat

api_router = APIRouter()

api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    study_plans.router, prefix="/study-plans", tags=["study-plans"])
api_router.include_router(chat.router, prefix="/chats", tags=["chats"])
