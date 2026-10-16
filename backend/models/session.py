from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=True, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # Review status: NORMAL_RHYTHM, REVIEW_SUGGESTED, INSUFFICIENT_DATA
    overall_review_status = Column(String(50), default="INSUFFICIENT_DATA", nullable=False, index=True)
    is_reviewed = Column(Boolean, default=False, nullable=False)
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    student = relationship("User", foreign_keys=[student_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    problem = relationship("CodingProblem")
    events = relationship("SessionEvent", back_populates="session", cascade="all, delete-orphan", order_by="SessionEvent.timestamp", foreign_keys="SessionEvent.session_id")
    integrity_signals = relationship("IntegritySignal", back_populates="session", cascade="all, delete-orphan")
    revisions = relationship("CodeRevision", back_populates="session", cascade="all, delete-orphan", order_by="CodeRevision.revision_number")


class CodeRevision(Base):
    __tablename__ = "code_revisions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("session_events.id"), nullable=True, index=True)
    snapshot_type = Column(String(50), nullable=False, default="INCREMENTAL") # MAJOR_SNAPSHOT, EVENT_SNAPSHOT, SUBMISSION
    source_code = Column(Text, nullable=False)
    diff_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    session = relationship("Session", back_populates="revisions")
    event = relationship("SessionEvent", foreign_keys=[event_id], post_update=True)


class SessionEvent(Base):
    __tablename__ = "session_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    assessment_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=True, index=True)
    client_event_id = Column(String(100), nullable=True, index=True) # Client idempotency key to prevent retry duplicates

    # Event Types: TYPE, PASTE, DELETE, REPLACE, COPY, RUN, SUBMIT, EDIT_AFTER_RUN, FOCUS, BLUR, VISIBILITY_CHANGE, SESSION_START, SESSION_END, KEYSTROKE
    event_type = Column(String(50), nullable=False, index=True)
    
    server_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    client_timestamp = Column(DateTime, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True) # Backwards compatible alias
    
    # Code Location: { "start_line": int, "start_column": int, "end_line": int, "end_column": int, "selection_range": dict }
    code_location = Column(JSON, nullable=True)
    
    revision_id = Column(Integer, ForeignKey("code_revisions.id"), nullable=True, index=True)
    inserted_character_count = Column(Integer, default=0, nullable=False)
    deleted_character_count = Column(Integer, default=0, nullable=False)
    duration = Column(Float, nullable=True) # Time since previous edit or action duration in seconds
    
    # Review status for this event: NORMAL_RHYTHM, REVIEW_SUGGESTED, INSUFFICIENT_DATA
    review_status = Column(String(50), default="NORMAL_RHYTHM", nullable=False, index=True)
    classification = Column(String(100), nullable=True) # Normal typing, Large paste, Rapid bulk insertion, Replacement, Uncertain activity
    classification_reason = Column(Text, nullable=True)
    
    event_metadata = Column("metadata", JSON, nullable=True)

    session = relationship("Session", back_populates="events", foreign_keys=[session_id])
    student = relationship("User", foreign_keys=[student_id])
    code_revision = relationship("CodeRevision", foreign_keys=[revision_id])
