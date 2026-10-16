from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.models.user import User
from backend.utils.security import get_current_user
from backend.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Assistance (OpenRouter)"])

class HintRequest(BaseModel):
    question_text: str
    student_attempt: Optional[str] = ""

class CodeAnalysisRequest(BaseModel):
    source_code: str
    problem_title: str
    language: Optional[str] = "python"

@router.post("/hint")
async def generate_ai_hint(
    req: HintRequest,
    current_user: User = Depends(get_current_user)
):
    hint = await AIService.generate_hint(req.question_text, req.student_attempt or "")
    return {"hint": hint}

@router.post("/analyze-code")
async def analyze_student_code(
    req: CodeAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    questions = await AIService.generate_code_questions(
        source_code=req.source_code,
        problem_title=req.problem_title,
        language=req.language or "python"
    )
    return {"questions": questions}
