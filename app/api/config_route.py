from fastapi import APIRouter
from ..core.config import settings

router = APIRouter(tags=["Config"])

@router.get("/config")
def get_config():
    return {"api_base_url": settings.api_base_url}
