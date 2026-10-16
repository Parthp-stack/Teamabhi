from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class IntegritySignalResponse(BaseModel):
    id: int
    session_id: int
    event_id: Optional[int] = None
    signal_type: str # LARGE_PASTE, FAST_CODE, NO_CYCLE, TAB_SWITCH, UNIFORM_TYPING
    severity: str # LOW, MEDIUM, HIGH
    description: str
    timestamp: datetime
    event_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class SessionReplayEvent(BaseModel):
    id: int
    event_type: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    signal: Optional[IntegritySignalResponse] = None

class SessionReplayResponse(BaseModel):
    session_id: int
    student_id: int
    student_name: str
    problem_id: Optional[int]
    problem_title: Optional[str]
    final_source_code: Optional[str] = ""
    events: list[SessionReplayEvent]
    signals: list[IntegritySignalResponse]
    summary_verdict: str = "Evidence for human review (No automatic verdict)"
