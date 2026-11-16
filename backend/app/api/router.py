from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine
from app.api import academies, auth, catalog, lesson_logs, people, scheduling, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(academies.router)
api_router.include_router(people.router)
api_router.include_router(catalog.router)
api_router.include_router(scheduling.router)
api_router.include_router(lesson_logs.router)


@api_router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
