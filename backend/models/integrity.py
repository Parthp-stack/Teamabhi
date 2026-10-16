from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class IntegritySignal(Base):
    __tablename__ = "integrity_signals"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("session_events.id"), nullable=True)
    signal_type = Column(String(50), nullable=False) # LARGE_PASTE, FAST_CODE, NO_CYCLE, TAB_SWITCH, UNIFORM_TYPING
    severity = Column(String(20), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("Session", back_populates="integrity_signals")
    event = relationship("SessionEvent")
