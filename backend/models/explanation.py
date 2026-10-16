from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class ExplanationQuestion(Base):
    __tablename__ = "explanation_questions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("coding_submissions.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    expected_concept = Column(String(100), nullable=True) # e.g. "Time Complexity", "Hash Map Data Structure"

    submission = relationship("CodingSubmission", back_populates="explanation_questions")
    answers = relationship("ExplanationAnswer", back_populates="question", cascade="all, delete-orphan")


class ExplanationAnswer(Base):
    __tablename__ = "explanation_answers"

    id = Column(Integer, primary_key=True, index=True)
    explanation_question_id = Column(Integer, ForeignKey("explanation_questions.id"), nullable=False, index=True)
    student_answer = Column(Text, nullable=False)
    evaluation = Column(Text, nullable=True) # AI technical evaluation & rationale
    score = Column(Float, default=0.0, nullable=False) # 0 to 10
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    question = relationship("ExplanationQuestion", back_populates="answers")
