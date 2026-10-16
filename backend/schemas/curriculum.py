from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None

class CourseUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class ModuleCreateRequest(BaseModel):
    course_id: int
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    order_index: Optional[int] = 0

class ModuleUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None

class ConceptCreateRequest(BaseModel):
    module_id: int
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    difficulty: str = Field("MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")
    order_index: Optional[int] = 0

class ConceptUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    order_index: Optional[int] = None

class PrerequisiteAddRequest(BaseModel):
    prerequisite_id: int

class QuestionCreateRequest(BaseModel):
    concept_id: int
    question_text: str = Field(..., min_length=5)
    question_type: str = Field("MCQ", pattern="^(MCQ|TRUE_FALSE|SHORT_ANSWER)$")
    difficulty: str = Field("MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")
    options: Optional[List[str]] = None
    correct_answer: str = Field(..., min_length=1)
    explanation: Optional[str] = None

class QuestionUpdateRequest(BaseModel):
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None

class QuestionResponseItem(BaseModel):
    id: int
    concept_id: int
    concept_name: str
    question_text: str
    question_type: str
    difficulty: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    created_at: Optional[datetime] = None

class AIQuestionPreviewRequest(BaseModel):
    concept_name: str
    difficulty: Optional[str] = "MEDIUM"
    question_type: Optional[str] = "MCQ"

class StudentHistoryItem(BaseModel):
    id: int
    question_id: int
    question_text: str
    concept_name: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    score: float
    time_taken: float
    timestamp: datetime
    explanation: Optional[str] = None

class StudentCodingHistoryItem(BaseModel):
    id: int
    problem_id: int
    problem_title: str
    language: str
    status: str
    score: float
    execution_time: float
    memory_used: float
    timestamp: datetime
    explanation_score: Optional[float] = None
    viva_summary: Optional[str] = None
    viva_details: Optional[List[Dict[str, Any]]] = None

class StudentAnalyticsResponse(BaseModel):
    overall_mastery: float
    mastery_progression: List[Dict[str, Any]]
    difficulty_performance: Dict[str, Dict[str, Any]]
    attempts_per_concept: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
