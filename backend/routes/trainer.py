from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.models.course import Course
from backend.models.concept import Concept
from backend.models.mastery import StudentMastery
from backend.utils.security import require_trainer

router = APIRouter(prefix="/trainer", tags=["Trainer Management"])

@router.get("/overview")
@router.get("/dashboard")
def get_trainer_overview(
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    """
    Phase 2 Basic Trainer View:
    Returns Course, Concepts, Number of Students, Average Mastery per concept, and Weakest concepts.
    """
    course = db.query(Course).first()
    students = db.query(User).filter(User.role == UserRole.STUDENT.value).all()
    total_students = len(students)

    concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()
    concept_stats = []
    total_system_mastery = 0.0
    mastery_count = 0

    for c in concepts:
        masteries = db.query(StudentMastery.mastery_score).filter(StudentMastery.concept_id == c.id).all()
        scores = [float(m[0]) for m in masteries]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        concept_stats.append({
            "id": c.id,
            "name": c.name,
            "difficulty": c.difficulty,
            "average_mastery": avg_score,
            "student_count": len(scores)
        })
        if scores:
            total_system_mastery += sum(scores)
            mastery_count += len(scores)

    cohort_average = round(total_system_mastery / mastery_count, 1) if mastery_count > 0 else 0.0

    # Sort for weakest concepts
    sorted_by_weakest = sorted(concept_stats, key=lambda x: x["average_mastery"])
    weakest_concepts = sorted_by_weakest[:3]

    # Students overview
    student_summaries = []
    for s in students:
        s_masteries = db.query(StudentMastery.mastery_score).filter(StudentMastery.student_id == s.id).all()
        s_scores = [float(m[0]) for m in s_masteries]
        s_avg = round(sum(s_scores) / len(s_scores), 1) if s_scores else 0.0

        student_summaries.append({
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "average_mastery": s_avg
        })

    return {
        "course": {
            "id": course.id if course else 1,
            "title": course.title if course else "Object Oriented Programming",
            "description": course.description if course else "OOP Curriculum"
        },
        "total_students": total_students,
        "cohort_average_mastery": cohort_average,
        "concepts": concept_stats,
        "weakest_concepts": weakest_concepts,
        "students": student_summaries
    }
