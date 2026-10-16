from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.models.course import Course, Module
from backend.models.concept import Concept, ConceptPrerequisite
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.question import Question, Attempt
from backend.models.coding import CodingProblem, CodingSubmission
from backend.models.session import Session as AssessmentSession
from backend.models.explanation import ExplanationAnswer, ExplanationQuestion
from backend.utils.security import require_trainer, get_current_user
from backend.services.adaptive_engine import AdaptiveEngine
from backend.services.curriculum_service import CurriculumService
from backend.services.ai_service import AIService
from backend.services.mcq_validation_service import MCQValidationService
from backend.services.github_service import GitHubEvaluationService
from backend.schemas.curriculum import (
    CourseCreateRequest, CourseUpdateRequest,
    ModuleCreateRequest, ModuleUpdateRequest,
    ConceptCreateRequest, ConceptUpdateRequest,
    PrerequisiteAddRequest,
    QuestionCreateRequest, QuestionUpdateRequest,
    AIQuestionPreviewRequest
)

router = APIRouter(prefix="/trainer", tags=["Trainer Management & Curriculum"])

# ==========================================
# 1. TRAINER DASHBOARD & COHORT OVERVIEW
# ==========================================
@router.get("/overview")
@router.get("/dashboard")
def get_trainer_overview(
    search: Optional[str] = Query(None, description="Search student by name or email"),
    min_mastery: Optional[float] = Query(None, ge=0.0, le=100.0),
    max_mastery: Optional[float] = Query(None, ge=0.0, le=100.0),
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    course = db.query(Course).first()
    students_query = db.query(User).filter(User.role == UserRole.STUDENT.value)
    
    if search:
        search_fmt = f"%{search.strip()}%"
        students_query = students_query.filter(
            (User.name.ilike(search_fmt)) | (User.email.ilike(search_fmt))
        )
    
    students = students_query.all()
    total_students = len(students)

    concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()
    concept_stats = []
    total_system_mastery = 0.0
    mastery_count = 0

    for c in concepts:
        masteries = db.query(StudentMastery.mastery_score).filter(StudentMastery.concept_id == c.id).all()
        scores = [float(m[0]) for m in masteries]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        weak_count = sum(1 for s in scores if s < 50.0)
        weak_pct = round((weak_count / len(scores) * 100), 1) if scores else 0.0

        concept_stats.append({
            "id": c.id,
            "name": c.name,
            "difficulty": c.difficulty,
            "average_mastery": avg_score,
            "student_count": len(scores),
            "weak_student_count": weak_count,
            "weak_student_percent": weak_pct,
            "prerequisites": [p.name for p in c.prerequisites]
        })
        if scores:
            total_system_mastery += sum(scores)
            mastery_count += len(scores)

    cohort_average = round(total_system_mastery / mastery_count, 1) if mastery_count > 0 else 0.0

    # Average Quiz Attempt Score across cohort
    attempts = db.query(Attempt.is_correct).all()
    avg_quiz_score = round(
        (sum(1 for a in attempts if a[0]) / len(attempts) * 100), 1
    ) if attempts else 0.0

    # Average Coding Performance
    coding_subs = db.query(CodingSubmission.score).all()
    avg_coding_score = round(
        sum(float(cs[0]) for cs in coding_subs) / len(coding_subs), 1
    ) if coding_subs else 0.0

    # Sort for weakest concepts
    sorted_by_weakest = sorted(concept_stats, key=lambda x: x["average_mastery"])
    weakest_concepts = sorted_by_weakest[:3]

    # Generate actionable cohort recommendations based on actual data
    recommendations = []
    for wc in weakest_concepts:
        if wc["average_mastery"] < 50.0 or wc["weak_student_percent"] >= 30.0:
            recommendations.append({
                "concept_id": wc["id"],
                "concept_name": wc["name"],
                "severity": "HIGH" if wc["average_mastery"] < 40.0 else "MEDIUM",
                "message": f"{wc['weak_student_percent']}% of students have low mastery in '{wc['name']}' (Avg: {wc['average_mastery']}%). Consider assigning additional practice questions.",
                "action": f"Assign reinforcement quiz on {wc['name']}"
            })

    # Student summaries with filtering
    student_summaries = []
    for s in students:
        s_masteries = db.query(StudentMastery).filter(StudentMastery.student_id == s.id).all()
        s_scores = [float(m.mastery_score) for m in s_masteries]
        s_avg = round(sum(s_scores) / len(s_scores), 1) if s_scores else 0.0

        if min_mastery is not None and s_avg < min_mastery:
            continue
        if max_mastery is not None and s_avg > max_mastery:
            continue

        # Find weakest concept for this student
        weakest_concept_name = "None"
        if s_masteries:
            lowest_rec = min(s_masteries, key=lambda m: float(m.mastery_score))
            c_obj = db.query(Concept).filter(Concept.id == lowest_rec.concept_id).first()
            if c_obj:
                weakest_concept_name = c_obj.name

        # Student's quiz attempt average
        s_attempts = db.query(Attempt.is_correct).filter(Attempt.student_id == s.id).all()
        s_quiz_avg = round((sum(1 for a in s_attempts if a[0]) / len(s_attempts) * 100), 1) if s_attempts else 0.0

        # Student's coding score average
        s_codings = db.query(CodingSubmission.score).filter(CodingSubmission.student_id == s.id).all()
        s_coding_avg = round(sum(float(c[0]) for c in s_codings) / len(s_codings), 1) if s_codings else 0.0

        # Last activity
        last_attempt = db.query(Attempt.created_at).filter(Attempt.student_id == s.id).order_by(Attempt.created_at.desc()).first()
        last_sub = db.query(CodingSubmission.created_at).filter(CodingSubmission.student_id == s.id).order_by(CodingSubmission.created_at.desc()).first()
        
        last_times = []
        if last_attempt and last_attempt[0]:
            last_times.append(last_attempt[0])
        if last_sub and last_sub[0]:
            last_times.append(last_sub[0])
        last_act = max(last_times).isoformat() if last_times else s.created_at.isoformat()

        student_summaries.append({
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "average_mastery": s_avg,
            "weakest_concept": weakest_concept_name,
            "assessment_score": s_quiz_avg,
            "coding_score": s_coding_avg,
            "last_activity": last_act
        })

    return {
        "course": {
            "id": course.id if course else 1,
            "title": course.title if course else "Object Oriented Programming",
            "description": course.description if course else "OOP Curriculum with Bayesian Knowledge Tracing"
        },
        "total_students": total_students,
        "cohort_average_mastery": cohort_average,
        "cohort_average_assessment_score": avg_quiz_score,
        "cohort_average_coding_score": avg_coding_score,
        "concepts": concept_stats,
        "weakest_concepts": weakest_concepts,
        "recommendations": recommendations,
        "students": student_summaries
    }

# ==========================================
# 2. STUDENT DETAIL / DEEP DIVE
# ==========================================
@router.get("/student/{student_id}")
def get_student_deep_dive(
    student_id: int,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()
    masteries = {
        m.concept_id: m for m in db.query(StudentMastery).filter(
            StudentMastery.student_id == student_id
        ).all()
    }
    mastery_map = {cid: float(rec.mastery_score) for cid, rec in masteries.items()}

    concept_list = []
    total_mastery = 0.0
    for c in concepts:
        m = masteries.get(c.id)
        score = float(m.mastery_score) if m else 0.0
        total_mastery += score
        attempts_count = m.attempts if m else 0
        correct_count = m.correct_attempts if m else 0
        prereq_eval = AdaptiveEngine.evaluate_prerequisites(c, mastery_map)

        concept_list.append({
            "concept_id": c.id,
            "name": c.name,
            "description": c.description,
            "difficulty": c.difficulty,
            "mastery": score,
            "attempts": attempts_count,
            "correct_attempts": correct_count,
            "accuracy": round((correct_count / attempts_count * 100), 1) if attempts_count > 0 else 0.0,
            "eligible": prereq_eval["eligible"],
            "prerequisites": [p.name for p in c.prerequisites]
        })

    overall_avg = round(total_mastery / len(concepts), 1) if concepts else 0.0

    # Dynamic learning path from Adaptive Engine
    learning_path = AdaptiveEngine.get_learning_path(db, student_id)

    # Mastery history progression
    history_records = db.query(MasteryHistory).filter(
        MasteryHistory.student_id == student_id
    ).order_by(MasteryHistory.timestamp.asc()).all()

    history = [
        {
            "id": h.id,
            "concept_id": h.concept_id,
            "mastery": float(h.mastery_score),
            "change": float(h.change_amount),
            "reason": h.reason,
            "timestamp": h.timestamp.isoformat()
        }
        for h in history_records
    ]

    # Quiz Attempts
    quiz_attempts = db.query(Attempt).filter(
        Attempt.student_id == student_id
    ).order_by(Attempt.created_at.desc()).limit(20).all()

    attempts_data = [
        {
            "id": a.id,
            "question_id": a.question_id,
            "question_text": a.question.question_text[:80] + "..." if a.question else "Question",
            "concept_name": a.question.concept.name if a.question and a.question.concept else "Concept",
            "selected_answer": a.selected_answer,
            "is_correct": a.is_correct,
            "score": a.score,
            "time_taken": a.time_taken,
            "timestamp": a.created_at.isoformat()
        }
        for a in quiz_attempts
    ]

    # Coding Submissions with Viva Voce scores
    coding_subs = db.query(CodingSubmission).filter(
        CodingSubmission.student_id == student_id
    ).order_by(CodingSubmission.created_at.desc()).all()

    submissions_data = []
    for cs in coding_subs:
        # Calculate viva comprehension score if questions exist
        viva_answers = db.query(ExplanationAnswer).join(ExplanationQuestion).filter(
            ExplanationQuestion.submission_id == cs.id
        ).all()
        viva_score = None
        if viva_answers:
            viva_score = round(sum(ans.score for ans in viva_answers) / len(viva_answers), 1)

        submissions_data.append({
            "id": cs.id,
            "problem_id": cs.problem_id,
            "problem_title": cs.problem.title if cs.problem else f"Problem #{cs.problem_id}",
            "language": cs.language,
            "status": cs.status,
            "score": cs.score,
            "execution_time": cs.execution_time,
            "memory_used": cs.memory_used,
            "viva_score": viva_score,
            "created_at": cs.created_at.isoformat()
        })

    # Recorded assessment sessions with link to Phase 3 integrity
    sessions = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student_id
    ).order_by(AssessmentSession.started_at.desc()).all()

    sessions_data = [
        {
            "id": s.id,
            "assessment_id": s.assessment_id,
            "problem_title": s.problem.title if s.problem else f"Assessment #{s.assessment_id}",
            "total_events": len(s.events) if s.events else 0,
            "signals_count": len(s.integrity_signals) if s.integrity_signals else 0,
            "overall_review_status": s.overall_review_status or "UNREVIEWED",
            "is_reviewed": s.is_reviewed or False,
            "review_notes": s.review_notes,
            "created_at": s.started_at.isoformat() if s.started_at else None
        }
        for s in sessions
    ]

    # AI Evaluations
    from backend.models.ai_evaluation import AIEvaluation
    ai_evals = db.query(AIEvaluation).filter(
        AIEvaluation.student_id == student_id
    ).order_by(AIEvaluation.timestamp.desc()).all()

    ai_eval_data = [
        {
            "id": ae.id,
            "submission_id": ae.submission_id,
            "score": ae.score,
            "understanding_verdict": ae.understanding_verdict,
            "feedback": ae.feedback,
            "detected_strengths": ae.detected_strengths or [],
            "detected_weaknesses": ae.detected_weaknesses or [],
            "difficulty_recommendation": ae.difficulty_recommendation,
            "next_question_recommendation": ae.next_question_recommendation,
            "timestamp": ae.timestamp.isoformat() if ae.timestamp else None
        }
        for ae in ai_evals
    ]

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "role": student.role,
            "created_at": student.created_at.isoformat()
        },
        "overall_mastery": overall_avg,
        "concepts": concept_list,
        "learning_path": learning_path,
        "history": history,
        "quiz_attempts": attempts_data,
        "submissions": submissions_data,
        "sessions": sessions_data,
        "ai_evaluations": ai_eval_data
    }

