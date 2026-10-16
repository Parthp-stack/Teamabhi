from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.models.user import User
from backend.models.question import Question, Attempt
from backend.models.concept import Concept
from backend.models.coding import CodingSubmission, CodingProblem
from datetime import datetime, timezone
from backend.models.explanation import ExplanationQuestion, ExplanationAnswer
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.session import Session as CodingSession, SessionEvent
from backend.models.integrity import IntegritySignal
from backend.utils.security import get_current_user, require_trainer
from backend.services.adaptive_engine import AdaptiveEngine
from backend.services.mastery_service import MasteryService
from backend.services.ai_service import AIService
from backend.services.mcq_validation_service import MCQValidationService
from backend.models.assessment_attempt import AssessmentAttempt, AssessmentWarning, QuestionAttempt, StudentConceptProgress
from backend.models.integrity import IntegritySignal, IntegrityEvent
from backend.services.integrity_service import IntegrityService

router = APIRouter(tags=["Adaptive Learning & Questions"])

class AttemptSubmission(BaseModel):
    selected_answer: str
    time_taken: Optional[float] = 0.0
    assessment_id: Optional[int] = None
    attempt_number: Optional[int] = None

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
    attempt_number: Optional[int] = 1
    difficulty: Optional[str] = None

class MCQValidationRequest(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: Optional[str] = "MEDIUM"
    concept: Optional[str] = "General"
    use_ai: Optional[bool] = True

# 0. POST /api/questions/validate
@router.post("/questions/validate")
async def validate_mcq_endpoint(
    req: MCQValidationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Validates an MCQ before making it available in an active assessment.
    Performs deterministic syntax, schema, uniqueness, and matching checks,
    followed by AI-assisted ambiguity and correctness analysis.
    """
    payload = req.model_dump()
    if req.use_ai:
        res = await MCQValidationService.validate_mcq_with_ai(payload)
    else:
        res = MCQValidationService.validate_mcq_deterministic(payload)
    return res

# 1. GET /api/questions/next
@router.get("/questions/next")
@router.get("/learning/next")
def get_next_question(
    course_id: Optional[int] = None,
    module_id: Optional[int] = None,
    concept_id: Optional[int] = None,
    assessment_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Selects the next question based on the student's weakest eligible prerequisite,
    prior attempt performance, and calibration difficulty. Avoids repeating questions in the current session.
    """
    res = AdaptiveEngine.get_next_question(
        db=db,
        student_id=current_user.id,
        course_id=course_id,
        module_id=module_id,
        concept_id=concept_id,
        assessment_id=assessment_id
    )
    if isinstance(res, dict) and "question" in res and isinstance(res["question"], dict):
        res["id"] = res["question"].get("id")
        res["question_text"] = res["question"].get("question_text")
        res["concept_name"] = res.get("concept")
        res["options"] = res["question"].get("options")
        res["difficulty"] = res["question"].get("difficulty")
        res["code_snippet"] = res["question"].get("code_snippet")
    return res

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
    Evaluates student answer, creates an Attempt record with time_taken and attempt_number,
    updates StudentMastery with time-calibrated Bayesian logic, and updates AssessmentAttempt if in a session.
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

    # Compute attempt number
    prev_count = db.query(Attempt).filter(
        Attempt.student_id == current_user.id,
        Attempt.question_id == question.id
    ).count()
    attempt_num = submission.attempt_number or (prev_count + 1)

    # Record Attempt with time taken and assessment metadata
    attempt = Attempt(
        student_id=current_user.id,
        question_id=question.id,
        selected_answer=submission.selected_answer,
        is_correct=is_correct,
        score=1.0 if is_correct else 0.0,
        time_taken=submission.time_taken or 0.0,
        assessment_id=submission.assessment_id,
        attempt_number=attempt_num,
        difficulty=question.difficulty,
        concept_id=question.concept_id
    )
    db.add(attempt)
    db.commit()

    # If associated with an active AssessmentAttempt session, update counters
    if submission.assessment_id:
        asst_att = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.id == submission.assessment_id,
            AssessmentAttempt.student_id == current_user.id
        ).first()
        if asst_att:
            asst_att.questions_attempted += 1
            if is_correct:
                asst_att.questions_correct += 1
            asst_att.score = round((asst_att.questions_correct / asst_att.questions_attempted * 100), 1)
            db.commit()

    # Update StudentMastery using explainable Bayesian logic with time-based calibration
    mastery_result = MasteryService.update_mastery(
        db=db,
        student_id=current_user.id,
        concept_id=question.concept_id,
        is_correct=is_correct,
        difficulty=question.difficulty,
        reason_detail=f"Q#{question.id} '{question.question_text[:40]}...'",
        time_taken=submission.time_taken
    )

    concept = db.query(Concept).filter(Concept.id == question.concept_id).first()

    # Recalculate next recommended concept
    next_activity = AdaptiveEngine.get_next_question(
        db=db,
        student_id=current_user.id,
        course_id=concept.module.course_id if concept and concept.module else None,
        assessment_id=submission.assessment_id
    )
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
        next_recommended_concept=next_rec,
        attempt_number=attempt_num,
        difficulty=question.difficulty
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

# 6. GET /api/student/history (Quiz assessment history)
@router.get("/student/history")
@router.get("/student/assessments")
def get_student_assessment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns student's past quiz attempts. Excludes hidden tests or trainer-only data.
    """
    attempts = db.query(Attempt).filter(
        Attempt.student_id == current_user.id
    ).order_by(Attempt.created_at.desc()).all()

    results = []
    for a in attempts:
        results.append({
            "id": a.id,
            "question_id": a.question_id,
            "question_text": a.question.question_text if a.question else "Question",
            "concept_name": a.question.concept.name if a.question and a.question.concept else "Concept",
            "selected_answer": a.selected_answer,
            "correct_answer": a.question.correct_answer if a.question else "",
            "is_correct": a.is_correct,
            "score": a.score,
            "time_taken": a.time_taken,
            "timestamp": a.created_at.isoformat(),
            "explanation": a.question.explanation if a.question else None
        })
    return {"total": len(results), "attempts": results}

# 7. GET /api/student/coding-history
@router.get("/student/coding-history")
def get_student_coding_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns student's past coding submissions. Never exposes hidden test cases or trainer audit records.
    """
    subs = db.query(CodingSubmission).filter(
        CodingSubmission.student_id == current_user.id
    ).order_by(CodingSubmission.created_at.desc()).all()

    results = []
    for s in subs:
        # Load viva voce questions and answers
        viva_q_list = db.query(ExplanationQuestion).filter(ExplanationQuestion.submission_id == s.id).all()
        viva_details = []
        total_viva_score = 0.0
        for vq in viva_q_list:
            ans = db.query(ExplanationAnswer).filter(ExplanationAnswer.explanation_question_id == vq.id).first()
            if ans:
                total_viva_score += ans.score
                viva_details.append({
                    "question_id": vq.id,
                    "question": vq.question,
                    "student_answer": ans.student_answer,
                    "evaluation": ans.evaluation,
                    "score": ans.score
                })
            else:
                viva_details.append({
                    "question_id": vq.id,
                    "question": vq.question,
                    "student_answer": None,
                    "evaluation": "Awaiting response",
                    "score": 0.0
                })

        avg_viva = round(total_viva_score / len(viva_details), 1) if viva_details and any(v["student_answer"] for v in viva_details) else None

        results.append({
            "id": s.id,
            "problem_id": s.problem_id,
            "problem_title": s.problem.title if s.problem else f"Problem #{s.problem_id}",
            "language": s.language,
            "status": s.status,
            "score": s.score,
            "execution_time": s.execution_time,
            "memory_used": s.memory_used,
            "timestamp": s.created_at.isoformat(),
            "viva_score": avg_viva,
            "viva_details": viva_details
        })

    return {"total": len(results), "submissions": results}

# 8. GET /api/student/analytics
@router.get("/student/analytics")
def get_student_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Structured analytics for charts:
    - Mastery progression over time
    - Performance by difficulty (EASY, MEDIUM, HARD)
    - Attempts and accuracy per concept
    - Actionable recommendations based on weak concepts
    """
    concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()
    masteries = {m.concept_id: m for m in db.query(StudentMastery).filter(StudentMastery.student_id == current_user.id).all()}
    
    total_score = sum(float(m.mastery_score) for m in masteries.values())
    overall_mastery = round(total_score / len(concepts), 1) if concepts else 0.0

    # Progression timeline from MasteryHistory
    history = db.query(MasteryHistory).filter(
        MasteryHistory.student_id == current_user.id
    ).order_by(MasteryHistory.timestamp.asc()).all()

    progression = [
        {
            "timestamp": h.timestamp.isoformat(),
            "mastery": float(h.mastery_score),
            "concept_id": h.concept_id,
            "reason": h.reason
        }
        for h in history
    ]

    # Difficulty breakdown
    attempts = db.query(Attempt).filter(Attempt.student_id == current_user.id).all()
    diff_stats = {
        "EASY": {"total": 0, "correct": 0, "accuracy": 0.0},
        "MEDIUM": {"total": 0, "correct": 0, "accuracy": 0.0},
        "HARD": {"total": 0, "correct": 0, "accuracy": 0.0}
    }

    for a in attempts:
        diff = a.question.difficulty.upper() if a.question and a.question.difficulty else "MEDIUM"
        if diff in diff_stats:
            diff_stats[diff]["total"] += 1
            if a.is_correct:
                diff_stats[diff]["correct"] += 1

    for d in diff_stats.values():
        d["accuracy"] = round((d["correct"] / d["total"] * 100), 1) if d["total"] > 0 else 0.0

    # Attempts per concept
    concept_breakdown = []
    recommendations = []

    for c in concepts:
        m = masteries.get(c.id)
        score = float(m.mastery_score) if m else 0.0
        attempts_c = m.attempts if m else 0
        correct_c = m.correct_attempts if m else 0
        acc = round((correct_c / attempts_c * 100), 1) if attempts_c > 0 else 0.0

        concept_breakdown.append({
            "concept_id": c.id,
            "concept_name": c.name,
            "mastery": score,
            "attempts": attempts_c,
            "correct_attempts": correct_c,
            "accuracy": acc
        })

        if score < 50.0:
            recommendations.append({
                "concept_id": c.id,
                "concept_name": c.name,
                "mastery": score,
                "message": f"You have low mastery in {c.name} ({score}%). Recommended: Practice {max(3, 5 - attempts_c)} targeted questions.",
                "action": f"Practice {c.name}"
            })

    return {
        "overall_mastery": overall_mastery,
        "mastery_progression": progression,
        "difficulty_performance": diff_stats,
        "attempts_per_concept": concept_breakdown,
        "recommendations": recommendations
    }

# 9. GET /api/student/adaptive-score
@router.get("/student/adaptive-score")
def get_student_adaptive_score(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculates personalized adaptive score from actual database data:
    - Overall Adaptive Learning Score (%)
    - Topic-level mastery (e.g. Searching: 85%, Sorting: 62%, Stack: 91%)
    - List of weak concepts (< 50%)
    - List of strong concepts (>= 75%)
    """
    query = db.query(Concept).order_by(Concept.order_index.asc())
    if course_id:
        query = query.join(Concept.module).filter(Concept.module.has(course_id=course_id))
    concepts = query.all()

    masteries = {m.concept_id: m for m in db.query(StudentMastery).filter(StudentMastery.student_id == current_user.id).all()}

    topic_totals: Dict[str, Dict[str, Any]] = {}
    weak_concepts = []
    strong_concepts = []
    concept_details = []

    total_score = 0.0
    for c in concepts:
        m = masteries.get(c.id)
        score = float(m.mastery_score) if m else 0.0
        att = m.attempts if m else 0
        total_score += score

        topic_name = c.module.title if c.module else "General"
        if topic_name not in topic_totals:
            topic_totals[topic_name] = {"total_score": 0.0, "count": 0}
        topic_totals[topic_name]["total_score"] += score
        topic_totals[topic_name]["count"] += 1

        prereq_eval = AdaptiveEngine.evaluate_prerequisites(c, {cid: float(rec.mastery_score) for cid, rec in masteries.items()})
        status = MasteryService.get_concept_status(score, prereq_eval["eligible"], attempts=att)

        if score >= 75.0:
            strong_concepts.append({"id": c.id, "name": c.name, "mastery": score, "mastery_score": score, "topic": topic_name, "topic_name": topic_name})
        elif score < 50.0 and (att > 0 or not prereq_eval["eligible"]):
            weak_concepts.append({"id": c.id, "name": c.name, "mastery": score, "mastery_score": score, "topic": topic_name, "topic_name": topic_name, "reason": "Low mastery or prerequisite lock"})

        concept_details.append({
            "id": c.id,
            "name": c.name,
            "topic": topic_name,
            "mastery": score,
            "status": status,
            "attempts": att
        })

    overall_score = round(total_score / len(concepts), 1) if concepts else 0.0

    topic_mastery_list = [
        {"topic_id": idx, "topic_name": name, "mastery": round(data["total_score"] / data["count"], 1)}
        for idx, (name, data) in enumerate(topic_totals.items(), 1) if data["count"] > 0
    ]
    topic_mastery_dict = {
        name: round(data["total_score"] / data["count"], 1)
        for name, data in topic_totals.items() if data["count"] > 0
    }

    return {
        "student_id": current_user.id,
        "student_name": current_user.name,
        "adaptive_learning_score": overall_score,
        "topic_mastery": topic_mastery_list,
        "topic_mastery_dict": topic_mastery_dict,
        "concept_mastery": concept_details,
        "weak_concepts": weak_concepts,
        "strong_concepts": strong_concepts,
        "total_concepts": len(concepts),
        "mastered_concepts": len(strong_concepts),
        "in_progress_concepts": len([c for c in concept_details if c["status"] in ["DEVELOPING", "LEARNING"]]),
        "weak_concept_count": len(weak_concepts)
    }

# 10. GET /api/student/concept-breakdown
@router.get("/student/concept-breakdown")
def get_concept_breakdown(
    course_id: Optional[int] = None,
    module_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns full syllabus breakdown for Subject -> Topic -> Concept -> Sub-concept.
    Shows status: Not Started, Learning, Weak, Developing, Mastered.
    Clicking a concept reveals explanation, examples, code, current mastery, and past attempts.
    """
    from backend.models.course import Course, Module

    c_query = db.query(Course)
    if course_id:
        c_query = c_query.filter(Course.id == course_id)
    courses = c_query.all()

    masteries = {m.concept_id: m for m in db.query(StudentMastery).filter(StudentMastery.student_id == current_user.id).all()}
    all_mastery_map = {cid: float(rec.mastery_score) for cid, rec in masteries.items()}

    breakdown = []
    for crs in courses:
        modules_data = []
        mod_query = db.query(Module).filter(Module.course_id == crs.id)
        if module_id:
            mod_query = mod_query.filter(Module.id == module_id)
        modules = mod_query.order_by(Module.order_index.asc()).all()

        for mod in modules:
            concepts_data = []
            for c in mod.concepts:
                m = masteries.get(c.id)
                score = float(m.mastery_score) if m else 0.0
                att_count = m.attempts if m else 0
                corr_count = m.correct_attempts if m else 0

                prereq_eval = AdaptiveEngine.evaluate_prerequisites(c, all_mastery_map)
                status = MasteryService.get_concept_status(score, prereq_eval["eligible"], attempts=att_count)

                # Recent attempts on this concept
                past_attempts = db.query(Attempt).join(Question).filter(
                    Attempt.student_id == current_user.id,
                    Question.concept_id == c.id
                ).order_by(Attempt.created_at.desc()).limit(5).all()

                att_history = [
                    {
                        "id": a.id,
                        "question_text": a.question.question_text[:60] if a.question else "",
                        "is_correct": a.is_correct,
                        "time_taken": a.time_taken,
                        "created_at": a.created_at.isoformat()
                    }
                    for a in past_attempts
                ]

                # Questions available for practice
                q_count = db.query(Question).filter(Question.concept_id == c.id).count()

                concepts_data.append({
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "explanation": c.explanation or f"Core algorithmic concept of {c.name}.",
                    "examples": c.examples or [],
                    "code_snippet": c.code_snippet or f"# Implementation pattern for {c.name}",
                    "difficulty": c.difficulty,
                    "difficulty_level": c.difficulty,
                    "order_index": c.order_index,
                    "parent_concept_id": c.parent_concept_id,
                    "mastery_score": score,
                    "current_mastery": score,
                    "status": status,
                    "attempts_count": att_count,
                    "correct_count": corr_count,
                    "accuracy": round((corr_count / att_count * 100), 1) if att_count > 0 else 0.0,
                    "eligible": prereq_eval["eligible"],
                    "blocking_prereqs": prereq_eval["blocking_prereqs"],
                    "available_questions": q_count,
                    "recent_attempts": att_history
                })

            modules_data.append({
                "id": mod.id,
                "title": mod.title,
                "name": mod.title,
                "description": mod.description,
                "order_index": mod.order_index,
                "concepts": concepts_data
            })

        breakdown.append({
            "id": crs.id,
            "title": crs.title,
            "name": crs.title,
            "description": crs.description,
            "topics": modules_data,
            "modules": modules_data
        })

    return {"courses": breakdown}

# ==========================================
# 11. ASSESSMENT ATTEMPTS & TIMELINE (Req 7, 8)
# ==========================================

class AssessmentStartRequest(BaseModel):
    assessment_id: str
    assessment_type: Optional[str] = "ADAPTIVE_QUIZ"
    course_id: Optional[int] = None
    module_id: Optional[int] = None
    concept_id: Optional[int] = None
    resume: Optional[bool] = True

class QuestionNavigateRequest(BaseModel):
    target_question_number: int

class QuestionAnswerRequest(BaseModel):
    question_number: Optional[int] = None
    question_id: Optional[int] = None
    selected_answer: str
    time_taken: Optional[float] = 0.0

def build_assessment_state_dict(attempt: AssessmentAttempt, db: Session) -> Dict[str, Any]:
    qa_list = db.query(QuestionAttempt).filter(
        QuestionAttempt.attempt_id == attempt.id
    ).order_by(QuestionAttempt.question_number.asc()).all()

    q_data = []
    answered_count = 0
    unanswered_count = 0
    changed_count = 0
    visited_count = 0

    for qa in qa_list:
        q = qa.question
        if qa.visited:
            visited_count += 1
        if qa.is_changed:
            changed_count += 1
        if qa.selected_answer and len(qa.selected_answer.strip()) > 0:
            answered_count += 1
        else:
            unanswered_count += 1

        q_data.append({
            "id": qa.id,
            "question_id": qa.question_id,
            "question_number": qa.question_number,
            "question_text": q.question_text if q else "",
            "question_type": q.question_type if q else "MCQ",
            "difficulty": q.difficulty if q else "MEDIUM",
            "concept_id": q.concept_id if q else None,
            "concept_name": q.concept.name if (q and q.concept) else "General",
            "concept_description": q.concept.description if (q and q.concept) else "",
            "topic_name": q.topic.title if (q and q.topic) else "",
            "options": q.options if q else [],
            "code_snippet": q.code_snippet if q else None,
            "selected_answer": qa.selected_answer,
            "previous_answer": qa.previous_answer,
            "answer_status": qa.answer_status,
            "visited": qa.visited,
            "submitted": qa.submitted,
            "is_changed": qa.is_changed,
            "is_correct": qa.is_correct,
            "correct_answer": q.correct_answer if q else None,
            "explanation": q.explanation if q else None,
            "score": qa.score,
            "time_taken": qa.time_taken,
            "timestamp": qa.timestamp.isoformat() if qa.timestamp else None
        })

    curr_idx = attempt.current_question_index or 1
    curr_q = next((q for q in q_data if q["question_number"] == curr_idx), q_data[0] if q_data else None)

    return {
        "attempt_id": attempt.id,
        "assessment_id": attempt.assessment_id,
        "assessment_type": attempt.assessment_type,
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "current_question_index": curr_idx,
        "current_question": curr_q,
        "total_questions": len(q_data),
        "score": attempt.score,
        "questions": q_data,
        "summary": {
            "total": len(q_data),
            "answered": answered_count,
            "unanswered": unanswered_count,
            "changed": changed_count,
            "visited": visited_count
        }
    }

@router.post("/assessments/start")
def start_assessment_attempt(
    req: AssessmentStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Starts or resumes an assessment attempt.
    Preserves existing question navigation state across page refreshes.
    Generates Question #1 adaptively if not already present.
    """
    attempt = None
    if req.resume:
        attempt = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.student_id == current_user.id,
            AssessmentAttempt.assessment_id == req.assessment_id,
            AssessmentAttempt.status == "IN_PROGRESS"
        ).order_by(AssessmentAttempt.started_at.desc()).first()

    if not attempt:
        prev_attempts_count = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.student_id == current_user.id,
            AssessmentAttempt.assessment_id == req.assessment_id
        ).count()

        attempt = AssessmentAttempt(
            student_id=current_user.id,
            assessment_id=req.assessment_id,
            assessment_type=req.assessment_type or "ADAPTIVE_QUIZ",
            attempt_number=prev_attempts_count + 1,
            status="IN_PROGRESS",
            current_question_index=1,
            started_at=datetime.now(timezone.utc)
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # Record ASSESSMENT_START integrity event
        IntegrityService.record_integrity_event(
            db=db,
            student_id=current_user.id,
            event_type="ASSESSMENT_START",
            action="Assessment started",
            details=f"Student started assessment '{req.assessment_id}' (Attempt #{attempt.attempt_number})",
            risk_level="NORMAL",
            source="ADAPTIVE_QUIZ",
            assessment_id=attempt.assessment_id,
            attempt_id=attempt.id
        )

    # Ensure Question #1 exists in question_attempts
    qa1 = db.query(QuestionAttempt).filter(
        QuestionAttempt.attempt_id == attempt.id,
        QuestionAttempt.question_number == 1
    ).first()

    if not qa1:
        q1_data = AdaptiveEngine.get_next_question(
            db=db,
            student_id=current_user.id,
            course_id=req.course_id,
            module_id=req.module_id,
            concept_id=req.concept_id,
            assessment_id=attempt.assessment_id,
            attempt_id=attempt.id
        )
        if q1_data.get("question"):
            q1_obj = q1_data["question"]
            qa1 = QuestionAttempt(
                student_id=current_user.id,
                assessment_id=attempt.assessment_id,
                attempt_id=attempt.id,
                question_id=q1_obj["id"],
                question_number=1,
                visited=True,
                answer_status="UNANSWERED",
                selected_answer=None
            )
            db.add(qa1)
            db.commit()
            db.refresh(qa1)

            # Record QUESTION_OPENED integrity event
            IntegrityService.record_integrity_event(
                db=db,
                student_id=current_user.id,
                event_type="QUESTION_OPENED",
                action="Question opened",
                details="Question #1 opened for first time",
                risk_level="NORMAL",
                source="ADAPTIVE_QUIZ",
                assessment_id=attempt.assessment_id,
                attempt_id=attempt.id,
                question_id=q1_obj["id"],
                question_number=1
            )

    return build_assessment_state_dict(attempt, db)

@router.get("/assessments/{attempt_id}/state")
def get_assessment_state(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Requirement 2: QUESTION STATE MANAGEMENT
    Returns the complete assessment state, all questions, visited/answered status, and active question.
    """
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt.student_id != current_user.id and current_user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")

    return build_assessment_state_dict(attempt, db)

@router.post("/assessments/{attempt_id}/navigate")
def navigate_assessment_question(
    attempt_id: int,
    req: QuestionNavigateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Requirement 1: Revisit any previously viewed question.
    """
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt.student_id != current_user.id and current_user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")

    target_qa = db.query(QuestionAttempt).filter(
        QuestionAttempt.attempt_id == attempt.id,
        QuestionAttempt.question_number == req.target_question_number
    ).first()

    if not target_qa:
        raise HTTPException(status_code=404, detail=f"Question #{req.target_question_number} not found in this attempt")

    ev_type = "QUESTION_REVISITED" if target_qa.visited else "QUESTION_OPENED"
    target_qa.visited = True
    attempt.current_question_index = req.target_question_number
    db.commit()

    IntegrityService.record_integrity_event(
        db=db,
        student_id=current_user.id,
        event_type=ev_type,
        action=f"Question #{req.target_question_number} {'revisited' if ev_type == 'QUESTION_REVISITED' else 'opened'}",
        details=f"Navigated to Question #{req.target_question_number}",
        risk_level="NORMAL",
        source="ADAPTIVE_QUIZ",
        assessment_id=attempt.assessment_id,
        attempt_id=attempt.id,
        question_id=target_qa.question_id,
        question_number=target_qa.question_number
    )

    return build_assessment_state_dict(attempt, db)

@router.post("/assessments/{attempt_id}/save-answer")
def save_assessment_answer(
    attempt_id: int,
    req: QuestionAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Requirement 1 & 2:
    Save or change selected answer for question.
    Preserves answer in DB, marks changed if modified, and updates Bayesian student mastery.
    """
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt.student_id != current_user.id and current_user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")

    qa_q = db.query(QuestionAttempt).filter(QuestionAttempt.attempt_id == attempt.id)
    if req.question_number:
        qa = qa_q.filter(QuestionAttempt.question_number == req.question_number).first()
    elif req.question_id:
        qa = qa_q.filter(QuestionAttempt.question_id == req.question_id).first()
    else:
        qa = qa_q.filter(QuestionAttempt.question_number == (attempt.current_question_index or 1)).first()

    if not qa:
        raise HTTPException(status_code=404, detail="Question not found")

    old_ans = qa.selected_answer
    new_ans = req.selected_answer.strip()

    is_changed = False
    if old_ans and old_ans.strip() != new_ans:
        is_changed = True
        qa.previous_answer = old_ans
        qa.is_changed = True
        qa.answer_status = "CHANGED"
        ev_type = "ANSWER_CHANGED"
        action = "Answer changed"
        details = f"Changed Q#{req.question_number} answer from '{old_ans}' to '{new_ans}'"
    else:
        qa.answer_status = "ANSWERED"
        ev_type = "ANSWER_SELECTED"
        action = "Answer selected"
        details = f"Selected Q#{req.question_number} answer: '{new_ans}'"

    qa.selected_answer = new_ans
    qa.submitted = True
    qa.visited = True
    qa.time_taken = (qa.time_taken or 0.0) + (req.time_taken or 0.0)

    # Evaluate answer correctness
    question = qa.question
    is_correct = False
    if question:
        c_ans = question.correct_answer.strip().lower()
        s_ans = new_ans.lower()
        is_correct = (s_ans == c_ans)
        if not is_correct and question.options:
            opts = [o.strip().lower() for o in question.options]
            if s_ans in opts and s_ans == c_ans:
                is_correct = True

    qa.is_correct = is_correct
    qa.score = 1.0 if is_correct else 0.0

    # Update AssessmentAttempt metrics
    all_qa = db.query(QuestionAttempt).filter(QuestionAttempt.attempt_id == attempt.id).all()
    attempt.questions_attempted = sum(1 for q in all_qa if q.selected_answer)
    attempt.questions_correct = sum(1 for q in all_qa if q.is_correct is True)
    attempt.score = round((attempt.questions_correct / max(1, attempt.questions_attempted) * 100), 1)

    # Update academic StudentMastery using Bayesian logic
    if question:
        MasteryService.update_mastery(
            db=db,
            student_id=current_user.id,
            concept_id=question.concept_id,
            is_correct=is_correct,
            difficulty=question.difficulty,
            reason_detail=f"Assessment Q#{qa.question_number} answer",
            time_taken=req.time_taken
        )

    # Record IntegrityEvent
    IntegrityService.record_integrity_event(
        db=db,
        student_id=current_user.id,
        event_type=ev_type,
        action=action,
        details=details,
        risk_level="NORMAL",
        source="ADAPTIVE_QUIZ",
        assessment_id=attempt.assessment_id,
        attempt_id=attempt.id,
        question_id=qa.question_id,
        question_number=qa.question_number
    )

    db.commit()
    return build_assessment_state_dict(attempt, db)

@router.post("/assessments/{attempt_id}/next-question")
def next_assessment_question(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Requirement 1 & 3:
    Move to the next question.
    If next question already exists in this attempt, restores it.
    If at the latest question, adaptively generates the next question using previous question performance.
    """
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt.student_id != current_user.id and current_user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")

    curr_idx = attempt.current_question_index or 1
    total_existing = db.query(QuestionAttempt).filter(QuestionAttempt.attempt_id == attempt.id).count()

    if curr_idx < total_existing:
        # Move forward to next already-generated question
        attempt.current_question_index = curr_idx + 1
        next_qa = db.query(QuestionAttempt).filter(
            QuestionAttempt.attempt_id == attempt.id,
            QuestionAttempt.question_number == attempt.current_question_index
        ).first()
        if next_qa:
            next_qa.visited = True
        db.commit()

        IntegrityService.record_integrity_event(
            db=db,
            student_id=current_user.id,
            event_type="QUESTION_REVISITED",
            action=f"Next Question Q#{attempt.current_question_index}",
            details=f"Moved to already generated question #{attempt.current_question_index}",
            risk_level="NORMAL",
            source="ADAPTIVE_QUIZ",
            assessment_id=attempt.assessment_id,
            attempt_id=attempt.id,
            question_id=next_qa.question_id if next_qa else None,
            question_number=attempt.current_question_index
        )
    else:
        # Generate next question adaptively!
        next_q_data = AdaptiveEngine.get_next_question(
            db=db,
            student_id=current_user.id,
            assessment_id=attempt.assessment_id,
            attempt_id=attempt.id
        )

        if not next_q_data.get("question"):
            # All available questions completed
            return {
                **build_assessment_state_dict(attempt, db),
                "all_completed": True,
                "message": "All eligible adaptive questions completed for this assessment."
            }

        new_q_obj = next_q_data["question"]
        new_q_num = total_existing + 1

        new_qa = QuestionAttempt(
            student_id=current_user.id,
            assessment_id=attempt.assessment_id,
            attempt_id=attempt.id,
            question_id=new_q_obj["id"],
            question_number=new_q_num,
            visited=True,
            answer_status="UNANSWERED",
            selected_answer=None
        )
        db.add(new_qa)
        attempt.current_question_index = new_q_num
        db.commit()
        db.refresh(new_qa)

        IntegrityService.record_integrity_event(
            db=db,
            student_id=current_user.id,
            event_type="QUESTION_OPENED",
            action=f"Next Question Q#{new_q_num}",
            details=f"Opened adaptive question #{new_q_num} ({new_q_obj.get('difficulty', 'MEDIUM')})",
            risk_level="NORMAL",
            source="ADAPTIVE_QUIZ",
            assessment_id=attempt.assessment_id,
            attempt_id=attempt.id,
            question_id=new_q_obj["id"],
            question_number=new_q_num
        )

    return build_assessment_state_dict(attempt, db)

@router.post("/assessments/{attempt_id}/previous-question")
def previous_assessment_question(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Requirement 1:
    Move back to the previous question.
    Restores Question state and previous selected answer.
    """
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt.student_id != current_user.id and current_user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")

    curr_idx = attempt.current_question_index or 1
    if curr_idx > 1:
        attempt.current_question_index = curr_idx - 1
        prev_qa = db.query(QuestionAttempt).filter(
            QuestionAttempt.attempt_id == attempt.id,
            QuestionAttempt.question_number == attempt.current_question_index
        ).first()
        if prev_qa:
            prev_qa.visited = True
        db.commit()

        IntegrityService.record_integrity_event(
            db=db,
            student_id=current_user.id,
            event_type="QUESTION_REVISITED",
            action=f"Previous Question Q#{attempt.current_question_index}",
            details=f"Returned to Question #{attempt.current_question_index} (Answer preserved: {prev_qa.selected_answer if prev_qa else 'None'})",
            risk_level="NORMAL",
            source="ADAPTIVE_QUIZ",
            assessment_id=attempt.assessment_id,
            attempt_id=attempt.id,
            question_id=prev_qa.question_id if prev_qa else None,
            question_number=attempt.current_question_index
        )

    return build_assessment_state_dict(attempt, db)

@router.post("/assessments/{attempt_id}/finish")
def finish_assessment_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt.student_id != current_user.id and current_user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")

    # Compute final score
    all_qa = db.query(QuestionAttempt).filter(QuestionAttempt.attempt_id == attempt.id).all()
    answered_qa = [q for q in all_qa if q.selected_answer]
    attempt.questions_attempted = len(answered_qa)
    attempt.questions_correct = sum(1 for q in answered_qa if q.is_correct is True)
    if attempt.questions_attempted > 0:
        attempt.score = round((attempt.questions_correct / attempt.questions_attempted * 100), 1)

    attempt.status = "COMPLETED"
    attempt.ended_at = datetime.now(timezone.utc)

    if attempt.risk_score >= 70.0 or attempt.warnings_count >= 3:
        attempt.risk_level = "HIGH_RISK"
    elif attempt.risk_score >= 40.0 or attempt.warnings_count >= 2:
        attempt.risk_level = "MEDIUM_RISK"
    elif attempt.warnings_count == 1:
        attempt.risk_level = "LOW_RISK"
    else:
        attempt.risk_level = "NORMAL"

    # Record ASSESSMENT_COMPLETED integrity event
    IntegrityService.record_integrity_event(
        db=db,
        student_id=current_user.id,
        event_type="ASSESSMENT_COMPLETED",
        action="Assessment completed",
        details=f"Final score: {attempt.score}% ({attempt.questions_correct}/{attempt.questions_attempted} correct)",
        risk_level=attempt.risk_level.replace("_RISK", ""),
        source="ADAPTIVE_QUIZ",
        assessment_id=attempt.assessment_id,
        attempt_id=attempt.id
    )

    db.commit()
    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "score": attempt.score,
        "questions_attempted": attempt.questions_attempted,
        "questions_correct": attempt.questions_correct,
        "warnings_count": attempt.warnings_count,
        "risk_level": attempt.risk_level,
        "ended_at": attempt.ended_at.isoformat()
    }

@router.get("/student/attempts/{attempt_id}/analysis")
def get_attempt_analysis(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Requirement 11: PREVIOUS ATTEMPT -> ADAPTIVE LEARNING
    Analyzes student's previous attempts while keeping Academic and Integrity separate.
    """
    return AdaptiveEngine.analyze_previous_attempts(db, current_user.id)


@router.get("/student/attempts")
def get_student_attempts(
    assessment_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AssessmentAttempt).filter(AssessmentAttempt.student_id == current_user.id)
    if assessment_id:
        query = query.filter(AssessmentAttempt.assessment_id == assessment_id)
    attempts = query.order_by(AssessmentAttempt.started_at.desc()).all()

    results = []
    for a in attempts:
        results.append({
            "id": a.id,
            "assessment_id": a.assessment_id,
            "assessment_type": a.assessment_type,
            "attempt_number": a.attempt_number,
            "status": a.status,
            "score": a.score,
            "questions_attempted": a.questions_attempted,
            "questions_correct": a.questions_correct,
            "coding_submissions_count": a.coding_submissions_count,
            "warnings_count": a.warnings_count,
            "integrity_events_count": a.integrity_events_count,
            "risk_score": a.risk_score,
            "risk_level": a.risk_level,
            "started_at": a.started_at.isoformat() if a.started_at else None,
            "ended_at": a.ended_at.isoformat() if a.ended_at else None
        })
    return {"total": len(results), "attempts": results}

@router.get("/trainer/attempts")
def get_trainer_attempts(
    student_id: Optional[int] = None,
    assessment_id: Optional[str] = None,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    query = db.query(AssessmentAttempt)
    if student_id:
        query = query.filter(AssessmentAttempt.student_id == student_id)
    if assessment_id:
        query = query.filter(AssessmentAttempt.assessment_id == assessment_id)
    attempts = query.order_by(AssessmentAttempt.started_at.desc()).all()

    results = []
    for a in attempts:
        results.append({
            "id": a.id,
            "student_id": a.student_id,
            "student_name": a.student.name if a.student else "Student",
            "student_email": a.student.email if a.student else "",
            "assessment_id": a.assessment_id,
            "assessment_type": a.assessment_type,
            "attempt_number": a.attempt_number,
            "status": a.status,
            "score": a.score,
            "questions_attempted": a.questions_attempted,
            "questions_correct": a.questions_correct,
            "warnings_count": a.warnings_count,
            "risk_score": a.risk_score,
            "risk_level": a.risk_level,
            "started_at": a.started_at.isoformat() if a.started_at else None,
            "ended_at": a.ended_at.isoformat() if a.ended_at else None
        })
    return {"total": len(results), "attempts": results}

@router.get("/trainer/attempts/{attempt_id}/timeline")
def get_attempt_timeline(
    attempt_id: int,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    events_timeline = []

    # 1. Assessment Warnings
    warnings = db.query(AssessmentWarning).filter(AssessmentWarning.attempt_id == attempt_id).all()
    for w in warnings:
        events_timeline.append({
            "timestamp": w.timestamp.isoformat(),
            "time_display": w.timestamp.strftime("%H:%M:%S"),
            "event_type": "WARNING",
            "label": f"Warning displayed ({w.warning_type})",
            "category": "INTEGRITY_WARNING",
            "risk_level": w.severity,
            "details": w.message
        })

    # 2. Question Attempts
    q_attempts = db.query(Attempt).filter(
        Attempt.student_id == attempt.student_id,
        Attempt.assessment_id == attempt.id
    ).all()
    for qa in q_attempts:
        events_timeline.append({
            "timestamp": qa.created_at.isoformat(),
            "time_display": qa.created_at.strftime("%H:%M:%S"),
            "event_type": "QUESTION_ATTEMPT",
            "label": f"Question #{qa.question_id} {'Correct' if qa.is_correct else 'Incorrect'}",
            "category": "QUIZ",
            "risk_level": "NORMAL",
            "details": f"Answer: {qa.selected_answer} ({qa.time_taken:.1f}s)"
        })

    events_timeline.sort(key=lambda x: x["timestamp"])

    return {
        "attempt_id": attempt.id,
        "student_name": attempt.student.name if attempt.student else "Student",
        "score": attempt.score,
        "warnings_count": attempt.warnings_count,
        "risk_level": attempt.risk_level,
        "timeline": events_timeline
    }


