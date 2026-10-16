from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    type = Column(String(50), nullable=False, default="MCQ") # MCQ, SHORT_ANSWER, CODING
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False, default="MEDIUM") # EASY, MEDIUM, HARD
    options = Column(JSON, nullable=True) # list of choices for MCQ
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    concept = relationship("Concept", back_populates="questions")
    attempts = relationship("Attempt", back_populates="question", cascade="all, delete-orphan")


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer = Column(Text, nullable=False)
    correct = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship("User")
    question = relationship("Question", back_populates="attempts")
