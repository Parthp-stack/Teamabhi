from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class StudentMastery(Base):
    __tablename__ = "student_mastery"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    mastery_score = Column(Float, default=0.0, nullable=False) # 0 to 100
    attempts = Column(Integer, default=0, nullable=False)
    correct_attempts = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    student = relationship("User")
    concept = relationship("Concept", back_populates="masteries")

    # Compatibility alias
    @property
    def mastery(self) -> float:
        return self.mastery_score

    @mastery.setter
    def mastery(self, value: float):
        self.mastery_score = value

    @property
    def updated_at(self):
        return self.last_attempt_at


class MasteryHistory(Base):
    __tablename__ = "mastery_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    mastery_score = Column(Float, nullable=False)
    change_amount = Column(Float, nullable=False)
    reason = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    student = relationship("User")
    concept = relationship("Concept")

    # Compatibility alias
    @property
    def mastery(self) -> float:
        return self.mastery_score
