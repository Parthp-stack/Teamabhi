from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime

class IntegritySignalResponse(BaseModel):
    id: int
    session_id: int
    event_id: Optional[int] = None
    signal_type: str # LARGE_PASTE, FAST_CODE, NO_CYCLE, TAB_SWITCH, UNIFORM_TYPING, RAPID_INSERTION, SUBSTANTIAL_REPLACEMENT
    severity: str # LOW, MEDIUM, HIGH
    description: str
    timestamp: datetime
    review_status: str = "PENDING"
    trainer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    event_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class TimelineEventResponse(BaseModel):
    id: int
    session_id: int
    student_id: Optional[int] = None
    assessment_id: Optional[int] = None
    client_event_id: Optional[str] = None
    event_type: str
    timestamp: datetime
    server_timestamp: datetime
    client_timestamp: Optional[datetime] = None
    code_location: Optional[Dict[str, Any]] = None
    revision_id: Optional[int] = None
    inserted_character_count: int = 0
    deleted_character_count: int = 0
    duration: Optional[float] = None
    review_status: str = "NORMAL_RHYTHM"
    classification: Optional[str] = None
    classification_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    signal: Optional[IntegritySignalResponse] = None

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
    events: List[TimelineEventResponse]
    signals: List[IntegritySignalResponse]
    summary_verdict: str = "Evidence for human review (No automatic verdict)"
    overall_review_status: str = "INSUFFICIENT_DATA"

class TypingRhythmMetrics(BaseModel):
    baseline_cps: float # Characters per second
    mean_interval_seconds: float
    typical_insertion_range: str # e.g. "5 - 20 chars"
    typical_interval_range: str # e.g. "0.2s - 1.5s"
    total_typing_events: int
    total_paste_events: int
    rapid_insertions_count: int
    review_status: str # NORMAL_RHYTHM, REVIEW_SUGGESTED, INSUFFICIENT_DATA
    status_message: str

class CodeRevisionComparison(BaseModel):
    revision_id: int
    revision_number: int
    event_id: Optional[int] = None
    snapshot_type: str
    diff_summary: Optional[str] = None
    before_code: str
    current_code: str
    after_code: str
    code_location: Optional[Dict[str, Any]] = None

class TrainerReviewRequest(BaseModel):
    action: str # MARK_REVIEWED, DISMISS, ADD_NOTE
    notes: Optional[str] = None
    signal_id: Optional[int] = None

class IntegrityDashboardMetrics(BaseModel):
    total_sessions: int
    normal_rhythm_count: int
    review_suggested_count: int
    insufficient_data_count: int
    pending_review_signals_count: int

class IntegrityDashboardOverview(BaseModel):
    metrics: IntegrityDashboardMetrics
    sessions: List[Dict[str, Any]]
