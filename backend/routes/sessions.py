from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from backend.database import get_db
from backend.models.user import User
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
        started_at=datetime.now(timezone.utc)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
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

    events_to_add = []
    for item in batch.events:
        ev = SessionEvent(
            session_id=session_id,
            event_type=item.event_type,
            timestamp=item.timestamp,
            event_metadata=item.metadata
        )
        events_to_add.append(ev)

    if events_to_add:
        db.add_all(events_to_add)
        db.commit()

    return {"status": "ok", "recorded_count": len(events_to_add)}

@router.post("/{session_id}/end")
def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at = datetime.now(timezone.utc)
    db.commit()

    # Trigger automatic integrity evidence analysis
    signals = IntegrityService.analyze_session_events(db, session_id)

    return {
        "status": "ended",
        "session_id": session_id,
        "signals_generated": len(signals)
    }

@router.get("/{session_id}/replay")
def get_session_replay(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    replay = ReplayService.get_session_replay_data(db, session_id)
    if not replay:
        raise HTTPException(status_code=404, detail="Session replay data not found")
    return replay
