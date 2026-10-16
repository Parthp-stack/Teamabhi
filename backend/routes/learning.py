from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from backend.database import get_db
from backend.models.user import User
from backend.models.question import Question, Attempt
from backend.models.concept import Concept
from backend.schemas.question import QuestionAttemptRequest, QuestionAttemptResult
from backend.utils.security import get_current_user
from backend.services.adaptive_engine import AdaptiveEngine
from backend.services.mastery_service import MasteryService
from backend.services.ai_service import AIService

router = APIRouter(prefix="/learning", tags=["Adaptive Learning"])

@router.get("/next")
def get_next_activity(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Core adaptive learning endpoint:
    Returns the next optimal question determined by student mastery & prerequisite graph.
    """
    result = AdaptiveEngine.get_next_learning_activity(db, current_user.id, course_id)
    return result

@router.post("/attempt", response_model=QuestionAttemptResult)
def submit_question_attempt(
    attempt_in: QuestionAttemptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    question = db.query(Question).filter(Question.id == attempt_in.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Evaluate answer (case-insensitive strip for short answer, exact match for MCQ)
    student_ans_clean = attempt_in.answer.strip().lower()
    correct_ans_clean = question.correct_answer.strip().lower()

    # If MCQ, check direct match
    is_correct = (student_ans_clean == correct_ans_clean)

    # If short answer and options array provided, check if in accepted list
    if not is_correct and question.type == "SHORT_ANSWER" and question.options:
        accepted = [opt.strip().lower() for opt in question.options]
        if student_ans_clean in accepted:
            is_correct = True

    # Save attempt
    attempt = Attempt(
        student_id=current_user.id,
        question_id=question.id,
        answer=attempt_in.answer,
        correct=is_correct
    )
    db.add(attempt)
    db.commit()

    # Update knowledge tracing model
    mastery_update = MasteryService.update_mastery(
        db=db,
        student_id=current_user.id,
        concept_id=question.concept_id,
        is_correct=is_correct,
        difficulty=question.difficulty,
        reason_detail=f"Question #{question.id}: '{question.title}'"
    )

    concept = db.query(Concept).filter(Concept.id == question.concept_id).first()

    return QuestionAttemptResult(
        question_id=question.id,
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        previous_mastery=mastery_update["previous_mastery"],
        new_mastery=mastery_update["new_mastery"],
        mastery_change=mastery_update["delta"],
        concept_id=question.concept_id,
        concept_name=concept.name if concept else "Concept"
    )

@router.post("/hint")
async def get_question_hint(
    question_id: int,
    current_answer: Optional[str] = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    hint = await AIService.generate_hint(question.description, current_answer or "")
    return {"question_id": question_id, "hint": hint}
