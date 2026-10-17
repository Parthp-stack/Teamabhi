from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.models.course import Course, Module
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
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_student_id = current_user.id
    if student_id and current_user.role == "TRAINER":
        target_student_id = student_id

    query = db.query(Concept).order_by(Concept.order_index.asc())
    if course_id:
        query = query.join(Concept.module).filter(Module.course_id == course_id)
    concepts: List[Concept] = query.all()

    # Load masteries for target student
    masteries = {
        m.concept_id: m for m in db.query(StudentMastery).filter(
            StudentMastery.student_id == target_student_id
        ).all()
    }
    mastery_map = {cid: float(rec.mastery_score) for cid, rec in masteries.items()}

    nodes = []
    edges = []

    # 2D Tiered DAG layout coordinates for clean multi-row clusters (fixed square nodes):
    layout_map = {
        # Course 1: Object Oriented Programming (Hierarchical DAG)
        "Programming Basics": {"x": 80, "y": 80},
        "Classes": {"x": 280, "y": 80},
        "Objects": {"x": 480, "y": 30},
        "Constructors": {"x": 480, "y": 220},
        "Encapsulation": {"x": 680, "y": 30},
        "Inheritance": {"x": 680, "y": 220},
        "Polymorphism": {"x": 880, "y": 220},
        "Dependency Injection": {"x": 1080, "y": 220},

        # Course 2: Data Structures (Curriculum Modules)
        # Searching Module
        "Linear Search": {"x": 80, "y": 420},
        "Binary Search": {"x": 280, "y": 420},
        "Sentinel Search": {"x": 480, "y": 420},
        # Sorting Module
        "Bubble Sort": {"x": 80, "y": 620},
        "Merge Sort": {"x": 280, "y": 620},
        "Quick Sort": {"x": 480, "y": 620},
        # Linked List Module
        "Singly Linked List": {"x": 720, "y": 420},
        "Doubly Linked List": {"x": 920, "y": 420},
        # Stack & Queue Modules
        "Stack Operations": {"x": 720, "y": 620},
        "Valid Parentheses": {"x": 920, "y": 620},
        "Queue Basics": {"x": 720, "y": 820},
        "Circular Queue": {"x": 920, "y": 820}
    }

    concept_id_set = {c.id for c in concepts}

    for idx, c in enumerate(concepts):
        m = masteries.get(c.id)
        score = float(m.mastery_score) if m else 0.0
        attempts = m.attempts if m else 0
        correct_attempts = m.correct_attempts if m else 0
        accuracy = round((correct_attempts / attempts * 100), 1) if attempts > 0 else 0.0

        prereq_eval = AdaptiveEngine.evaluate_prerequisites(c, mastery_map)
        status = MasteryService.get_concept_status(score, prereq_eval["eligible"])
        
        # 2D grid fallback if concept not explicitly mapped (avoids single straight line)
        pos = layout_map.get(c.name, {"x": 80 + (idx % 4) * 200, "y": 80 + (idx // 4) * 200})

        course_title = "Data Structures"
        module_title = "General"
        course_id_val = None
        if c.module:
            module_title = c.module.title
            if c.module.course:
                course_title = c.module.course.title
                course_id_val = c.module.course.id

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
                "course_id": course_id_val,
                "course_title": course_title,
                "module_title": module_title,
                "prerequisites": [p.id for p in c.prerequisites],
                "dependents": [d.id for d in c.dependents]
            }
        })

        for p in c.prerequisites:
            if p.id in concept_id_set:
                edges.append({
                    "id": f"e{p.id}-{c.id}",
                    "source": str(p.id),
                    "target": str(c.id),
                    "animated": status in ["DEVELOPING", "WEAK"],
                    "style": {"stroke": "#6366f1", "strokeWidth": 2}
                })

    courses_list = [
        {"id": course.id, "title": course.title}
        for course in db.query(Course).all()
    ]

    return {"nodes": nodes, "edges": edges, "courses": courses_list}

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
