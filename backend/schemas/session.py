from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class CodeLocation(BaseModel):
    start_line: Optional[int] = None
    start_column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    selection_range: Optional[Dict[str, Any]] = None

class SessionEventItem(BaseModel):
    client_event_id: Optional[str] = None
    event_type: str # TYPE, PASTE, DELETE, REPLACE, COPY, RUN, SUBMIT, EDIT_AFTER_RUN, FOCUS, BLUR, VISIBILITY_CHANGE, SESSION_START, SESSION_END, KEYSTROKE
    timestamp: Optional[datetime] = None
    client_timestamp: Optional[datetime] = None
    code_location: Optional[Dict[str, Any]] = None
    revision_id: Optional[int] = None
    inserted_character_count: Optional[int] = 0
    deleted_character_count: Optional[int] = 0
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    current_code: Optional[str] = None # code snapshot for revision tracking

class SessionEventBatchRequest(BaseModel):
    events: List[SessionEventItem]

class SessionCreateRequest(BaseModel):
    assessment_id: Optional[int] = None

class SessionResponse(BaseModel):
    id: int
    student_id: int
    assessment_id: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    overall_review_status: str = "INSUFFICIENT_DATA"

    class Config:
        from_attributes = True

class SessionDetailResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    student_email: Optional[str] = None
    assessment_id: Optional[int] = None
    problem_title: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_events: int = 0
    paste_count: int = 0
    review_suggested_count: int = 0
    overall_review_status: str = "INSUFFICIENT_DATA"
    is_reviewed: bool = False
    review_notes: Optional[str] = None
    integrity_signals_count: int = 0
