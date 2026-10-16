from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, synonym
from datetime import datetime, timezone
from backend.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    name = synonym("title")

    creator = relationship("User", foreign_keys=[created_by])
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order_index")


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)

    name = synonym("title")

    course = relationship("Course", back_populates="modules")
    concepts = relationship("Concept", back_populates="module", cascade="all, delete-orphan", order_by="Concept.order_index")
