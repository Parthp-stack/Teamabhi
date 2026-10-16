from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class ConceptNodeData(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    mastery: float
    status: str # MASTERED, LEARNING, WEAK, LOCKED
    attempts: int
    correct_attempts: int
    accuracy: float
    prerequisites: List[int] = []
    dependents: List[int] = []

class ConceptGraphNode(BaseModel):
    id: str
    position: Dict[str, float]
    data: ConceptNodeData
    type: Optional[str] = "conceptNode"

class ConceptGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: Optional[bool] = False
    style: Optional[Dict[str, Any]] = None

class ConceptGraphResponse(BaseModel):
    nodes: List[ConceptGraphNode]
    edges: List[ConceptGraphEdge]

class ConceptDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    mastery: float
    status: str
    attempts: int
    correct_attempts: int
    accuracy: float
    prerequisites: List[Dict[str, Any]] = []
    dependents: List[Dict[str, Any]] = []
    recent_attempts: List[Dict[str, Any]] = []
