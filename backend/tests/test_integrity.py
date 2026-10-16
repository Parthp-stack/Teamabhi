import pytest
from datetime import datetime, timezone, timedelta
from backend.database import SessionLocal, Base, engine
from backend.models.user import User
from backend.models.session import Session as CodingSession, SessionEvent
from backend.services.integrity_service import IntegrityService
from backend.utils.seed_data import seed_database

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    yield db
    db.close()

def test_integrity_signals_generation(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    t0 = datetime.now(timezone.utc)
    ev_focus = SessionEvent(session_id=sess.id, event_type="FOCUS", timestamp=t0, event_metadata={})
    ev_paste = SessionEvent(
        session_id=sess.id,
        event_type="PASTE",
        timestamp=t0 + timedelta(seconds=5),
        event_metadata={"length": 500, "text": "large pasted block"}
    )
    ev_tab1 = SessionEvent(session_id=sess.id, event_type="TAB_SWITCH", timestamp=t0 + timedelta(seconds=10), event_metadata={})
    ev_tab2 = SessionEvent(session_id=sess.id, event_type="TAB_SWITCH", timestamp=t0 + timedelta(seconds=12), event_metadata={})
    ev_submit = SessionEvent(session_id=sess.id, event_type="SUBMIT", timestamp=t0 + timedelta(seconds=20), event_metadata={})

    db_session.add_all([ev_focus, ev_paste, ev_tab1, ev_tab2, ev_submit])
    db_session.commit()

    signals = IntegrityService.analyze_session_events(db_session, sess.id)
    types = [s.signal_type for s in signals]

    assert "LARGE_PASTE" in types
    assert "TAB_SWITCH" in types
    assert "NO_CYCLE" in types

    for s in signals:
        assert "Evidence for review" in s.description
        assert s.severity in ["LOW", "MEDIUM", "HIGH"]
        assert s.event_id is not None
