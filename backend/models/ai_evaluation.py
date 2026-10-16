from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class AIEvaluation(Base):
    __tablename__ = "ai_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True, index=True)
    submission_id = Column(Integer, ForeignKey("coding_submissions.id"), nullable=True, index=True)
    score = Column(Float, default=0.0, nullable=False)
    understanding_verdict = Column(String(100), nullable=True) # e.g. "Correct code + understood", "Correct code + poor understanding", "Wrong code + good conceptual understanding", "Wrong code + poor understanding"
    feedback = Column(Text, nullable=True)
    detected_weaknesses = Column(JSON, default=list, nullable=True)
    detected_strengths = Column(JSON, default=list, nullable=True)
    difficulty_recommendation = Column(String(50), nullable=True)
    next_question_recommendation = Column(String(200), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    student = relationship("User")
    question = relationship("Question")
    concept = relationship("Concept")
    submission = relationship("CodingSubmission", back_populates="ai_evaluations")

