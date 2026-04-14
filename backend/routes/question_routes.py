from fastapi import APIRouter
from pydantic import BaseModel
from backend.ai.question_generator import generate_question, generate_followup_question
router = APIRouter(prefix="/question", tags=["Question"])


class QuestionRequest(BaseModel):
    level: str
    category: str
    role: str
class FollowupRequest(BaseModel):
    previous_question: str
    user_answer: str
    role: str
    hint: str = ""
@router.post("/generate")
def generate_question_api(req: QuestionRequest):
    try:
        question = generate_question(
            level=req.level,
            category=req.category,
            role=req.role
        )

        return {
            "status": "success",
            "question": question
        }

    except Exception as e:
        print("[Question API Error]:", e)

        return {
            "status": "error",
            "question": "Unable to generate question right now."
        }
@router.post("/followup")
def generate_followup_api(req: FollowupRequest):
    try:
        question = generate_followup_question(
            previous_question=req.previous_question,
            user_answer=req.user_answer,
            role=req.role,
            hint=req.hint
        )

        return {
            "status": "success",
            "question": question
        }

    except Exception as e:
        print("[Followup API Error]:", e)

        return {
            "status": "error",
            "question": "Unable to generate follow-up question."
        }