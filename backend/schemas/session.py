from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class SessionEventItem(BaseModel):
    event_type: str # KEYSTROKE, DELETE, PASTE, RUN, SUBMIT, FOCUS, BLUR, TAB_SWITCH
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

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

    class Config:
        from_attributes = True

class SessionDetailResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    assessment_id: Optional[int] = None
    problem_title: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_events: int
    integrity_signals_count: int
