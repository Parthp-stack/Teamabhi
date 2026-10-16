from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.models.user import User
from backend.models.question import Question, Attempt
from backend.models.concept import Concept
from backend.models.coding import CodingSubmission, CodingProblem
from backend.models.explanation import ExplanationQuestion, ExplanationAnswer
from backend.models.mastery import StudentMastery, MasteryHistory
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
    module_id: Optional[int] = None,
    concept_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Selects the next question based on the student's weakest eligible prerequisite,
    or targeted topic/concept if specified.
    """
    res = AdaptiveEngine.get_next_question(
        db=db,
        student_id=current_user.id,
        course_id=course_id,
        module_id=module_id,
        concept_id=concept_id
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
    Evaluates student answer, creates an Attempt record with time_taken, updates StudentMastery
    with time-calibrated Bayesian logic, and returns immediate feedback with next recommendations.
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

    # Record Attempt with time taken
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
        course_id=concept.module.course_id if concept and concept.module else None
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
            strong_concepts.append({"id": c.id, "name": c.name, "mastery": score, "topic": topic_name})
        elif score < 50.0 and (att > 0 or not prereq_eval["eligible"]):
            weak_concepts.append({"id": c.id, "name": c.name, "mastery": score, "topic": topic_name, "reason": "Low mastery or prerequisite lock"})

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

