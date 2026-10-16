from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.coding import CodingSubmission
from backend.models.explanation import ExplanationQuestion, ExplanationAnswer
from backend.schemas.explanation import (
    ExplanationQuestionResponse,
    ExplanationAnswersSubmitRequest,
    ExplanationResultResponse,
    EvaluatedAnswerResponse
)
from backend.utils.security import get_current_user
from backend.services.ai_service import AIService

router = APIRouter(prefix="/explanation", tags=["Explain Your Code (Viva)"])

@router.get("/submission/{submission_id}/questions", response_model=List[ExplanationQuestionResponse])
def get_submission_questions(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(CodingSubmission).filter(CodingSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    questions = db.query(ExplanationQuestion).filter(
        ExplanationQuestion.submission_id == submission_id
    ).all()

    return questions

@router.post("/submit", response_model=ExplanationResultResponse)
async def submit_explanation_answers(
    req: ExplanationAnswersSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not req.answers:
        raise HTTPException(status_code=400, detail="No answers provided")

    first_q = db.query(ExplanationQuestion).filter(
        ExplanationQuestion.id == req.answers[0].question_id
    ).first()
    if not first_q:
        raise HTTPException(status_code=404, detail="Question not found")

    sub = first_q.submission
    evaluated_list: List[EvaluatedAnswerResponse] = []
    total_score = 0.0

    for item in req.answers:
        q = db.query(ExplanationQuestion).filter(ExplanationQuestion.id == item.question_id).first()
        if not q:
            continue

        # AI evaluation of technical consistency against the actual source code
        eval_result = await AIService.evaluate_explanation(
            source_code=sub.source_code,
            question=q.question,
            expected_concept=q.expected_concept or "Implementation Structure",
            student_answer=item.student_answer
        )

        # Save or update answer record
        ans_record = db.query(ExplanationAnswer).filter(
            ExplanationAnswer.explanation_question_id == q.id
        ).first()

        if not ans_record:
            ans_record = ExplanationAnswer(
                explanation_question_id=q.id,
                student_answer=item.student_answer,
                evaluation=eval_result["evaluation"],
                score=eval_result["score"]
            )
            db.add(ans_record)
        else:
            ans_record.student_answer = item.student_answer
            ans_record.evaluation = eval_result["evaluation"]
            ans_record.score = eval_result["score"]

        total_score += eval_result["score"]
        evaluated_list.append(EvaluatedAnswerResponse(
            question_id=q.id,
            question=q.question,
            student_answer=item.student_answer,
            evaluation=eval_result["evaluation"],
            score=eval_result["score"]
        ))

    db.commit()

    count = len(evaluated_list)
    avg_score = round(total_score / count, 1) if count > 0 else 0.0

    summary = (
        f"Demonstrated solid conceptual grasp of {count} viva questions ({avg_score}/10)."
        if avg_score >= 7.0 else
        f"Partial code alignment ({avg_score}/10). Recommended for human trainer review."
    )

    return ExplanationResultResponse(
        submission_id=sub.id,
        overall_understanding_score=avg_score,
        evaluated_answers=evaluated_list,
        summary_review=summary,
        needs_review=(avg_score < 7.0)
    )

@router.get("/submission/{submission_id}/results", response_model=ExplanationResultResponse)
def get_explanation_results(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    questions = db.query(ExplanationQuestion).filter(
        ExplanationQuestion.submission_id == submission_id
    ).all()

    if not questions:
        raise HTTPException(status_code=404, detail="No explanation questions found for submission")

    evaluated_list: List[EvaluatedAnswerResponse] = []
    total_score = 0.0

    for q in questions:
        ans = db.query(ExplanationAnswer).filter(
            ExplanationAnswer.explanation_question_id == q.id
        ).first()

        score = ans.score if ans else 0.0
        evaluation = ans.evaluation if ans else "Awaiting submission"
        student_ans = ans.student_answer if ans else ""

        total_score += score
        evaluated_list.append(EvaluatedAnswerResponse(
            question_id=q.id,
            question=q.question,
            student_answer=student_ans,
            evaluation=evaluation,
            score=score
        ))

    count = len(evaluated_list)
    avg_score = round(total_score / count, 1) if count > 0 else 0.0

    return ExplanationResultResponse(
        submission_id=submission_id,
        overall_understanding_score=avg_score,
        evaluated_answers=evaluated_list,
        summary_review=f"Overall Comprehension Score: {avg_score}/10",
        needs_review=(avg_score < 7.0)
    )
