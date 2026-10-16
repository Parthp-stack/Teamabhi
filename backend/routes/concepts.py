from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.models.user import User
from backend.models.concept import Concept
from backend.models.mastery import StudentMastery
from backend.models.question import Attempt
from backend.utils.security import get_current_user
from backend.services.mastery_service import MasteryService

router = APIRouter(prefix="/concepts", tags=["Concepts"])

@router.get("/graph")
def get_concept_graph(
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # If trainer specifies student_id, use it; otherwise use logged in student
    target_student_id = current_user.id
    if student_id and current_user.role == "TRAINER":
        target_student_id = student_id

    concepts: List[Concept] = db.query(Concept).all()

    # Load masteries for target student
    masteries = {
        m.concept_id: m for m in db.query(StudentMastery).filter(
            StudentMastery.student_id == target_student_id
        ).all()
    }

    nodes = []
    edges = []

    # Layout coordinates for OOP pipeline
    # Classes -> Objects -> Constructors -> Inheritance -> Polymorphism -> Dependency Injection
    layout_map = {
        "Classes": {"x": 80, "y": 180},
        "Objects": {"x": 300, "y": 180},
        "Constructors": {"x": 520, "y": 180},
        "Inheritance": {"x": 740, "y": 180},
        "Polymorphism": {"x": 960, "y": 180},
        "Dependency Injection": {"x": 1180, "y": 180}
    }

    for idx, c in enumerate(concepts):
        m = masteries.get(c.id)
        score = m.mastery if m else 0.0
        attempts = m.attempts if m else 0
        correct_attempts = m.correct_attempts if m else 0
        accuracy = round((correct_attempts / attempts * 100), 1) if attempts > 0 else 0.0

        # Check if prereqs are met
        prereq_ids = [p.id for p in c.prerequisites]
        prereqs_met = True
        for pid in prereq_ids:
            pm = masteries.get(pid)
            if not pm or pm.mastery < 65.0:
                prereqs_met = False
                break

        status = MasteryService.get_concept_status(score, prereqs_met)
        pos = layout_map.get(c.name, {"x": 80 + idx * 220, "y": 180})

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
                "prerequisites": prereq_ids,
                "dependents": [d.id for d in c.dependents]
            }
        })

        # Add directed edges from prerequisites to this concept
        for p in c.prerequisites:
            edges.append({
                "id": f"e{p.id}-{c.id}",
                "source": str(p.id),
                "target": str(c.id),
                "animated": status in ["LEARNING", "WEAK"],
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

    mastery = db.query(StudentMastery).filter(
        StudentMastery.student_id == target_student_id,
        StudentMastery.concept_id == concept_id
    ).first()

    score = mastery.mastery if mastery else 0.0
    attempts = mastery.attempts if mastery else 0
    correct = mastery.correct_attempts if mastery else 0
    accuracy = round((correct / attempts * 100), 1) if attempts > 0 else 0.0

    # Prereqs info
    prereqs_info = [
        {"id": p.id, "name": p.name, "description": p.description}
        for p in concept.prerequisites
    ]
    dependents_info = [
        {"id": d.id, "name": d.name, "description": d.description}
        for d in concept.dependents
    ]

    # Recent attempts
    recent_attempts = db.query(Attempt).filter(
        Attempt.student_id == target_student_id,
        Attempt.question.has(concept_id=concept_id)
    ).order_by(Attempt.timestamp.desc()).limit(10).all()

    attempts_data = [
        {
            "id": a.id,
            "question_title": a.question.title,
            "correct": a.correct,
            "timestamp": a.timestamp.isoformat()
        }
        for a in recent_attempts
    ]

    return {
        "id": concept.id,
        "name": concept.name,
        "description": concept.description,
        "mastery": score,
        "status": MasteryService.get_concept_status(score, True),
        "attempts": attempts,
        "correct_attempts": correct,
        "accuracy": accuracy,
        "prerequisites": prereqs_info,
        "dependents": dependents_info,
        "recent_attempts": attempts_data
    }
