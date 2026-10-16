from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.integrity import IntegritySignal
from backend.schemas.integrity import IntegritySignalResponse
from backend.utils.security import get_current_user
from backend.services.integrity_service import IntegrityService

router = APIRouter(prefix="/integrity", tags=["Integrity Evidence Analysis"])

@router.get("/sessions/{session_id}/signals", response_model=List[IntegritySignalResponse])
def get_session_signals(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    signals = IntegrityService.analyze_session_events(db, session_id)
    return {
        "status": "completed",
        "session_id": session_id,
        "signals_count": len(signals),
        "disclaimer": "Evidence collected for human review. No automatic cheating verdict."
    }
