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

def classify_understanding_verdict(is_code_correct: bool, is_understood: bool) -> str:
    if is_code_correct and is_understood:
        return "Correct code + understood"
    elif is_code_correct and not is_understood:
        return "Correct code + poor understanding"
    elif not is_code_correct and is_understood:
        return "Wrong code + good conceptual understanding"
    else:
        return "Wrong code + poor understanding"

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

    count = len(evaluated_list)
    avg_score = round(total_score / count, 1) if count > 0 else 0.0

    # 4-tier Understanding Verdict analysis
    is_code_correct = (sub.status == "PASSED" or (sub.score is not None and sub.score >= 100.0))
    is_understood = (avg_score >= 7.0)

    verdict = classify_understanding_verdict(is_code_correct, is_understood)
    if verdict == "Correct code + understood":
        diff_rec = "ADVANCED"
        next_q_rec = "Explore non-linear and logarithmic boundary optimization problems"
    elif verdict == "Correct code + poor understanding":
        diff_rec = "CONCEPTUAL_REINFORCEMENT"
        next_q_rec = "Targeted viva practice on state invariants and algorithmic mechanics"
    elif verdict == "Wrong code + good conceptual understanding":
        diff_rec = "SYNTAX_DEBUGGING"
        next_q_rec = "Syntax and boundary debugging practice on same concept"
    else:
        diff_rec = "FOUNDATIONAL"
        next_q_rec = "Foundational tutorial and beginner concept practice"

    strengths = [ans.question for ans in evaluated_list if ans.score >= 7.0]
    weaknesses = [ans.question for ans in evaluated_list if ans.score < 7.0]

    summary = (
        f"Verdict: {verdict}. Comprehension: {avg_score}/10 across {count} questions."
    )

    # Save to AIEvaluation table
    from backend.models.ai_evaluation import AIEvaluation
    ai_eval = db.query(AIEvaluation).filter(AIEvaluation.submission_id == sub.id).first()
    if not ai_eval:
        ai_eval = AIEvaluation(
            student_id=sub.student_id,
            question_id=None,
            concept_id=None,
            submission_id=sub.id,
            score=avg_score,
            understanding_verdict=verdict,
            feedback=summary,
            detected_weaknesses=weaknesses,
            detected_strengths=strengths,
            difficulty_recommendation=diff_rec,
            next_question_recommendation=next_q_rec
        )
        db.add(ai_eval)
    else:
        ai_eval.score = avg_score
        ai_eval.understanding_verdict = verdict
        ai_eval.feedback = summary
        ai_eval.detected_weaknesses = weaknesses
        ai_eval.detected_strengths = strengths
        ai_eval.difficulty_recommendation = diff_rec
        ai_eval.next_question_recommendation = next_q_rec

    sub.viva_verdict = verdict
    sub.ai_feedback = summary
    db.commit()

    return ExplanationResultResponse(
        submission_id=sub.id,
        overall_understanding_score=avg_score,
        understanding_verdict=verdict,
        evaluated_answers=evaluated_list,
        summary_review=summary,
        needs_review=(avg_score < 7.0 or not is_code_correct),
        detected_weaknesses=weaknesses,
        detected_strengths=strengths,
        difficulty_recommendation=diff_rec,
        next_question_recommendation=next_q_rec
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

    from backend.models.ai_evaluation import AIEvaluation
    ai_eval = db.query(AIEvaluation).filter(AIEvaluation.submission_id == submission_id).first()

    verdict = ai_eval.understanding_verdict if ai_eval else ("Under Review" if count > 0 else "Pending")
    strengths = ai_eval.detected_strengths if ai_eval else []
    weaknesses = ai_eval.detected_weaknesses if ai_eval else []
    diff_rec = ai_eval.difficulty_recommendation if ai_eval else None
    next_q_rec = ai_eval.next_question_recommendation if ai_eval else None

    return ExplanationResultResponse(
        submission_id=submission_id,
        overall_understanding_score=avg_score,
        understanding_verdict=verdict,
        evaluated_answers=evaluated_list,
        summary_review=ai_eval.feedback if ai_eval else f"Overall Comprehension Score: {avg_score}/10",
        needs_review=(avg_score < 7.0),
        detected_weaknesses=weaknesses,
        detected_strengths=strengths,
        difficulty_recommendation=diff_rec,
        next_question_recommendation=next_q_rec
    )

@router.get("/evaluations/student")
def get_student_ai_evaluations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from backend.models.ai_evaluation import AIEvaluation
    evals = db.query(AIEvaluation).filter(
        AIEvaluation.student_id == current_user.id
    ).order_by(AIEvaluation.timestamp.desc()).all()

    return [
        {
            "id": e.id,
            "submission_id": e.submission_id,
            "score": e.score,
            "understanding_verdict": e.understanding_verdict,
            "feedback": e.feedback,
            "detected_strengths": e.detected_strengths or [],
            "detected_weaknesses": e.detected_weaknesses or [],
            "difficulty_recommendation": e.difficulty_recommendation,
            "next_question_recommendation": e.next_question_recommendation,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None
        }
        for e in evals
    ]

