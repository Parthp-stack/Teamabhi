from pydantic import BaseModel
from typing import List, Optional

class ConceptSummary(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    prerequisites: List[int] = []

    class Config:
        from_attributes = True

class ModuleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    order_index: int
    concepts: List[ConceptSummary] = []

    class Config:
        from_attributes = True

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    modules: List[ModuleResponse] = []

    class Config:
        from_attributes = True
