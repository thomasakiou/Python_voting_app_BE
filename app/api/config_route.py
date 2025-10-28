from fastapi import APIRouter
from ..core.config import settings

router = APIRouter(tags=["Config"])

@router.get("/config")
def get_config():
    return {"api_base_url": settings.api_base_url}


# from fastapi import APIRouter

# router = APIRouter()

# # @router.get("/config")
# def get_config():
#     return {
#         "app_name": "Voting App",
#         "version": "1.0",
#         "status": "running"
#     }
