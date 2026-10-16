from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class StudentMastery(Base):
    __tablename__ = "student_mastery"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    mastery = Column(Float, default=0.0, nullable=False) # 0 to 100
    attempts = Column(Integer, default=0, nullable=False)
    correct_attempts = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    student = relationship("User")
    concept = relationship("Concept", back_populates="masteries")


class MasteryHistory(Base):
    __tablename__ = "mastery_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    mastery = Column(Float, nullable=False)
    change_amount = Column(Float, nullable=False)
    reason = Column(String(255), nullable=True) # e.g. "Attempt #3 (Correct)" or "Initial baseline"
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship("User")
    concept = relationship("Concept")
