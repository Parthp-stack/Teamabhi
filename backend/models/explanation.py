from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class ExplanationQuestion(Base):
    __tablename__ = "explanation_questions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("coding_submissions.id"), nullable=False, index=True)
    question_index = Column(Integer, default=1, nullable=False)
    question_text = Column(Text, nullable=False)
    question = Column(Text, nullable=True)
    expected_concept = Column(String(100), nullable=True) # e.g. "Time Complexity", "Hash Map Data Structure"

    submission = relationship("CodingSubmission", back_populates="explanation_questions")
    answers = relationship("ExplanationAnswer", back_populates="question", cascade="all, delete-orphan")


class ExplanationAnswer(Base):
    __tablename__ = "explanation_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("explanation_questions.id"), nullable=False, default=1)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    student_response = Column(Text, nullable=False, default="")
    explanation_question_id = Column(Integer, nullable=True, index=True)
    student_answer = Column(Text, nullable=True)
    evaluation = Column(Text, nullable=True) # AI technical evaluation & rationale
    ai_feedback = Column(Text, nullable=True)
    score = Column(Float, default=0.0, nullable=False) # 0 to 10
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    question = relationship("ExplanationQuestion", back_populates="answers", foreign_keys=[question_id])