# ==========================================
# 3. CURRICULUM MANAGEMENT (COURSES, MODULES, CONCEPTS)
# ==========================================
@router.get("/curriculum")
def get_curriculum_management(
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    courses = db.query(Course).all()
    modules = db.query(Module).order_by(Module.order_index.asc()).all()
    concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()

    concept_list = []
    for c in concepts:
        q_count = db.query(Question).filter(Question.concept_id == c.id).count()
        concept_list.append({
            "id": c.id,
            "module_id": c.module_id,
            "name": c.name,
            "description": c.description,
            "difficulty": c.difficulty,
            "order_index": c.order_index,
            "question_count": q_count,
            "prerequisites": [{"id": p.id, "name": p.name} for p in c.prerequisites],
            "dependents": [{"id": d.id, "name": d.name} for d in c.dependents]
        })

    return {
        "courses": [
            {
                "id": crs.id,
                "title": crs.title,
                "description": crs.description,
                "modules": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "description": m.description,
                        "order_index": m.order_index
                    } for m in crs.modules
                ]
            } for crs in courses
        ],
        "modules": [
            {
                "id": m.id,
                "course_id": m.course_id,
                "title": m.title,
                "description": m.description,
                "order_index": m.order_index
            } for m in modules
        ],
        "concepts": concept_list
    }

