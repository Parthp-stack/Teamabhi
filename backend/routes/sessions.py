from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from backend.database import get_db
from backend.models.user import User, UserRole
from backend.models.session import Session as CodingSession, SessionEvent
from backend.schemas.session import (
    SessionCreateRequest,
    SessionResponse,
    SessionEventBatchRequest,
    SessionDetailResponse
)
from backend.utils.security import get_current_user
from backend.services.integrity_service import IntegrityService
from backend.services.replay_service import ReplayService

router = APIRouter(prefix="/sessions", tags=["Session Recording & Replay"])

@router.post("/start", response_model=SessionResponse)
def start_session(
    req: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = CodingSession(
        student_id=current_user.id,
        assessment_id=req.assessment_id,
        started_at=datetime.now(timezone.utc),
        overall_review_status="INSUFFICIENT_DATA"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Initial start event
    start_ev = SessionEvent(
        session_id=session.id,
        student_id=current_user.id,
        assessment_id=req.assessment_id,
        event_type="SESSION_START",
        server_timestamp=datetime.now(timezone.utc),
        timestamp=datetime.now(timezone.utc),
        review_status="NORMAL_RHYTHM",
        classification="Session lifecycle",
        classification_reason="Assessment session initiated."
    )
    db.add(start_ev)
    db.commit()

    return session

@router.post("/{session_id}/events")
def record_events_batch(
    session_id: int,
    batch: SessionEventBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Security check: Students cannot write audit records to another student's session
    if current_user.role == UserRole.STUDENT.value and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot modify audit records for another user")

    raw_events = [ev.model_dump() for ev in batch.events]
    res = IntegrityService.save_event_batch(
        db=db,
        session_id=session_id,
        student_id=session.student_id,
        batch_events=raw_events
    )

    return res

@router.post("/{session_id}/end")
def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.role == UserRole.STUDENT.value and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot end another user's session")

    session.ended_at = datetime.now(timezone.utc)

    # Record end event
    end_ev = SessionEvent(
        session_id=session.id,
        student_id=session.student_id,
        assessment_id=session.assessment_id,
        event_type="SESSION_END",
        server_timestamp=datetime.now(timezone.utc),
        timestamp=datetime.now(timezone.utc),
        review_status="NORMAL_RHYTHM",
        classification="Session lifecycle",
        classification_reason="Assessment session terminated."
    )
    db.add(end_ev)
    db.commit()

    # Trigger automatic integrity evidence analysis
    signals = IntegrityService.analyze_session_events(db, session_id)
    overall_status = session.overall_review_status

    return {
        "status": "ended",
        "session_id": session_id,
        "signals_generated": len(signals),
        "overall_review_status": overall_status,
        "disclaimer": "Evidence collected for human review. No automatic cheating verdict."
    }

@router.get("/{session_id}/replay")
def get_session_replay(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Access control: Students can only view their own session replay
    if current_user.role == UserRole.STUDENT.value and session.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: Access to session replay is restricted")

    replay = ReplayService.get_session_replay_data(db, session_id)
    if not replay:
        raise HTTPException(status_code=404, detail="Session replay data not found")
    return replay
