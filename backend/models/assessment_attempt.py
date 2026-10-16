from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(String(100), nullable=False, index=True)
    assessment_type = Column(String(50), default="ADAPTIVE_QUIZ", nullable=False) # ADAPTIVE_QUIZ, CODING, PRACTICE
    attempt_number = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="IN_PROGRESS", nullable=False, index=True) # IN_PROGRESS, COMPLETED, ABANDONED

    score = Column(Float, default=0.0, nullable=False)
    questions_attempted = Column(Integer, default=0, nullable=False)
    questions_correct = Column(Integer, default=0, nullable=False)
    coding_submissions_count = Column(Integer, default=0, nullable=False)

    warnings_count = Column(Integer, default=0, nullable=False)
    integrity_events_count = Column(Integer, default=0, nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    risk_level = Column(String(50), default="NORMAL", nullable=False) # NORMAL, LOW_RISK, MEDIUM_RISK, HIGH_RISK

    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)

    student = relationship("User", foreign_keys=[student_id])
    warnings = relationship("AssessmentWarning", back_populates="attempt", cascade="all, delete-orphan")


class AssessmentWarning(Base):
    __tablename__ = "assessment_warnings"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(String(100), nullable=True, index=True)
    attempt_id = Column(Integer, ForeignKey("assessment_attempts.id"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)

    warning_type = Column(String(100), nullable=False, index=True) # TAB_SWITCH, WINDOW_BLUR, VISIBILITY_CHANGE, FULLSCREEN_EXIT, RESIZE_ANOMALY, POSSIBLE_SPLIT_SCREEN
    warning_number = Column(Integer, default=1, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), default="LOW", nullable=False) # LOW, MEDIUM, HIGH
    evidence = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    student = relationship("User", foreign_keys=[student_id])
    attempt = relationship("AssessmentAttempt", back_populates="warnings", foreign_keys=[attempt_id])
    session = relationship("Session", foreign_keys=[session_id])
