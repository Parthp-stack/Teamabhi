import pytest
import uuid
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User, UserRole
from backend.models.assessment_attempt import AssessmentAttempt, QuestionAttempt
from backend.models.integrity import IntegrityEvent
from backend.models.question import Question
from backend.services.adaptive_engine import AdaptiveEngine
from backend.services.integrity_service import IntegrityService
from backend.utils.security import create_access_token

client = TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def student_token(db):
    student = db.query(User).filter(User.role == UserRole.STUDENT.value).first()
    token = create_access_token({"sub": student.email, "role": student.role, "id": student.id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def trainer_token(db):
    trainer = db.query(User).filter(User.role == UserRole.TRAINER.value).first()
    token = create_access_token({"sub": trainer.email, "role": trainer.role, "id": trainer.id})
    return {"Authorization": f"Bearer {token}"}

# =========================================================================
# 1. QUESTION NAVIGATION & ANSWER PRESERVATION (Requirements 1, 2, 13)
# =========================================================================

def test_assessment_start_and_initial_question(student_token):
    asst_id = f"test_asst_{uuid.uuid4().hex[:6]}"
    res = client.post("/api/assessments/start", json={"assessment_id": asst_id}, headers=student_token)
    assert res.status_code == 200
    data = res.json()
    assert "attempt_id" in data
    assert "current_question" in data
    assert data["current_question"]["question_number"] == 1
    assert data["total_questions"] >= 1

def test_complete_end_to_end_navigation_flow(student_token, db):
    """
    Test exact flow:
    Q1: answer -> Next Question
    Q2: answer -> Next Question
    Q3: click Previous -> Q2 opens -> previous answer is still visible
    Change Q2 answer -> save updated answer
    Go forward again -> verify Q2 contains the updated answer
    """
    asst_id = f"test_asst_nav_{uuid.uuid4().hex[:6]}"
    # Start assessment
    start_res = client.post("/api/assessments/start", json={"assessment_id": asst_id}, headers=student_token)
    assert start_res.status_code == 200
    att_data = start_res.json()
    attempt_id = att_data["attempt_id"]

    # Q1: Select answer and go next
    q1 = att_data["current_question"]
    q1_opt = q1["options"][0] if q1.get("options") else "Option A"
    save_q1 = client.post(f"/api/assessments/{attempt_id}/save-answer", json={
        "question_id": q1["question_id"],
        "selected_answer": q1_opt
    }, headers=student_token)
    assert save_q1.status_code == 200
    assert save_q1.json()["current_question"]["selected_answer"] == q1_opt

    # Next -> Q2
    next_1 = client.post(f"/api/assessments/{attempt_id}/next-question", headers=student_token)
    assert next_1.status_code == 200
    q2_data = next_1.json()
    q2 = q2_data["current_question"]
    assert q2["question_number"] == 2

    # Q2: Select initial answer and go next
    q2_opt_old = q2["options"][0] if q2.get("options") else "Option X"
    save_q2 = client.post(f"/api/assessments/{attempt_id}/save-answer", json={
        "question_id": q2["question_id"],
        "selected_answer": q2_opt_old
    }, headers=student_token)
    assert save_q2.status_code == 200

    # Next -> Q3
    next_2 = client.post(f"/api/assessments/{attempt_id}/next-question", headers=student_token)
    assert next_2.status_code == 200
    q3_data = next_2.json()
    assert q3_data["current_question"]["question_number"] == 3

    # Previous -> Q2 opens, previous answer still visible!
    prev_1 = client.post(f"/api/assessments/{attempt_id}/previous-question", headers=student_token)
    assert prev_1.status_code == 200
    returned_q2 = prev_1.json()["current_question"]
    assert returned_q2["question_number"] == 2
    assert returned_q2["selected_answer"] == q2_opt_old
    assert returned_q2["visited"] is True
    assert returned_q2["answer_status"] == "ANSWERED"

    # Change Q2 answer: Old Answer -> New Answer
    q2_opt_new = q2["options"][1] if len(q2.get("options", [])) > 1 else "Option Y (New)"
    save_q2_updated = client.post(f"/api/assessments/{attempt_id}/save-answer", json={
        "question_id": q2["question_id"],
        "selected_answer": q2_opt_new
    }, headers=student_token)
    assert save_q2_updated.status_code == 200
    assert save_q2_updated.json()["current_question"]["selected_answer"] == q2_opt_new
    assert save_q2_updated.json()["current_question"]["is_changed"] is True

    # Go Previous -> Q1 (check Q1 preserved)
    prev_2 = client.post(f"/api/assessments/{attempt_id}/previous-question", headers=student_token)
    assert prev_2.status_code == 200
    assert prev_2.json()["current_question"]["selected_answer"] == q1_opt

    # Go Forward again -> Q2 (verify Q2 contains the updated answer!)
    fwd_1 = client.post(f"/api/assessments/{attempt_id}/next-question", headers=student_token)
    assert fwd_1.status_code == 200
    fwd_q2 = fwd_1.json()["current_question"]
    assert fwd_q2["question_number"] == 2
    assert fwd_q2["selected_answer"] == q2_opt_new

    # Check assessment state restoration (e.g. on page refresh)
    state_res = client.get(f"/api/assessments/{attempt_id}/state", headers=student_token)
    assert state_res.status_code == 200
    state = state_res.json()
    assert state["attempt_id"] == attempt_id
    assert state["current_question_index"] == 2
    assert len(state["questions"]) >= 3
    assert state["questions"][0]["selected_answer"] == q1_opt
    assert state["questions"][1]["selected_answer"] == q2_opt_new
    assert state["questions"][1]["is_changed"] is True

# =========================================================================
# 2. QUESTION STATE MANAGEMENT (Requirement 2)
# =========================================================================

def test_question_state_records_in_database(student_token, db):
    asst_id = f"test_state_mgmt_{uuid.uuid4().hex[:6]}"
    start_res = client.post("/api/assessments/start", json={"assessment_id": asst_id}, headers=student_token)
    att_id = start_res.json()["attempt_id"]
    q1 = start_res.json()["current_question"]

    # Save answer
    client.post(f"/api/assessments/{att_id}/save-answer", json={
        "question_id": q1["question_id"],
        "selected_answer": "TestAnswer"
    }, headers=student_token)

    # Check QuestionAttempt in database
    qa = db.query(QuestionAttempt).filter(
        QuestionAttempt.attempt_id == att_id,
        QuestionAttempt.question_id == q1["question_id"]
    ).first()

    assert qa is not None
    assert qa.selected_answer == "TestAnswer"
    assert qa.visited is True
    assert qa.answer_status == "ANSWERED"
    assert qa.timestamp is not None

# =========================================================================
# 3. ADAPTIVE QUESTION LOGIC (Requirement 3, 11)
# =========================================================================

def test_adaptive_difficulty_progression(db):
    student = db.query(User).filter(User.role == UserRole.STUDENT.value).first()
    # Correct answer -> next can become harder
    res = AdaptiveEngine.get_next_question(
        db=db,
        student_id=student.id,
        previous_concept="Classes",
        last_was_correct=True,
        last_difficulty="EASY"
    )
    assert res is not None
    assert "question" in res
    assert res["question"]["difficulty"] in ["MEDIUM", "HARD"]

def test_adaptive_remedial_question_on_repeated_wrong_answers(db):
    student = db.query(User).filter(User.role == UserRole.STUDENT.value).first()
    # Repeated wrong answers -> identify weak concept and provide easier/remedial question
    res = AdaptiveEngine.get_next_question(
        db=db,
        student_id=student.id,
        previous_concept="Classes",
        last_was_correct=False,
        consecutive_wrong=2
    )
    assert res is not None
    assert "question" in res
    assert res["question"]["difficulty"] == "EASY"

def test_analyze_previous_attempts_separates_academic_from_integrity(db):
    student = db.query(User).filter(User.role == UserRole.STUDENT.value).first()
    analysis = AdaptiveEngine.analyze_previous_attempts(db, student.id)
    assert "academic_performance" in analysis
    assert "integrity_performance" in analysis
    assert "separation_guarantee" in analysis
    assert analysis["separation_guarantee"] is True
    assert "weak_concepts" in analysis["academic_performance"]
    assert "strong_concepts" in analysis["academic_performance"]
    assert "total_integrity_events" in analysis["integrity_performance"]
    assert "warnings_count" in analysis["integrity_performance"]

# =========================================================================
# 4. STUDENT INTEGRITY & EVENT TRACKING (Requirements 4, 5, 6, 7, 8, 9)
# =========================================================================

def test_record_integrity_events_coding_and_browser(student_token, db):
    events = [
        {"event_type": "COPY / CTRL+C", "action": "Code copied", "details": "Code copied from editor (45 chars)"},
        {"event_type": "PASTE / CTRL+V", "action": "Code pasted", "details": "Code pasted (+120 chars)"},
        {"event_type": "TAB_SWITCH", "action": "Assessment tab hidden", "details": "Student switched tabs"},
        {"event_type": "WINDOW_BLUR", "action": "Window lost focus", "details": "Window blur event"},
        {"event_type": "FULLSCREEN_EXIT", "action": "Fullscreen exited", "details": "Fullscreen mode exited"},
        {"event_type": "POSSIBLE_SPLIT_SCREEN", "action": "Resize anomaly", "details": "Viewport changed from 1920x1080 to 850x900", "metadata": {"width_ratio": 0.44}},
        {"event_type": "CODE_RUN", "action": "Test cases executed", "details": "Sandbox test run"},
        {"event_type": "SUBMISSION", "action": "Code submitted", "details": "Solution submitted"},
    ]

    for ev in events:
        res = client.post("/api/integrity/events", json=ev, headers=student_token)
        assert res.status_code == 200
        data = res.json()
        assert data["event_type"] == ev["event_type"]
        assert data["action"] == ev["action"]

def test_split_screen_detection_preserves_evidence_without_false_accusation(student_token, db):
    res = client.post("/api/integrity/events", json={
        "event_type": "POSSIBLE_SPLIT_SCREEN",
        "action": "Resize anomaly",
        "details": "Viewport changed from 1920x1080 to 850x900",
        "risk_level": "MEDIUM",
        "metadata": {
            "screen_width": 1920,
            "window_width": 850,
            "ratio": 0.44
        }
    }, headers=student_token)
    assert res.status_code == 200
    ev = res.json()
    assert ev["event_type"] == "POSSIBLE_SPLIT_SCREEN"
    assert ev["risk_level"] == "MEDIUM"

def test_progressive_warning_system_does_not_fail_student(student_token, db):
    start = client.post("/api/assessments/start", json={"assessment_id": f"warning_test_{uuid.uuid4().hex[:6]}"}, headers=student_token)
    att_id = start.json()["attempt_id"]

    # First suspicious event in this attempt
    res1 = client.post("/api/integrity/events", json={
        "attempt_id": att_id,
        "event_type": "TAB_SWITCH",
        "action": "Assessment tab hidden",
        "details": "First tab switch"
    }, headers=student_token)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["warning"] is not None
    assert "warning #1" in data1["warning"].lower()

    # Second suspicious event in this attempt -> progressive warning
    res2 = client.post("/api/integrity/events", json={
        "attempt_id": att_id,
        "event_type": "WINDOW_BLUR",
        "action": "Window blur",
        "details": "Second interruption"
    }, headers=student_token)
    assert res2.status_code == 200
    data2 = res2.json()
    assert "warning #2" in data2["warning"].lower()

def test_integrity_events_table_contains_all_12_required_columns(trainer_token):
    res = client.get("/api/integrity/events?limit=50", headers=trainer_token)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "events" in data
    assert len(data["events"]) > 0

    first_event = data["events"][0]
    required_columns = [
        "timestamp",
        "student_name",
        "student_id",
        "assessment",
        "attempt_no",
        "question_no",
        "event_type",
        "action",
        "details",
        "risk_level",
        "warning",
        "source"
    ]
    for col in required_columns:
        assert col in first_event, f"Missing required column: {col}"

def test_integrity_summary_cards_contain_all_11_database_metrics(trainer_token):
    res = client.get("/api/integrity/summary", headers=trainer_token)
    assert res.status_code == 200
    summary = res.json()
    required_metrics = [
        "total_events",
        "copy_events",
        "paste_events",
        "tab_switches",
        "window_blur_events",
        "fullscreen_exits",
        "possible_split_screen_events",
        "code_runs",
        "submissions",
        "warnings",
        "risk_score"
    ]
    for metric in required_metrics:
        assert metric in summary, f"Missing summary card metric: {metric}"
        assert isinstance(summary[metric], (int, float)), f"Metric {metric} must be numeric"

def test_integrity_filtering_and_sorting(trainer_token):
    # Filter by event_type
    res_copy = client.get("/api/integrity/events?event_type=COPY", headers=trainer_token)
    assert res_copy.status_code == 200
    for ev in res_copy.json()["events"]:
        assert "COPY" in ev["event_type"].upper() or "CTRL+C" in ev["event_type"].upper()

    # Filter by risk_level
    res_risk = client.get("/api/integrity/events?risk_level=MEDIUM", headers=trainer_token)
    assert res_risk.status_code == 200
    for ev in res_risk.json()["events"]:
        assert ev["risk_level"].upper() == "MEDIUM"

    # Sorting
    res_asc = client.get("/api/integrity/events?sort_by=timestamp&sort_order=asc", headers=trainer_token)
    assert res_asc.status_code == 200

# =========================================================================
# 5. ATTEMPT HISTORY PRESERVATION (Requirement 10)
# =========================================================================

def test_multiple_attempts_stored_separately(student_token, db):
    unique_asst_id = f"test_multi_att_{uuid.uuid4().hex[:8]}"
    # Start Attempt 1
    att1_res = client.post("/api/assessments/start", json={"assessment_id": unique_asst_id}, headers=student_token)
    att1_id = att1_res.json()["attempt_id"]

    # Finish Attempt 1
    fin1 = client.post(f"/api/assessments/{att1_id}/finish", headers=student_token)
    assert fin1.status_code == 200

    # Start Attempt 2
    att2_res = client.post("/api/assessments/start", json={"assessment_id": unique_asst_id, "resume": False}, headers=student_token)
    att2_id = att2_res.json()["attempt_id"]
    assert att2_id != att1_id

    # Verify both attempts exist separately in database
    a1 = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == att1_id).first()
    a2 = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == att2_id).first()

    assert a1 is not None
    assert a2 is not None
    assert a1.attempt_number == 1
    assert a2.attempt_number == 2
    assert a1.status == "COMPLETED"
    assert a2.status == "IN_PROGRESS"
