from pydantic import BaseModel, field_validator, ConfigDict
from typing import List, Optional, Any

class ConceptSummary(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    prerequisites: List[int] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("prerequisites", mode="before")
    @classmethod
    def extract_prereq_ids(cls, v: Any) -> List[int]:
        if not v:
            return []
        res = []
        for item in v:
            if isinstance(item, int):
                res.append(item)
            elif hasattr(item, "id"):
                res.append(item.id)
            elif hasattr(item, "prerequisite_id"):
                res.append(item.prerequisite_id)
        return res

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
