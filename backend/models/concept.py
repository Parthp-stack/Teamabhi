from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from backend.database import Base

concept_prerequisites = Table(
    "concept_prerequisites",
    Base.metadata,
    Column("concept_id", Integer, ForeignKey("concepts.id"), primary_key=True),
    Column("prerequisite_id", Integer, ForeignKey("concepts.id"), primary_key=True)
)

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    module = relationship("Module", back_populates="concepts")
    questions = relationship("Question", back_populates="concept", cascade="all, delete-orphan")
    masteries = relationship("StudentMastery", back_populates="concept", cascade="all, delete-orphan")

    # Prerequisites relationship
    prerequisites = relationship(
        "Concept",
        secondary=concept_prerequisites,
        primaryjoin=id == concept_prerequisites.c.concept_id,
        secondaryjoin=id == concept_prerequisites.c.prerequisite_id,
        backref="dependents"
    )
