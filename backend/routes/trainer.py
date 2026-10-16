from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.models.concept import Concept
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.coding import CodingSubmission, CodingProblem
from backend.models.session import Session as CodingSession, SessionEvent
from backend.models.integrity import IntegritySignal
from backend.models.explanation import ExplanationQuestion, ExplanationAnswer
from backend.utils.security import require_trainer

router = APIRouter(prefix="/trainer", tags=["Trainer Management"])

@router.get("/dashboard")
def get_trainer_dashboard_overview(
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    # Total students
    students = db.query(User).filter(User.role == UserRole.STUDENT.value).all()
    total_students = len(students)

    # Concept masteries
    concepts = db.query(Concept).all()
    concept_stats = []
    total_system_mastery = 0.0
    mastery_count = 0

    for c in concepts:
        masteries = db.query(StudentMastery.mastery).filter(StudentMastery.concept_id == c.id).all()
        scores = [m[0] for m in masteries]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        concept_stats.append({
            "id": c.id,
            "name": c.name,
            "average_mastery": avg_score,
            "total_students": len(scores)
        })
        total_system_mastery += sum(scores)
        mastery_count += len(scores)

    overall_avg = round(total_system_mastery / mastery_count, 1) if mastery_count > 0 else 0.0
    concept_stats.sort(key=lambda x: x["average_mastery"])
    weakest_concepts = concept_stats[:3]

    # Integrity review sessions
    recent_signals = db.query(IntegritySignal).order_by(IntegritySignal.timestamp.desc()).limit(15).all()
    flagged_sessions_map: Dict[int, Any] = {}
    for sig in recent_signals:
        if sig.session_id not in flagged_sessions_map:
            sess = db.query(CodingSession).filter(CodingSession.id == sig.session_id).first()
            student_name = sess.student.name if sess and sess.student else "Student"
            prob_title = sess.problem.title if sess and sess.problem else "Coding Assessment"
            flagged_sessions_map[sig.session_id] = {
                "session_id": sig.session_id,
                "student_id": sess.student_id if sess else 0,
                "student_name": student_name,
                "problem_title": prob_title,
                "signal_type": sig.signal_type,
                "severity": sig.severity,
                "description": sig.description,
                "timestamp": sig.timestamp.isoformat()
            }

    # Student summary list
    student_list = []
    for s in students:
        s_masteries = db.query(StudentMastery.mastery).filter(StudentMastery.student_id == s.id).all()
        s_scores = [m[0] for m in s_masteries]
        s_avg = round(sum(s_scores) / len(s_scores), 1) if s_scores else 0.0

        # Submissions count
        subs_count = db.query(CodingSubmission).filter(CodingSubmission.student_id == s.id).count()

        # Flagged signals count
        signals_count = db.query(IntegritySignal).join(CodingSession).filter(CodingSession.student_id == s.id).count()

        student_list.append({
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "average_mastery": s_avg,
            "submissions_count": subs_count,
            "signals_count": signals_count,
            "needs_intervention": s_avg < 60.0 or signals_count > 0
        })

    return {
        "total_students": total_students,
        "average_mastery": overall_avg,
        "weakest_concepts": weakest_concepts,
        "flagged_sessions": list(flagged_sessions_map.values()),
        "students": student_list
    }

@router.get("/student/{student_id}")
def get_student_deep_dive(
    student_id: int,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    student = db.query(User).filter(User.id == student_id, User.role == UserRole.STUDENT.value).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Mastery by concept
    concepts = db.query(Concept).all()
    concept_data = []
    for c in concepts:
        m = db.query(StudentMastery).filter(
            StudentMastery.student_id == student.id,
            StudentMastery.concept_id == c.id
        ).first()
        score = m.mastery if m else 0.0
        concept_data.append({
            "concept_id": c.id,
            "name": c.name,
            "mastery": score,
            "attempts": m.attempts if m else 0,
            "correct_attempts": m.correct_attempts if m else 0
        })

    # History
    history = db.query(MasteryHistory).filter(
        MasteryHistory.student_id == student.id
    ).order_by(MasteryHistory.timestamp.asc()).all()
    history_data = [
        {
            "id": h.id,
            "concept_id": h.concept_id,
            "mastery": h.mastery,
            "change_amount": h.change_amount,
            "reason": h.reason,
            "timestamp": h.timestamp.isoformat()
        }
        for h in history
    ]

    # Submissions
    submissions = db.query(CodingSubmission).filter(
        CodingSubmission.student_id == student.id
    ).order_by(CodingSubmission.created_at.desc()).all()

    sub_data = []
    for sub in submissions:
        # Check viva explanation results
        expl_questions = db.query(ExplanationQuestion).filter(ExplanationQuestion.submission_id == sub.id).all()
        expl_score_sum = 0.0
        ans_count = 0
        for eq in expl_questions:
            ans = db.query(ExplanationAnswer).filter(ExplanationAnswer.explanation_question_id == eq.id).first()
            if ans:
                expl_score_sum += ans.score
                ans_count += 1
        viva_avg = round(expl_score_sum / ans_count, 1) if ans_count > 0 else None

        sub_data.append({
            "id": sub.id,
            "problem_id": sub.problem_id,
            "problem_title": sub.problem.title if sub.problem else "Problem",
            "language": sub.language,
            "status": sub.status,
            "score": sub.score,
            "viva_score": viva_avg,
            "execution_time": sub.execution_time,
            "created_at": sub.created_at.isoformat()
        })

    # Sessions and signals
    sessions = db.query(CodingSession).filter(CodingSession.student_id == student.id).order_by(CodingSession.started_at.desc()).all()
    sessions_data = []
    for sess in sessions:
        sig_count = len(sess.integrity_signals)
        event_count = len(sess.events)
        sessions_data.append({
            "id": sess.id,
            "problem_title": sess.problem.title if sess.problem else "Coding Assessment",
            "started_at": sess.started_at.isoformat(),
            "ended_at": sess.ended_at.isoformat() if sess.ended_at else None,
            "total_events": event_count,
            "signals_count": sig_count
        })

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "created_at": student.created_at.isoformat()
        },
        "concepts": concept_data,
        "history": history_data,
        "submissions": sub_data,
        "sessions": sessions_data
    }
