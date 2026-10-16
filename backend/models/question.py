from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("modules.id"), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, default="MCQ") # MCQ, TRUE_FALSE, SHORT_ANSWER, CODING, DEBUGGING, EXPLANATION, VIVA
    difficulty = Column(String(20), nullable=False, default="MEDIUM") # EASY, MEDIUM, HARD
    language = Column(String(50), nullable=True, default="all") # python, cpp, c, java, javascript, all
    code_snippet = Column(Text, nullable=True)
    options = Column(JSON, nullable=True) # list of choices for MCQ / TRUE_FALSE
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    concept = relationship("Concept", back_populates="questions")
    topic = relationship("Module")
    attempts = relationship("Attempt", back_populates="question", cascade="all, delete-orphan")

    # Compatibility aliases
    @property
    def title(self) -> str:
        return self.question_text.split("\n")[0][:80]

    @property
    def description(self) -> str:
        return self.question_text

    @property
    def type(self) -> str:
        return self.question_type


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    selected_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False, index=True)
    score = Column(Float, default=1.0, nullable=False)
    time_taken = Column(Float, default=0.0, nullable=False) # seconds
    
    # Adaptive assessment attempt metadata
    assessment_id = Column(Integer, nullable=True, index=True)
    attempt_number = Column(Integer, default=1, nullable=False)
    difficulty = Column(String(20), nullable=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True, index=True)
    assessment_attempt_id = Column(Integer, ForeignKey("assessment_attempts.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    student = relationship("User")
    question = relationship("Question", back_populates="attempts")
    concept = relationship("Concept", foreign_keys=[concept_id])

    # Compatibility aliases
    @property
    def answer(self) -> str:
        return self.selected_answer

    @property
    def correct(self) -> bool:
        return self.is_correct

    @property
    def timestamp(self):
        return self.created_at

