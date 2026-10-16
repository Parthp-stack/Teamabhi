from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class AIEvaluationCreate(BaseModel):
    student_id: int
    question_id: Optional[int] = None
    concept_id: Optional[int] = None
    submission_id: Optional[int] = None
    score: float = 0.0
    understanding_verdict: Optional[str] = None
    feedback: Optional[str] = None
    detected_weaknesses: Optional[List[str]] = None
    detected_strengths: Optional[List[str]] = None
    difficulty_recommendation: Optional[str] = None
    next_question_recommendation: Optional[str] = None

class AIEvaluationResponse(BaseModel):
    id: int
    student_id: int
    question_id: Optional[int] = None
    concept_id: Optional[int] = None
    concept_name: Optional[str] = None
    submission_id: Optional[int] = None
    score: float
    understanding_verdict: Optional[str] = None
    feedback: Optional[str] = None
    detected_weaknesses: Optional[List[str]] = None
    detected_strengths: Optional[List[str]] = None
    difficulty_recommendation: Optional[str] = None
    next_question_recommendation: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
