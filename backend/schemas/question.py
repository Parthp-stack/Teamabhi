from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class QuestionResponse(BaseModel):
    id: int
    concept_id: int
    concept_name: Optional[str] = None
    type: str
    title: str
    description: str
    difficulty: str
    options: Optional[List[str]] = None
    # Note: correct_answer and explanation are deliberately omitted or kept hidden before submission!

    class Config:
        from_attributes = True

class QuestionAttemptRequest(BaseModel):
    question_id: int
    answer: str

class QuestionAttemptResult(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    previous_mastery: float
    new_mastery: float
    mastery_change: float
    concept_id: int
    concept_name: str
