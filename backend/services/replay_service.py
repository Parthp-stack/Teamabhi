from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from backend.models.session import Session as CodingSession, SessionEvent, CodeRevision
from backend.models.integrity import IntegritySignal
from backend.models.coding import CodingProblem, CodingSubmission

class ReplayService:
    @staticmethod
    def get_session_replay_data(db: Session, session_id: int) -> Optional[Dict[str, Any]]:
        session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
        if not session:
            return None

        # Fetch problem info if available
        problem_title = "Coding Assessment"
        if session.assessment_id:
            prob = db.query(CodingProblem).filter(CodingProblem.id == session.assessment_id).first()
            if prob:
                problem_title = prob.title

        # Fetch latest submission code for this session/student
        latest_sub = db.query(CodingSubmission).filter(
            CodingSubmission.student_id == session.student_id,
            CodingSubmission.problem_id == session.assessment_id
        ).order_by(CodingSubmission.created_at.desc()).first()

        final_code = latest_sub.source_code if latest_sub else ""

        # Fetch events chronologically
        events: List[SessionEvent] = db.query(SessionEvent).filter(
            SessionEvent.session_id == session_id
        ).order_by(SessionEvent.timestamp.asc()).all()

        # Fetch signals
        signals: List[IntegritySignal] = db.query(IntegritySignal).filter(
            IntegritySignal.session_id == session_id
        ).order_by(IntegritySignal.timestamp.asc()).all()

        signal_map = {s.event_id: s for s in signals if s.event_id}

        events_data = []
        for ev in events:
            sig = signal_map.get(ev.id)
            sig_dict = None
            if sig:
                sig_dict = {
                    "id": sig.id,
                    "session_id": sig.session_id,
                    "event_id": sig.event_id,
                    "signal_type": sig.signal_type,
                    "severity": sig.severity,
                    "description": sig.description,
                    "review_status": sig.review_status,
                    "trainer_notes": sig.trainer_notes,
                    "timestamp": sig.timestamp.isoformat()
                }

            events_data.append({
                "id": ev.id,
                "session_id": ev.session_id,
                "client_event_id": ev.client_event_id,
                "event_type": ev.event_type,
                "timestamp": ev.timestamp.isoformat(),
                "server_timestamp": ev.server_timestamp.isoformat() if ev.server_timestamp else ev.timestamp.isoformat(),
                "client_timestamp": ev.client_timestamp.isoformat() if ev.client_timestamp else None,
                "code_location": ev.code_location,
                "revision_id": ev.revision_id,
                "inserted_character_count": ev.inserted_character_count or 0,
                "deleted_character_count": ev.deleted_character_count or 0,
                "duration": ev.duration,
                "review_status": ev.review_status or "NORMAL_RHYTHM",
                "classification": ev.classification or "Normal typing",
                "classification_reason": ev.classification_reason or "Typing rhythm consistent with observed activity.",
                "metadata": ev.event_metadata or {},
                "signal": sig_dict
            })

        signals_data = [
            {
                "id": s.id,
                "session_id": s.session_id,
                "event_id": s.event_id,
                "signal_type": s.signal_type,
                "severity": s.severity,
                "description": s.description,
                "review_status": s.review_status,
                "trainer_notes": s.trainer_notes,
                "timestamp": s.timestamp.isoformat()
            }
            for s in signals
        ]

        return {
            "session_id": session.id,
            "student_id": session.student_id,
            "student_name": session.student.name if session.student else "Student",
            "problem_id": session.assessment_id,
            "problem_title": problem_title,
            "final_source_code": final_code,
            "overall_review_status": session.overall_review_status or "INSUFFICIENT_DATA",
            "is_reviewed": session.is_reviewed or False,
            "review_notes": session.review_notes,
            "events": events_data,
            "signals": signals_data,
            "summary_verdict": "Evidence for human review (No automatic verdict)"
        }

    @staticmethod
    def get_revision_comparison(db: Session, session_id: int, revision_id: int) -> Optional[Dict[str, Any]]:
        revision = db.query(CodeRevision).filter(
            CodeRevision.session_id == session_id,
            CodeRevision.id == revision_id
        ).first()

        if not revision:
            return None

        # Previous revision
        prev_rev = db.query(CodeRevision).filter(
            CodeRevision.session_id == session_id,
            CodeRevision.revision_number < revision.revision_number
        ).order_by(CodeRevision.revision_number.desc()).first()

        # Next revision
        next_rev = db.query(CodeRevision).filter(
            CodeRevision.session_id == session_id,
            CodeRevision.revision_number > revision.revision_number
        ).order_by(CodeRevision.revision_number.asc()).first()

        event = revision.event
        code_location = event.code_location if event else None

        return {
            "revision_id": revision.id,
            "revision_number": revision.revision_number,
            "event_id": revision.event_id,
            "snapshot_type": revision.snapshot_type,
            "diff_summary": revision.diff_summary,
            "before_code": prev_rev.source_code if prev_rev else "",
            "current_code": revision.source_code,
            "after_code": next_rev.source_code if next_rev else revision.source_code,
            "code_location": code_location
        }
