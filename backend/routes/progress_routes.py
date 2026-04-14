from fastapi import APIRouter
from backend.services.progress_service import compute_progress
from backend.services.user_service import get_user
router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("/user/{user_id}")
def get_progress(user_id: int):
    if not get_user(user_id):
        return {"error": "User not found"}
    return compute_progress(user_id=user_id)