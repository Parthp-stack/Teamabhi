from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), default="MEDIUM", nullable=False) # EASY, MEDIUM, HARD
    allowed_languages = Column(JSON, default=lambda: ["python", "cpp", "c", "java", "javascript"], nullable=False)
    time_limit = Column(Float, default=2.0, nullable=False) # seconds
    memory_limit = Column(Integer, default=128, nullable=False) # MB

    # Comprehensive problem definition fields (Requirement 3)
    problem_statement = Column(Text, nullable=True)
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    examples = Column(JSON, nullable=True)
    expected_solution_concept = Column(String(100), nullable=True)
    topic = Column(String(100), nullable=True)

    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("CodingSubmission", back_populates="problem", cascade="all, delete-orphan")

    @property
    def full_statement(self) -> str:
        return self.problem_statement or self.description



class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=False)
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, default=False, nullable=False)

    problem = relationship("CodingProblem", back_populates="test_cases")


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=False)
    language = Column(String(50), nullable=False) # python, cpp, c, java, javascript
    source_code = Column(Text, nullable=False)
    status = Column(String(50), nullable=False) # PASSED, FAILED, COMPILE_ERROR, RUNTIME_ERROR, TIMEOUT, MEMORY_LIMIT, SECURITY_BLOCKED
    score = Column(Float, default=0.0, nullable=False)
    execution_time = Column(Float, default=0.0, nullable=False)
    memory_used = Column(Float, default=0.0, nullable=False)
    viva_verdict = Column(String(100), nullable=True)
    ai_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship("User")
    problem = relationship("CodingProblem", back_populates="submissions")
    explanation_questions = relationship("ExplanationQuestion", back_populates="submission", cascade="all, delete-orphan")
    ai_evaluations = relationship("AIEvaluation", back_populates="submission", cascade="all, delete-orphan")
