from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StudentMasteryResponse(BaseModel):
    id: int
    student_id: int
    concept_id: int
    concept_name: str
    mastery: float
    attempts: int
    correct_attempts: int
    status: str # MASTERED, LEARNING, WEAK, LOCKED
    updated_at: datetime

    class Config:
        from_attributes = True

class MasteryUpdateRequest(BaseModel):
    concept_id: int
    score_delta: float
    reason: Optional[str] = "Manual update"
    student_id: Optional[int] = None

class MasteryHistoryResponse(BaseModel):
    id: int
    concept_id: int
    concept_name: str
    mastery: float
    change_amount: float
    reason: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class StudentMasteryOverview(BaseModel):
    student_id: int
    student_name: str
    overall_mastery: float
    concepts: List[StudentMasteryResponse]
    weak_concepts: List[StudentMasteryResponse]
    strong_concepts: List[StudentMasteryResponse]
    recommended_concept: Optional[str] = None
