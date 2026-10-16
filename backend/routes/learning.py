from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.models.user import User
from backend.models.question import Question, Attempt
from backend.models.concept import Concept
from backend.models.mastery import StudentMastery
from backend.utils.security import get_current_user
from backend.services.adaptive_engine import AdaptiveEngine
from backend.services.mastery_service import MasteryService
from backend.services.ai_service import AIService

router = APIRouter(tags=["Adaptive Learning & Questions"])

class AttemptSubmission(BaseModel):
    selected_answer: str
    time_taken: Optional[float] = 0.0

class AttemptResultResponse(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    previous_mastery: float
    new_mastery: float
    mastery_change: float
    concept_id: int
    concept_name: str
    next_recommended_concept: str

# 1. GET /api/questions/next
@router.get("/questions/next")
@router.get("/learning/next")
def get_next_question(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Selects the next question based on the student's weakest eligible prerequisite.
    """
    return AdaptiveEngine.get_next_question(db, current_user.id, course_id)

# 2. POST /api/questions/{question_id}/attempt
@router.post("/questions/{question_id}/attempt", response_model=AttemptResultResponse)
@router.post("/learning/attempt", response_model=AttemptResultResponse)
def submit_question_attempt(
    question_id: int,
    submission: AttemptSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates student answer, creates an Attempt record, updates StudentMastery,
    and returns immediate feedback along with the next recommended concept.
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    student_ans_clean = submission.selected_answer.strip().lower()
    correct_ans_clean = question.correct_answer.strip().lower()

    # Exact match check
    is_correct = (student_ans_clean == correct_ans_clean)

    # Check accepted options for short answers
    if not is_correct and question.options:
        accepted = [opt.strip().lower() for opt in question.options]
        if student_ans_clean in accepted:
            is_correct = True

    # Record Attempt
    attempt = Attempt(
        student_id=current_user.id,
        question_id=question.id,
        selected_answer=submission.selected_answer,
        is_correct=is_correct,
        score=1.0 if is_correct else 0.0,
        time_taken=submission.time_taken or 0.0
    )
    db.add(attempt)
    db.commit()

    # Update StudentMastery using explainable Bayesian logic
    mastery_result = MasteryService.update_mastery(
        db=db,
        student_id=current_user.id,
        concept_id=question.concept_id,
        is_correct=is_correct,
        difficulty=question.difficulty,
        reason_detail=f"Q#{question.id} '{question.question_text[:40]}...'"
    )

    concept = db.query(Concept).filter(Concept.id == question.concept_id).first()

    # Recalculate next recommended concept
    next_activity = AdaptiveEngine.get_next_question(db, current_user.id)
    next_rec = next_activity.get("concept", concept.name if concept else "Next Concept")

    return AttemptResultResponse(
        question_id=question.id,
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        previous_mastery=mastery_result["previous_mastery"],
        new_mastery=mastery_result["new_mastery"],
        mastery_change=mastery_result["delta"],
        concept_id=question.concept_id,
        concept_name=concept.name if concept else "Concept",
        next_recommended_concept=next_rec
    )

# 3. GET /api/student/mastery
@router.get("/student/mastery")
def get_student_mastery_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns student's overall mastery score and concept competencies.
    """
    concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()
    mastery_map = {m.concept_id: m for m in db.query(StudentMastery).filter(StudentMastery.student_id == current_user.id).all()}

    results = []
    total_score = 0.0

    for c in concepts:
        m = mastery_map.get(c.id)
        score = float(m.mastery_score) if m else 0.0
        total_score += score
        attempts_count = m.attempts if m else 0
        correct_count = m.correct_attempts if m else 0

        # Check prerequisite status
        prereq_eval = AdaptiveEngine.evaluate_prerequisites(c, {cid: float(rec.mastery_score) for cid, rec in mastery_map.items()})
        status = MasteryService.get_concept_status(score, prereq_eval["eligible"])

        results.append({
            "concept_id": c.id,
            "concept_name": c.name,
            "description": c.description,
            "difficulty": c.difficulty,
            "mastery_score": score,
            "status": status,
            "attempts": attempts_count,
            "correct_attempts": correct_count,
            "accuracy": round((correct_count / attempts_count * 100), 1) if attempts_count > 0 else 0.0,
            "eligible": prereq_eval["eligible"],
            "prerequisites": [p.name for p in c.prerequisites],
            "last_attempt_at": m.last_attempt_at.isoformat() if m and m.last_attempt_at else None
        })

    avg_mastery = round(total_score / len(concepts), 1) if concepts else 0.0

    return {
        "student_id": current_user.id,
        "student_name": current_user.name,
        "overall_mastery": avg_mastery,
        "concepts": results
    }

# 4. GET /api/student/weak-concepts
@router.get("/student/weak-concepts")
def get_student_weak_concepts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Identifies weak concepts (< 50% mastery or unfulfilled prerequisites).
    """
    concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()
    mastery_map = {m.concept_id: float(m.mastery_score) for m in db.query(StudentMastery).filter(StudentMastery.student_id == current_user.id).all()}

    weak_list = []
    for c in concepts:
        score = mastery_map.get(c.id, 0.0)
        prereq_eval = AdaptiveEngine.evaluate_prerequisites(c, mastery_map)

        if score < 50.0:
            weak_list.append({
                "concept_id": c.id,
                "name": c.name,
                "mastery_score": score,
                "eligible": prereq_eval["eligible"],
                "reason": "Mastery competency is below 50%" if prereq_eval["eligible"] else f"Prerequisites incomplete: {', '.join([b['name'] for b in prereq_eval['blocking_prereqs']])}"
            })

    return {
        "student_id": current_user.id,
        "weak_concepts_count": len(weak_list),
        "weak_concepts": weak_list
    }

# 5. GET /api/learning/path
@router.get("/learning/path")
def get_adaptive_learning_path(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the student's dynamic learning path overview.
    """
    return AdaptiveEngine.get_learning_path(db, current_user.id)
