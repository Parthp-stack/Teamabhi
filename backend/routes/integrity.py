from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from backend.database import get_db
from backend.models.user import User, UserRole
from backend.models.session import Session as CodingSession, SessionEvent, CodeRevision
from backend.models.integrity import IntegritySignal
from backend.models.coding import CodingProblem
from backend.schemas.integrity import (
    IntegritySignalResponse,
    TimelineEventResponse,
    TypingRhythmMetrics,
    CodeRevisionComparison,
    TrainerReviewRequest,
    IntegrityDashboardOverview
)
from backend.utils.security import get_current_user
from backend.services.integrity_service import IntegrityService
from backend.services.replay_service import ReplayService

router = APIRouter(prefix="/integrity", tags=["Coding Integrity & Activity Tracking"])

def require_trainer(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.TRAINER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: This action requires trainer privileges"
        )
    return user

@router.get("/sessions", response_model=IntegrityDashboardOverview)
def get_integrity_dashboard_sessions(
    student_id: Optional[int] = Query(None),
    assessment_id: Optional[int] = Query(None),
    review_status: Optional[str] = Query(None), # NORMAL_RHYTHM, REVIEW_SUGGESTED, INSUFFICIENT_DATA
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    query = db.query(CodingSession).join(User, CodingSession.student_id == User.id)

    if student_id:
        query = query.filter(CodingSession.student_id == student_id)
    if assessment_id:
        query = query.filter(CodingSession.assessment_id == assessment_id)
    if review_status and review_status.upper() != "ALL":
        query = query.filter(CodingSession.overall_review_status == review_status.upper())
    if search:
        query = query.filter(User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))

    sessions = query.order_by(CodingSession.started_at.desc()).all()

    # Calculate overall metrics across all sessions
    all_sessions = db.query(CodingSession).all()
    total_count = len(all_sessions)
    normal_count = sum(1 for s in all_sessions if s.overall_review_status == "NORMAL_RHYTHM")
    review_sugg_count = sum(1 for s in all_sessions if s.overall_review_status == "REVIEW_SUGGESTED")
    insufficient_count = sum(1 for s in all_sessions if s.overall_review_status == "INSUFFICIENT_DATA")
    pending_signals = db.query(IntegritySignal).filter(IntegritySignal.review_status == "PENDING").count()

    session_rows = []
    for s in sessions:
        student = s.student
        problem = db.query(CodingProblem).filter(CodingProblem.id == s.assessment_id).first() if s.assessment_id else None
        
        events = db.query(SessionEvent).filter(SessionEvent.session_id == s.id).all()
        total_evs = len(events)
        paste_evs = sum(1 for e in events if e.event_type.upper() == "PASTE")
        rev_sugg_evs = sum(1 for e in events if e.review_status == "REVIEW_SUGGESTED")

        duration_sec = 0
        if events:
            first_t = events[0].timestamp
            last_t = events[-1].timestamp
            duration_sec = int((last_t - first_t).total_seconds())

        session_rows.append({
            "id": s.id,
            "student_id": s.student_id,
            "student_name": student.name if student else "Unknown",
            "student_email": student.email if student else "",
            "assessment_id": s.assessment_id,
            "problem_title": problem.title if problem else "Coding Assessment",
            "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "duration_seconds": duration_sec,
            "total_events": total_evs,
            "paste_count": paste_evs,
            "review_suggested_count": rev_sugg_evs,
            "overall_review_status": s.overall_review_status,
            "is_reviewed": s.is_reviewed,
            "review_notes": s.review_notes,
            "integrity_signals_count": len(s.integrity_signals)
        })

    return {
        "metrics": {
            "total_sessions": total_count,
            "normal_rhythm_count": normal_count,
            "review_suggested_count": review_sugg_count,
            "insufficient_data_count": insufficient_count,
            "pending_review_signals_count": pending_signals
        },
        "sessions": session_rows
    }

@router.get("/sessions/{session_id}/timeline", response_model=List[TimelineEventResponse])
def get_session_timeline(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.STUDENT.value and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot view audit events of other students")

    events = db.query(SessionEvent).filter(
        SessionEvent.session_id == session_id
    ).order_by(SessionEvent.timestamp.asc()).all()

    signals = db.query(IntegritySignal).filter(IntegritySignal.session_id == session_id).all()
    signal_map = {s.event_id: s for s in signals if s.event_id}

    res = []
    for ev in events:
        sig = signal_map.get(ev.id)
        sig_resp = None
        if sig:
            sig_resp = IntegritySignalResponse.model_validate(sig)

        res.append(TimelineEventResponse(
            id=ev.id,
            session_id=ev.session_id,
            student_id=ev.student_id,
            assessment_id=ev.assessment_id,
            client_event_id=ev.client_event_id,
            event_type=ev.event_type,
            timestamp=ev.timestamp,
            server_timestamp=ev.server_timestamp or ev.timestamp,
            client_timestamp=ev.client_timestamp,
            code_location=ev.code_location,
            revision_id=ev.revision_id,
            inserted_character_count=ev.inserted_character_count or 0,
            deleted_character_count=ev.deleted_character_count or 0,
            duration=ev.duration,
            review_status=ev.review_status or "NORMAL_RHYTHM",
            classification=ev.classification or "Normal typing",
            classification_reason=ev.classification_reason or "Typing rhythm consistent with observed activity.",
            metadata=ev.event_metadata or {},
            signal=sig_resp
        ))

    return res

@router.get("/sessions/{session_id}/rhythm", response_model=TypingRhythmMetrics)
def get_session_typing_rhythm(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.STUDENT.value and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: Access restricted")

    metrics = IntegrityService.get_typing_rhythm_metrics(db, session_id)
    return metrics

@router.get("/sessions/{session_id}/revisions/{revision_id}", response_model=CodeRevisionComparison)
def get_code_revision_comparison(
    session_id: int,
    revision_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.STUDENT.value and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: Access restricted")

    comp = ReplayService.get_revision_comparison(db, session_id, revision_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Code revision comparison not found")

    return comp

@router.post("/sessions/{session_id}/review")
def review_session(
    session_id: int,
    req: TrainerReviewRequest,
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    res = IntegrityService.apply_trainer_review_action(
        db=db,
        session_id=session_id,
        trainer_user_id=current_user.id,
        action=req.action,
        notes=req.notes,
        signal_id=req.signal_id
    )
    return res

@router.post("/cleanup")
def cleanup_integrity_records(
    retention_days: Optional[int] = Query(None),
    current_user: User = Depends(require_trainer),
    db: Session = Depends(get_db)
):
    deleted_count = IntegrityService.cleanup_expired_records(db, retention_days)
    return {
        "status": "success",
        "deleted_sessions_count": deleted_count,
        "retention_days_applied": retention_days
    }

# Backwards compatibility endpoints for Phase 1
@router.get("/sessions/{session_id}/signals", response_model=List[IntegritySignalResponse])
def get_session_signals(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.STUDENT.value and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: Access restricted")

    signals = db.query(IntegritySignal).filter(
        IntegritySignal.session_id == session_id
    ).order_by(IntegritySignal.timestamp.asc()).all()

    return signals

@router.post("/sessions/{session_id}/analyze")
def trigger_session_analysis(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if current_user.role == UserRole.STUDENT.value and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: Access restricted")

    signals = IntegrityService.analyze_session_events(db, session_id)
    return {
        "status": "completed",
        "session_id": session_id,
        "signals_count": len(signals),
        "disclaimer": "Evidence collected for human review. No automatic cheating verdict."
    }
