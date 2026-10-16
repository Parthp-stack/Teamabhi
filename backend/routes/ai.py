from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from backend.models.user import User
from backend.utils.security import get_current_user
from backend.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Integration (OpenRouter)"])

class GenerateQuestionRequest(BaseModel):
    concept: str
    difficulty: Optional[str] = "MEDIUM"
    question_type: Optional[str] = "MCQ"

class ExplainConceptRequest(BaseModel):
    concept: str
    student_mastery: Optional[float] = 0.0
    difficulty: Optional[str] = "MEDIUM"

class GeneratePracticeRequest(BaseModel):
    concept: str
    student_weak_areas: Optional[List[str]] = None

@router.post("/generate-question")
async def generate_question(
    req: GenerateQuestionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generates a new conceptual question on the fly using Nemotron via OpenRouter.
    """
    res = await AIService.generate_question(
        concept=req.concept,
        difficulty=req.difficulty or "MEDIUM",
        question_type=req.question_type or "MCQ"
    )
    return res

@router.post("/explain-concept")
async def explain_concept(
    req: ExplainConceptRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Produces a personalized conceptual explanation, example, common pitfall, and practice check.
    """
    res = await AIService.explain_concept(
        concept=req.concept,
        student_mastery=req.student_mastery or 0.0,
        difficulty=req.difficulty or "MEDIUM"
    )
    return res

@router.post("/generate-practice")
async def generate_practice(
    req: GeneratePracticeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generates targeted practice questions focusing on a student's weak concept areas.
    """
    questions = await AIService.generate_practice(
        concept=req.concept,
        student_weak_areas=req.student_weak_areas
    )
    return {"concept": req.concept, "practice_questions": questions}
