from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ExplanationQuestionResponse(BaseModel):
    id: int
    submission_id: int
    question: str
    expected_concept: Optional[str] = None

    class Config:
        from_attributes = True

class AnswerItem(BaseModel):
    question_id: int
    student_answer: str

class ExplanationAnswersSubmitRequest(BaseModel):
    answers: List[AnswerItem]

class EvaluatedAnswerResponse(BaseModel):
    question_id: int
    question: str
    student_answer: str
    evaluation: str
    score: float # 0 to 10

class ExplanationResultResponse(BaseModel):
    submission_id: int
    overall_understanding_score: float # 0 to 10
    understanding_verdict: Optional[str] = None # "Correct code + understood", "Correct code + poor understanding", "Wrong code + good conceptual understanding", "Wrong code + poor understanding"
    evaluated_answers: List[EvaluatedAnswerResponse]
    summary_review: str
    needs_review: bool
    detected_weaknesses: Optional[List[str]] = None
    detected_strengths: Optional[List[str]] = None
    difficulty_recommendation: Optional[str] = None
    next_question_recommendation: Optional[str] = None

