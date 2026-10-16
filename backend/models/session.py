from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)

    student = relationship("User")
    problem = relationship("CodingProblem")
    events = relationship("SessionEvent", back_populates="session", cascade="all, delete-orphan", order_by="SessionEvent.timestamp")
    integrity_signals = relationship("IntegritySignal", back_populates="session", cascade="all, delete-orphan")


class SessionEvent(Base):
    __tablename__ = "session_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False) # KEYSTROKE, DELETE, PASTE, RUN, SUBMIT, FOCUS, BLUR, TAB_SWITCH
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    event_metadata = Column("metadata", JSON, nullable=True) # character count, paste content preview, test result, diff

    session = relationship("Session", back_populates="events")
