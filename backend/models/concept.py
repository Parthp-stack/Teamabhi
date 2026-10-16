from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class ConceptPrerequisite(Base):
    __tablename__ = "concept_prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    prerequisite_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), default="MEDIUM", nullable=False) # EASY, MEDIUM, HARD
    order_index = Column(Integer, default=0, nullable=False)

    module = relationship("Module", back_populates="concepts")
    questions = relationship("Question", back_populates="concept", cascade="all, delete-orphan")
    masteries = relationship("StudentMastery", back_populates="concept", cascade="all, delete-orphan")

    # Prerequisites relationship via ConceptPrerequisite
    prerequisites = relationship(
        "Concept",
        secondary="concept_prerequisites",
        primaryjoin=id == ConceptPrerequisite.concept_id,
        secondaryjoin=id == ConceptPrerequisite.prerequisite_id,
        backref="dependents"
    )