@router.post("/courses")
def create_course(
    req: CourseCreateRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    course = Course(title=req.title, description=req.description, created_by=trainer.id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"message": "Course created", "course_id": course.id, "title": course.title}

@router.put("/courses/{course_id}")
def update_course(
    course_id: int,
    req: CourseUpdateRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if req.title is not None:
        course.title = req.title
    if req.description is not None:
        course.description = req.description
    db.commit()
    return {"message": "Course updated", "course_id": course.id, "title": course.title}

@router.post("/modules")
def create_module(
    req: ModuleCreateRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    module = Module(
        course_id=req.course_id,
        title=req.title,
        description=req.description,
        order_index=req.order_index or 0
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return {"message": "Module created", "module_id": module.id, "title": module.title}

@router.post("/concepts")
def create_concept(
    req: ConceptCreateRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    concept = CurriculumService.create_concept(db, req)
    return {
        "message": "Concept created",
        "concept_id": concept.id,
        "name": concept.name,
        "difficulty": concept.difficulty
    }

@router.put("/concepts/{concept_id}")
def update_concept(
    concept_id: int,
    req: ConceptUpdateRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    concept = CurriculumService.update_concept(db, concept_id, req)
    return {
        "message": "Concept updated",
        "concept_id": concept.id,
        "name": concept.name
    }

@router.delete("/concepts/{concept_id}")
def delete_concept(
    concept_id: int,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    return CurriculumService.delete_concept(db, concept_id)

@router.post("/concepts/{concept_id}/prerequisites")
def add_prerequisite(
    concept_id: int,
    req: PrerequisiteAddRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    """
    Adds a prerequisite edge: prerequisite_id -> concept_id.
    Includes CYCLE DETECTION VALIDATION to prevent invalid circular dependency graphs!
    """
    return CurriculumService.add_prerequisite(db, concept_id, req.prerequisite_id)

@router.delete("/concepts/{concept_id}/prerequisites/{prerequisite_id}")
def remove_prerequisite(
    concept_id: int,
    prerequisite_id: int,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    return CurriculumService.remove_prerequisite(db, concept_id, prerequisite_id)

# ==========================================
# 4. QUESTION BANK MANAGEMENT
# ==========================================
@router.get("/questions")
def get_question_bank(
    concept_id: Optional[int] = Query(None),
    difficulty: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    query = db.query(Question)
    if concept_id:
        query = query.filter(Question.concept_id == concept_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty.upper())
    if question_type:
        query = query.filter(Question.question_type == question_type.upper())
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(Question.question_text.ilike(search_fmt))

    questions = query.order_by(Question.created_at.desc()).all()
    results = []
    for q in questions:
        results.append({
            "id": q.id,
            "concept_id": q.concept_id,
            "concept_name": q.concept.name if q.concept else "Concept",
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "created_at": q.created_at.isoformat() if q.created_at else None
        })
    return {"total": len(results), "questions": results}

@router.post("/questions/validate")
async def validate_trainer_question(
    payload: Dict[str, Any],
    trainer: User = Depends(require_trainer)
):
    """
    Validates MCQ before adding or modifying in question bank.
    Returns structured validation feedback.
    """
    return await MCQValidationService.validate_mcq_with_ai(payload)

@router.post("/questions")
def create_question(
    req: QuestionCreateRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    concept = db.query(Concept).filter(Concept.id == req.concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # REQUIREMENT 1: Validate MCQ before allowing it into the question bank
    if (req.question_type or "").upper() == "MCQ":
        mcq_payload = {
            "question_text": req.question_text,
            "options": req.options,
            "correct_answer": req.correct_answer,
            "explanation": req.explanation,
            "difficulty": req.difficulty,
            "concept": concept.name
        }
        val_res = MCQValidationService.validate_mcq_deterministic(mcq_payload)
        if not val_res["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"MCQ Validation Error: {val_res['reason']}"
            )

    question = Question(
        concept_id=req.concept_id,
        question_text=req.question_text,
        question_type=req.question_type,
        difficulty=req.difficulty,
        options=req.options,
        correct_answer=req.correct_answer,
        explanation=req.explanation
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    return {
        "message": "Question created in question bank",
        "question_id": question.id,
        "concept_name": concept.name
    }

@router.put("/questions/{question_id}")
def update_question(
    question_id: int,
    req: QuestionUpdateRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    q_type = req.question_type if req.question_type is not None else question.question_type
    if (q_type or "").upper() == "MCQ":
        mcq_payload = {
            "question_text": req.question_text if req.question_text is not None else question.question_text,
            "options": req.options if req.options is not None else question.options,
            "correct_answer": req.correct_answer if req.correct_answer is not None else question.correct_answer,
            "explanation": req.explanation if req.explanation is not None else question.explanation,
            "difficulty": req.difficulty if req.difficulty is not None else question.difficulty,
            "concept": question.concept.name if question.concept else "General"
        }
        val_res = MCQValidationService.validate_mcq_deterministic(mcq_payload)
        if not val_res["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"MCQ Validation Error: {val_res['reason']}"
            )

    if req.question_text is not None:
        question.question_text = req.question_text
    if req.question_type is not None:
        question.question_type = req.question_type
    if req.difficulty is not None:
        question.difficulty = req.difficulty
    if req.options is not None:
        question.options = req.options
    if req.correct_answer is not None:
        question.correct_answer = req.correct_answer
    if req.explanation is not None:
        question.explanation = req.explanation

    db.commit()
    return {"message": "Question updated", "question_id": question.id}

@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}

@router.post("/questions/ai-preview")
async def preview_ai_question(
    req: AIQuestionPreviewRequest,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    """
    Generates a draft question using OpenRouter AI.
    The trainer can review and preview it before saving to the question bank.
    """
    draft = await AIService.generate_assessment_question(
        concept_name=req.concept_name,
        difficulty=req.difficulty,
        question_type=req.question_type
    )
    return {
        "concept_name": req.concept_name,
        "difficulty": req.difficulty,
        "question_type": req.question_type,
        "draft_question": draft
    }

# ==========================================
# 5. OPTIONAL FEATURE: GITHUB REPO EVALUATION & VIVA
# ==========================================
@router.post("/repo-evaluation/analyze")
async def analyze_github_repository(
    repo_url: str = Query(..., description="Public GitHub repo URL e.g. https://github.com/owner/repo"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Safely inspects a GitHub repository structure, identifies concepts,
    flags potential issues with line references, and prepares viva voce questions.
    """
    try:
        result = await GitHubEvaluationService.evaluate_repository(repo_url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze repository: {str(e)}")

@router.post("/repo-evaluation/viva")
async def evaluate_repo_viva(
    answers_payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates student's answers to the repository viva questions.
    """
    repo_context = answers_payload.get("repo_context", "General Repository Architecture")
    answers = answers_payload.get("answers", [])
    if not answers:
        raise HTTPException(status_code=400, detail="No answers provided")

    result = await GitHubEvaluationService.evaluate_viva_answers(repo_context, answers)
    return result
