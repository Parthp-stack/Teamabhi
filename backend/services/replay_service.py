from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from backend.models.session import Session as CodingSession, SessionEvent
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
        ).order_by(SessionEvent.timestamp).all()

        # Fetch signals
        signals: List[IntegritySignal] = db.query(IntegritySignal).filter(
            IntegritySignal.session_id == session_id
        ).order_by(IntegritySignal.timestamp).all()

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
                    "timestamp": sig.timestamp.isoformat()
                }

            events_data.append({
                "id": ev.id,
                "event_type": ev.event_type,
                "timestamp": ev.timestamp.isoformat(),
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
            "events": events_data,
            "signals": signals_data,
            "summary_verdict": "Evidence for human review (No automatic verdict)"
        }
