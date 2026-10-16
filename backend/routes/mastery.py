from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models.user import User
from backend.models.concept import Concept
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.schemas.mastery import (
    StudentMasteryResponse,
    MasteryUpdateRequest,
    MasteryHistoryResponse,
    StudentMasteryOverview
)
from backend.utils.security import get_current_user, require_trainer
from backend.services.mastery_service import MasteryService

router = APIRouter(prefix="/mastery", tags=["Mastery"])

def build_student_overview(db: Session, student: User) -> StudentMasteryOverview:
    concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()
    masteries = {
        m.concept_id: m for m in db.query(StudentMastery).filter(
            StudentMastery.student_id == student.id
        ).all()
    }

    concept_responses = []
    total_mastery = 0.0

    for c in concepts:
        m = masteries.get(c.id)
        score = float(m.mastery_score) if m else 0.0
        attempts = m.attempts if m else 0
        correct = m.correct_attempts if m else 0
        total_mastery += score

        concept_responses.append(StudentMasteryResponse(
            id=m.id if m else 0,
            student_id=student.id,
            concept_id=c.id,
            concept_name=c.name,
            mastery=score,
            attempts=attempts,
            correct_attempts=correct,
            status=MasteryService.get_concept_status(score, True),
            updated_at=m.last_attempt_at if m and m.last_attempt_at else student.created_at
        ))

    overall_avg = round(total_mastery / len(concepts), 1) if concepts else 0.0

    weak = [c for c in concept_responses if c.mastery < 50.0]
    strong = [c for c in concept_responses if c.mastery >= 75.0]
    recommended = weak[0].concept_name if weak else (concept_responses[0].concept_name if concept_responses else None)

    return StudentMasteryOverview(
        student_id=student.id,
        student_name=student.name,
        overall_mastery=overall_avg,
        concepts=concept_responses,
        weak_concepts=weak,
        strong_concepts=strong,
        recommended_concept=recommended
    )

@router.get("", response_model=StudentMasteryOverview)
def get_my_mastery(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_student_overview(db, current_user)

@router.get("/{student_id}", response_model=StudentMasteryOverview)
def get_student_mastery(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "TRAINER" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    target_student = db.query(User).filter(User.id == student_id).first()
    if not target_student:
        raise HTTPException(status_code=404, detail="Student not found")

    return build_student_overview(db, target_student)

@router.get("/{student_id}/history", response_model=List[MasteryHistoryResponse])
def get_mastery_history(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "TRAINER" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    records = db.query(MasteryHistory).filter(
        MasteryHistory.student_id == student_id
    ).order_by(MasteryHistory.timestamp.asc()).all()

    results = []
    for r in records:
        concept = db.query(Concept).filter(Concept.id == r.concept_id).first()
        results.append(MasteryHistoryResponse(
            id=r.id,
            concept_id=r.concept_id,
            concept_name=concept.name if concept else f"Concept #{r.concept_id}",
            mastery=float(r.mastery_score),
            change_amount=float(r.change_amount),
            reason=r.reason,
            timestamp=r.timestamp
        ))
    return results

@router.post("/update")
def manual_update_mastery(
    update_data: MasteryUpdateRequest,
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    target_student_id = update_data.student_id or current_user.id
    record = MasteryService.get_or_create_mastery(db, target_student_id, update_data.concept_id)
    new_score = max(0.0, min(100.0, float(record.mastery_score) + update_data.score_delta))
    record.mastery_score = round(new_score, 1)

    hist = MasteryHistory(
        student_id=target_student_id,
        concept_id=update_data.concept_id,
        mastery_score=record.mastery_score,
        change_amount=update_data.score_delta,
        reason=update_data.reason or f"Trainer manual adjustment ({current_user.name})"
    )
    db.add(hist)
    db.commit()
    db.refresh(record)

    return {"message": "Mastery updated", "student_id": target_student_id, "concept_id": update_data.concept_id, "new_mastery": record.mastery_score}
