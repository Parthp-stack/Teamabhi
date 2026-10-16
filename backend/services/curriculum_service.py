from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict, Set, Optional, Tuple, Any
from backend.models.course import Course, Module
from backend.models.concept import Concept, ConceptPrerequisite
from backend.models.question import Question
from backend.schemas.curriculum import (
    CourseCreateRequest, CourseUpdateRequest,
    ModuleCreateRequest, ModuleUpdateRequest,
    ConceptCreateRequest, ConceptUpdateRequest,
    QuestionCreateRequest, QuestionUpdateRequest
)

class CurriculumService:

    @staticmethod
    def detect_prerequisite_cycle(db: Session, target_concept_id: int, proposed_prerequisite_id: int) -> Optional[List[str]]:
        """
        Detects if adding 'proposed_prerequisite_id' as a prerequisite to 'target_concept_id'
        would introduce a cycle in the prerequisite DAG.

        In our graph:
        P is a prerequisite of C means: P -> C (P comes before C).
        Adding proposed_prereq -> target_concept creates a cycle if and only if
        there is already a path from target_concept -> ... -> proposed_prereq!

        Returns:
            List of concept names forming the cycle if a cycle is detected, or None if safe.
        """
        if target_concept_id == proposed_prerequisite_id:
            concept = db.query(Concept).filter(Concept.id == target_concept_id).first()
            name = concept.name if concept else f"Concept #{target_concept_id}"
            return [name, name]

        # Build adjacency map of existing prerequisites: parent -> list of children (dependents)
        # i.e., prerequisite_id -> list of concept_ids that depend on it
        all_edges = db.query(ConceptPrerequisite).all()
        adj: Dict[int, List[int]] = {}
        for edge in all_edges:
            adj.setdefault(edge.prerequisite_id, []).append(edge.concept_id)

        # Check if there is a path from target_concept_id to proposed_prerequisite_id
        # using DFS to also reconstruct the cycle path
        visited: Set[int] = set()
        path: List[int] = []

        def dfs(curr: int) -> bool:
            visited.add(curr)
            path.append(curr)

            if curr == proposed_prerequisite_id:
                return True

            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True

            path.pop()
            return False

        has_path = dfs(target_concept_id)
        if has_path:
            # We found path: target_concept -> ... -> proposed_prereq.
            # Adding proposed_prereq -> target_concept creates:
            # proposed_prereq -> target_concept -> ... -> proposed_prereq!
            full_cycle_ids = [proposed_prerequisite_id] + path
            id_to_name = {
                c.id: c.name for c in db.query(Concept).filter(Concept.id.in_(full_cycle_ids)).all()
            }
            return [id_to_name.get(cid, f"#{cid}") for cid in full_cycle_ids]

        return None

    @staticmethod
    def add_prerequisite(db: Session, concept_id: int, prerequisite_id: int) -> Dict[str, Any]:
        concept = db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            raise HTTPException(status_code=404, detail="Target concept not found")

        prereq = db.query(Concept).filter(Concept.id == prerequisite_id).first()
        if not prereq:
            raise HTTPException(status_code=404, detail="Prerequisite concept not found")

        # Check existing
        existing = db.query(ConceptPrerequisite).filter(
            ConceptPrerequisite.concept_id == concept_id,
            ConceptPrerequisite.prerequisite_id == prerequisite_id
        ).first()
        if existing:
            return {"message": "Prerequisite relationship already exists", "concept": concept.name, "prerequisite": prereq.name}

        # Cycle detection validation
        cycle_path = CurriculumService.detect_prerequisite_cycle(db, concept_id, prerequisite_id)
        if cycle_path:
            cycle_str = " -> ".join(cycle_path)
            raise HTTPException(
                status_code=400,
                detail=f"Circular prerequisite error: Adding '{prereq.name}' as prerequisite to '{concept.name}' creates a cycle: {cycle_str}"
            )

        edge = ConceptPrerequisite(concept_id=concept_id, prerequisite_id=prerequisite_id)
        db.add(edge)
        db.commit()

        return {
            "message": "Prerequisite added successfully",
            "concept_id": concept_id,
            "concept_name": concept.name,
            "prerequisite_id": prerequisite_id,
            "prerequisite_name": prereq.name
        }

    @staticmethod
    def remove_prerequisite(db: Session, concept_id: int, prerequisite_id: int) -> Dict[str, Any]:
        edge = db.query(ConceptPrerequisite).filter(
            ConceptPrerequisite.concept_id == concept_id,
            ConceptPrerequisite.prerequisite_id == prerequisite_id
        ).first()
        if not edge:
            raise HTTPException(status_code=404, detail="Prerequisite relationship not found")

        db.delete(edge)
        db.commit()
        return {"message": "Prerequisite removed successfully"}

    @staticmethod
    def create_concept(db: Session, req: ConceptCreateRequest) -> Concept:
        module = db.query(Module).filter(Module.id == req.module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        concept = Concept(
            module_id=req.module_id,
            name=req.name,
            description=req.description,
            difficulty=req.difficulty,
            order_index=req.order_index or 0
        )
        db.add(concept)
        db.commit()
        db.refresh(concept)
        return concept

    @staticmethod
    def update_concept(db: Session, concept_id: int, req: ConceptUpdateRequest) -> Concept:
        concept = db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")

        if req.name is not None:
            concept.name = req.name
        if req.description is not None:
            concept.description = req.description
        if req.difficulty is not None:
            concept.difficulty = req.difficulty
        if req.order_index is not None:
            concept.order_index = req.order_index

        db.commit()
        db.refresh(concept)
        return concept

    @staticmethod
    def delete_concept(db: Session, concept_id: int) -> Dict[str, Any]:
        concept = db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")

        # Remove prerequisites edges
        db.query(ConceptPrerequisite).filter(
            (ConceptPrerequisite.concept_id == concept_id) |
            (ConceptPrerequisite.prerequisite_id == concept_id)
        ).delete(synchronize_session=False)

        db.delete(concept)
        db.commit()
        return {"message": f"Concept '{concept.name}' and associated references deleted"}
