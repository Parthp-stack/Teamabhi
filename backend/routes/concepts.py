from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.models.user import User
from backend.models.concept import Concept
from backend.models.mastery import StudentMastery
from backend.models.question import Attempt
from backend.utils.security import get_current_user
from backend.services.mastery_service import MasteryService
from backend.services.adaptive_engine import AdaptiveEngine

router = APIRouter(prefix="/concepts", tags=["Concepts"])

@router.get("/graph")
def get_concept_graph(
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_student_id = current_user.id
    if student_id and current_user.role == "TRAINER":
        target_student_id = student_id

    concepts: List[Concept] = db.query(Concept).order_by(Concept.order_index.asc()).all()

    # Load masteries for target student
    masteries = {
        m.concept_id: m for m in db.query(StudentMastery).filter(
            StudentMastery.student_id == target_student_id
        ).all()
    }
    mastery_map = {cid: float(rec.mastery_score) for cid, rec in masteries.items()}

    nodes = []
    edges = []

    # Horizontal DAG layout coordinates for the 7 concepts:
    # Programming Basics -> Classes -> Objects -> Constructors -> Inheritance -> Polymorphism -> Dependency Injection
    layout_map = {
        "Programming Basics": {"x": 50, "y": 180},
        "Classes": {"x": 260, "y": 180},
        "Objects": {"x": 470, "y": 180},
        "Constructors": {"x": 680, "y": 180},
        "Inheritance": {"x": 890, "y": 180},
        "Polymorphism": {"x": 1100, "y": 180},
        "Dependency Injection": {"x": 1310, "y": 180}
    }

    for idx, c in enumerate(concepts):
        m = masteries.get(c.id)
        score = float(m.mastery_score) if m else 0.0
        attempts = m.attempts if m else 0
        correct_attempts = m.correct_attempts if m else 0
        accuracy = round((correct_attempts / attempts * 100), 1) if attempts > 0 else 0.0

        prereq_eval = AdaptiveEngine.evaluate_prerequisites(c, mastery_map)
        status = MasteryService.get_concept_status(score, prereq_eval["eligible"])
        pos = layout_map.get(c.name, {"x": 50 + idx * 210, "y": 180})

        nodes.append({
            "id": str(c.id),
            "position": pos,
            "type": "conceptNode",
            "data": {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "mastery": score,
                "status": status,
                "attempts": attempts,
                "correct_attempts": correct_attempts,
                "accuracy": accuracy,
                "prerequisites": [p.id for p in c.prerequisites],
                "dependents": [d.id for d in c.dependents]
            }
        })

        for p in c.prerequisites:
            edges.append({
                "id": f"e{p.id}-{c.id}",
                "source": str(p.id),
                "target": str(c.id),
                "animated": status in ["DEVELOPING", "WEAK"],
                "style": {"stroke": "#6366f1", "strokeWidth": 2}
            })

    return {"nodes": nodes, "edges": edges}

@router.get("/{concept_id}")
def get_concept_detail(
    concept_id: int,
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_student_id = current_user.id
    if student_id and current_user.role == "TRAINER":
        target_student_id = student_id

    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    m = db.query(StudentMastery).filter(
        StudentMastery.student_id == target_student_id,
        StudentMastery.concept_id == concept_id
    ).first()

    score = float(m.mastery_score) if m else 0.0
    attempts = m.attempts if m else 0
    correct = m.correct_attempts if m else 0
    accuracy = round((correct / attempts * 100), 1) if attempts > 0 else 0.0

    recent_attempts = db.query(Attempt).filter(
        Attempt.student_id == target_student_id,
        Attempt.question.has(concept_id=concept_id)
    ).order_by(Attempt.created_at.desc()).limit(10).all()

    attempts_data = [
        {
            "id": a.id,
            "question_text": a.question.question_text[:60] + "...",
            "selected_answer": a.selected_answer,
            "is_correct": a.is_correct,
            "timestamp": a.created_at.isoformat()
        }
        for a in recent_attempts
    ]

    return {
        "id": concept.id,
        "name": concept.name,
        "description": concept.description,
        "difficulty": concept.difficulty,
        "mastery": score,
        "status": MasteryService.get_concept_status(score, True),
        "attempts": attempts,
        "correct_attempts": correct,
        "accuracy": accuracy,
        "prerequisites": [{"id": p.id, "name": p.name} for p in concept.prerequisites],
        "dependents": [{"id": d.id, "name": d.name} for d in concept.dependents],
        "recent_attempts": attempts_data
    }
