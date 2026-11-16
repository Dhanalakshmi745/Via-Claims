from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["Version"])


@router.get("/version")
def get_version():
    return {"version": settings.app_version}