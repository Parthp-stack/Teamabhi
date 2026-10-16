from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class IntegritySignal(Base):
    __tablename__ = "integrity_signals"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("session_events.id"), nullable=True, index=True)
    signal_type = Column(String(50), nullable=False, index=True) # LARGE_PASTE, FAST_CODE, NO_CYCLE, TAB_SWITCH, UNIFORM_TYPING, RAPID_INSERTION, SUBSTANTIAL_REPLACEMENT
    severity = Column(String(20), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Trainer review workflow: PENDING, REVIEWED, DISMISSED
    review_status = Column(String(50), default="PENDING", nullable=False, index=True)
    trainer_notes = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    session = relationship("Session", back_populates="integrity_signals")
    event = relationship("SessionEvent")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class IntegrityEvent(Base):
    __tablename__ = "integrity_events"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(String(100), nullable=True, index=True)
    attempt_id = Column(Integer, ForeignKey("assessment_attempts.id"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    question_number = Column(Integer, nullable=True)

    event_type = Column(String(100), nullable=False, index=True) # COPY / CTRL+C, PASTE / CTRL+V, CUT / CTRL+X, TAB_SWITCH, WINDOW_BLUR, FULLSCREEN_EXIT, POSSIBLE_SPLIT_SCREEN, CODE_RUN, SUBMISSION, etc.
    action = Column(String(100), nullable=True) # Code copied, Code pasted, Window lost focus, Answer changed, etc.
    details = Column(Text, nullable=True)
    risk_level = Column(String(50), default="NORMAL", nullable=False, index=True) # NORMAL, LOW, MEDIUM, HIGH
    warning = Column(Text, nullable=True)
    source = Column(String(50), default="ASSESSMENT", nullable=False, index=True) # CODING_ASSESSMENT, ADAPTIVE_QUIZ, BROWSER
    event_metadata = Column("metadata", Text, nullable=True) # JSON-serializable string or dict
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    student = relationship("User", foreign_keys=[student_id])
    attempt = relationship("AssessmentAttempt", foreign_keys=[attempt_id])
    question = relationship("Question", foreign_keys=[question_id])
    session = relationship("Session", foreign_keys=[session_id])

