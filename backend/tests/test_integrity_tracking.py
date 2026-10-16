import pytest
from datetime import datetime, timezone, timedelta
from backend.database import SessionLocal, Base, engine
from backend.models.user import User, UserRole
from backend.models.session import Session as CodingSession, SessionEvent, CodeRevision
from backend.models.integrity import IntegritySignal
from backend.services.integrity_service import IntegrityService
from backend.services.replay_service import ReplayService
from backend.utils.seed_data import seed_database
from backend.utils.migrate_phase3 import migrate_database

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    migrate_database()
    db = SessionLocal()
    seed_database(db)
    yield db
    db.close()

# 1. Normal typing rhythm test -> Expected: NORMAL_RHYTHM
def test_normal_typing_rhythm(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(
        student_id=student.id,
        assessment_id=1,
        started_at=datetime.now(timezone.utc),
        overall_review_status="INSUFFICIENT_DATA"
    )
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    # Simulate 8 normal typing events spaced by 0.5s with 10 chars each
    t0 = datetime.now(timezone.utc)
    batch = []
    for i in range(8):
        batch.append({
            "client_event_id": f"type-ev-{i}",
            "event_type": "TYPE",
            "timestamp": (t0 + timedelta(seconds=i * 0.8)).isoformat(),
            "inserted_character_count": 12,
            "deleted_character_count": 0,
            "duration": 0.8,
            "code_location": {
                "start_line": i + 1,
                "start_column": 1,
                "end_line": i + 1,
                "end_column": 13
            },
            "current_code": f"# line {i}\nx = {i}"
        })

    res = IntegrityService.save_event_batch(db_session, sess.id, student.id, batch)
    assert res["status"] == "ok"
    assert res["recorded_count"] == 8

    # Query metrics
    metrics = IntegrityService.get_typing_rhythm_metrics(db_session, sess.id)
    assert metrics["review_status"] == "NORMAL_RHYTHM"
    assert "consistent with observed activity" in metrics["status_message"]

# 2. Large paste detection test -> Expected: REVIEW_SUGGESTED
def test_large_paste_detection(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(
        student_id=student.id,
        assessment_id=1,
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    t0 = datetime.now(timezone.utc)
    paste_event = [{
        "client_event_id": "paste-1284",
        "event_type": "PASTE",
        "timestamp": t0.isoformat(),
        "inserted_character_count": 1284,
        "deleted_character_count": 0,
        "code_location": {"start_line": 12, "start_column": 1, "end_line": 48, "end_column": 20},
        "current_code": "def solution():\n    return 'pasted'",
        "metadata": {"charCount": 1284, "preview": "def solution()..."}
    }]

    res = IntegrityService.save_event_batch(db_session, sess.id, student.id, paste_event)
    assert res["recorded_count"] == 1

    ev = db_session.query(SessionEvent).filter(SessionEvent.client_event_id == "paste-1284").first()
    assert ev.review_status == "REVIEW_SUGGESTED"
    assert ev.classification == "Large paste"
    assert "Observed paste event inserted substantial content" in ev.classification_reason
    assert "cheating" not in ev.classification_reason.lower()

# 3. Rapid bulk insertion test -> Expected: REVIEW_SUGGESTED
def test_rapid_bulk_insertion(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(
        student_id=student.id,
        assessment_id=1,
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    t0 = datetime.now(timezone.utc)
    # Insert 300 characters in 0.2s as TYPE event
    rapid_event = [{
        "client_event_id": "rapid-type-300",
        "event_type": "TYPE",
        "timestamp": t0.isoformat(),
        "inserted_character_count": 300,
        "deleted_character_count": 0,
        "duration": 0.2,
        "current_code": "class ComplexSystem:\n    pass\n" * 10
    }]

    res = IntegrityService.save_event_batch(db_session, sess.id, student.id, rapid_event)
    ev = db_session.query(SessionEvent).filter(SessionEvent.client_event_id == "rapid-type-300").first()
    assert ev.review_status == "REVIEW_SUGGESTED"
    assert ev.classification == "Rapid bulk insertion"
    assert "faster than observed typing rhythm" in ev.classification_reason

# 4. Deletion tracking with code location
def test_deletion_tracking(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    del_event = [{
        "client_event_id": "del-1",
        "event_type": "DELETE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inserted_character_count": 0,
        "deleted_character_count": 35,
        "code_location": {"start_line": 15, "start_column": 1, "end_line": 16, "end_column": 10}
    }]

    IntegrityService.save_event_batch(db_session, sess.id, student.id, del_event)
    ev = db_session.query(SessionEvent).filter(SessionEvent.client_event_id == "del-1").first()
    assert ev.event_type == "DELETE"
    assert ev.deleted_character_count == 35
    assert ev.code_location["start_line"] == 15
    assert ev.review_status == "NORMAL_RHYTHM"

# 5. Replacement tracking
def test_replacement_tracking(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    rep_event = [{
        "client_event_id": "rep-1",
        "event_type": "REPLACE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inserted_character_count": 120,
        "deleted_character_count": 110,
        "code_location": {"start_line": 5, "start_column": 1, "end_line": 10, "end_column": 20}
    }]

    IntegrityService.save_event_batch(db_session, sess.id, student.id, rep_event)
    ev = db_session.query(SessionEvent).filter(SessionEvent.client_event_id == "rep-1").first()
    assert ev.classification == "Replacement"
    assert ev.review_status == "REVIEW_SUGGESTED"

# 6. Run, Submission, and Edit After Run tracking
def test_run_submission_edit_after_run(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    events = [
        {"client_event_id": "run-1", "event_type": "RUN", "timestamp": datetime.now(timezone.utc).isoformat()},
        {"client_event_id": "edit-after-run-1", "event_type": "EDIT_AFTER_RUN", "inserted_character_count": 20, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"client_event_id": "sub-1", "event_type": "SUBMIT", "timestamp": datetime.now(timezone.utc).isoformat()}
    ]

    IntegrityService.save_event_batch(db_session, sess.id, student.id, events)
    ev_run = db_session.query(SessionEvent).filter(SessionEvent.client_event_id == "run-1").first()
    ev_edit = db_session.query(SessionEvent).filter(SessionEvent.client_event_id == "edit-after-run-1").first()
    ev_sub = db_session.query(SessionEvent).filter(SessionEvent.client_event_id == "sub-1").first()

    assert ev_run.event_type == "RUN"
    assert ev_edit.event_type == "EDIT_AFTER_RUN"
    assert ev_sub.event_type == "SUBMIT"

# 7. Visibility and Focus tracking
def test_visibility_tracking(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    events = [
        {"client_event_id": "blur-1", "event_type": "BLUR", "metadata": {"action": "blur"}, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"client_event_id": "vis-1", "event_type": "VISIBILITY_CHANGE", "metadata": {"hidden": True}, "timestamp": datetime.now(timezone.utc).isoformat()}
    ]

    IntegrityService.save_event_batch(db_session, sess.id, student.id, events)
    ev_vis = db_session.query(SessionEvent).filter(SessionEvent.client_event_id == "vis-1").first()
    assert ev_vis.event_type == "VISIBILITY_CHANGE"
    assert ev_vis.event_metadata["hidden"] is True

# 8. Insufficient data classification for brief session
def test_insufficient_data_status(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    # Only 2 typing events recorded
    brief_events = [
        {"client_event_id": "short-1", "event_type": "TYPE", "inserted_character_count": 5, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"client_event_id": "short-2", "event_type": "TYPE", "inserted_character_count": 8, "timestamp": datetime.now(timezone.utc).isoformat()}
    ]
    IntegrityService.save_event_batch(db_session, sess.id, student.id, brief_events)

    status = IntegrityService.update_session_review_status(db_session, sess.id)
    assert status == "INSUFFICIENT_DATA"

    metrics = IntegrityService.get_typing_rhythm_metrics(db_session, sess.id)
    assert metrics["review_status"] == "INSUFFICIENT_DATA"
    assert "Insufficient data" in metrics["status_message"]

# 9. Duplicate retry idempotency (Network retry protection)
def test_duplicate_retry_idempotency(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    events = [
        {"client_event_id": "idemp-101", "event_type": "TYPE", "inserted_character_count": 15, "timestamp": datetime.now(timezone.utc).isoformat()}
    ]

    # First send
    res1 = IntegrityService.save_event_batch(db_session, sess.id, student.id, events)
    assert res1["recorded_count"] == 1
    assert res1["skipped_duplicates"] == 0

    # Retry same packet
    res2 = IntegrityService.save_event_batch(db_session, sess.id, student.id, events)
    assert res2["recorded_count"] == 0
    assert res2["skipped_duplicates"] == 1

    # Verify database has exactly 1 entry for this session
    count = db_session.query(SessionEvent).filter(SessionEvent.session_id == sess.id, SessionEvent.client_event_id == "idemp-101").count()
    assert count == 1

# 10. Code Revision comparison & reconstruction
def test_code_revision_comparison(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    # First revision
    ev1 = [{"client_event_id": f"rev-1-{sess.id}", "event_type": "TYPE", "inserted_character_count": 20, "current_code": "def hello():\n    pass", "timestamp": datetime.now(timezone.utc).isoformat()}]
    IntegrityService.save_event_batch(db_session, sess.id, student.id, ev1)

    # Second revision (major edit)
    ev2 = [{"client_event_id": f"rev-2-{sess.id}", "event_type": "TYPE", "inserted_character_count": 30, "current_code": "def hello():\n    print('world')", "timestamp": datetime.now(timezone.utc).isoformat()}]
    IntegrityService.save_event_batch(db_session, sess.id, student.id, ev2)

    second_ev = db_session.query(SessionEvent).filter(SessionEvent.session_id == sess.id, SessionEvent.client_event_id == f"rev-2-{sess.id}").first()
    assert second_ev.revision_id is not None

    comp = ReplayService.get_revision_comparison(db_session, sess.id, second_ev.revision_id)
    assert comp is not None
    assert comp["before_code"] == "def hello():\n    pass"
    assert comp["current_code"] == "def hello():\n    print('world')"

# 11. Security & Access Control
def test_access_control_security(db_session):
    student_a = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    student_b = db_session.query(User).filter(User.email == "student.b@adaptive.edu").first()

    sess_a = CodingSession(student_id=student_a.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess_a)
    db_session.commit()
    db_session.refresh(sess_a)

    # Student B attempting to inject events into Student A's session must raise PermissionError
    malicious_event = [{"client_event_id": "hacked-1", "event_type": "PASTE", "inserted_character_count": 500}]
    with pytest.raises(PermissionError):
        IntegrityService.save_event_batch(db_session, sess_a.id, student_b.id, malicious_event)

# 12. Write -> Run -> Fix Cycle (NO_CYCLE) Detection
def test_no_cycle_detection(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    t0 = datetime.now(timezone.utc)
    events = [
        {"client_event_id": "cycle-paste", "event_type": "PASTE", "inserted_character_count": 350, "timestamp": t0.isoformat()},
        {"client_event_id": "cycle-sub", "event_type": "SUBMIT", "inserted_character_count": 0, "timestamp": (t0 + timedelta(seconds=10)).isoformat()}
    ]
    IntegrityService.save_event_batch(db_session, sess.id, student.id, events)

    signals = IntegrityService.analyze_session_events(db_session, sess.id)
    types = [s.signal_type for s in signals]
    assert "NO_CYCLE" in types
    assert "LARGE_PASTE" in types

    no_cycle_sig = next(s for s in signals if s.signal_type == "NO_CYCLE")
    assert "Evidence for review" in no_cycle_sig.description
    assert "cheating" not in no_cycle_sig.description.lower()

# 13. Trainer Review Workflow Actions (Mark Reviewed, Dismiss, Add Note)
def test_trainer_review_actions(db_session):
    trainer = db_session.query(User).filter(User.role == UserRole.TRAINER.value).first()
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()

    sess = CodingSession(student_id=student.id, assessment_id=1, started_at=datetime.now(timezone.utc))
    db_session.add(sess)
    db_session.commit()
    db_session.refresh(sess)

    res = IntegrityService.apply_trainer_review_action(
        db=db_session,
        session_id=sess.id,
        trainer_user_id=trainer.id,
        action="ADD_NOTE",
        notes="Reviewed student coding interview; legitimate development observed."
    )
    assert res["status"] == "success"
    assert "Reviewed student coding interview" in res["review_notes"]

    # Mark reviewed
    res_rev = IntegrityService.apply_trainer_review_action(
        db=db_session,
        session_id=sess.id,
        trainer_user_id=trainer.id,
        action="MARK_REVIEWED"
    )
    assert res_rev["is_reviewed"] is True

# 14. Data Retention Cleanup
def test_retention_cleanup(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()

    # Create an old session from 120 days ago that was reviewed
    old_time = datetime.now(timezone.utc) - timedelta(days=120)
    old_sess = CodingSession(
        student_id=student.id,
        assessment_id=1,
        started_at=old_time,
        is_reviewed=True
    )
    db_session.add(old_sess)
    db_session.commit()
    old_id = old_sess.id

    # Run cleanup with 90 days retention
    deleted = IntegrityService.cleanup_expired_records(db_session, retention_days=90)
    assert deleted >= 1

    # Verify old session was removed
    chk = db_session.query(CodingSession).filter(CodingSession.id == old_id).first()
    assert chk is None
