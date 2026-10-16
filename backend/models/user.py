from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from backend.database import Base

class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    TRAINER = "TRAINER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.STUDENT.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class StudentProfile(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    enrollment_number = Column(String(100), nullable=True)
    target_subject = Column(String(100), nullable=True, default="Data Structures")
    preferences = Column(JSON, default=dict, nullable=True)

    user = relationship("User", back_populates="student_profile")


class TeacherProfile(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=True, default="Computer Science")
    bio = Column(Text, nullable=True)

    user = relationship("User", back_populates="teacher_profile")

