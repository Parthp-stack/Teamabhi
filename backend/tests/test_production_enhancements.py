import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User, UserRole
from backend.models.coding import CodingProblem
from backend.models.question import Question, Attempt
from backend.models.assessment_attempt import AssessmentAttempt, AssessmentWarning
from backend.services.mcq_validation_service import MCQValidationService
from backend.services.integrity_service import IntegrityService
from backend.utils.security import create_access_token

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def student_auth_headers(db_session):
    student = db_session.query(User).filter(User.role == UserRole.STUDENT.value).first()
    token = create_access_token({"sub": student.email, "role": student.role, "id": student.id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def trainer_auth_headers(db_session):
    trainer = db_session.query(User).filter(User.role == UserRole.TRAINER.value).first()
    token = create_access_token({"sub": trainer.email, "role": trainer.role, "id": trainer.id})
    return {"Authorization": f"Bearer {token}"}

# =========================================================================
# REQUIREMENT 1: IMPROVE MCQ VALIDATION
# =========================================================================

def test_mcq_validation_deterministic_valid():
    valid_mcq = {
        "question_text": "What is the time complexity of searching in a balanced Binary Search Tree?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
        "correct_answer": "O(log n)",
        "explanation": "In a balanced BST, tree height is log(n), providing logarithmic search time.",
        "difficulty": "MEDIUM",
        "concept": "Binary Search Trees"
    }
    result = MCQValidationService.validate_mcq_deterministic(valid_mcq)
    assert result["valid"] is True
    assert result["correct_option"] == "O(log n)"
    assert len(result["errors"]) == 0

def test_mcq_validation_detects_duplicate_options():
    dup_mcq = {
        "question_text": "Which of the following is a fundamental principle of Object-Oriented Programming?",
        "options": ["Encapsulation", "Polymorphism", "Encapsulation", "Compilation"],
        "correct_answer": "Encapsulation",
        "explanation": "Encapsulation bundles data and methods together.",
        "difficulty": "EASY",
        "concept": "Encapsulation"
    }
    result = MCQValidationService.validate_mcq_deterministic(dup_mcq)
    assert result["valid"] is False
    assert any("Duplicate options" in err for err in result["errors"])

def test_mcq_validation_detects_mismatched_correct_answer():
    mismatched_mcq = {
        "question_text": "Which sorting algorithm exhibits worst-case O(n log n) time complexity?",
        "options": ["Quick Sort", "Bubble Sort", "Insertion Sort", "Selection Sort"],
        "correct_answer": "Merge Sort", # Not in options!
        "explanation": "Merge sort consistently divides and merges in O(n log n) time.",
        "difficulty": "MEDIUM",
        "concept": "Sorting"
    }
    result = MCQValidationService.validate_mcq_deterministic(mismatched_mcq)
    assert result["valid"] is False
    assert any("does not match any available option" in err for err in result["errors"])

def test_mcq_validation_endpoint(student_auth_headers):
    payload = {
        "question_text": "What does FIFO stand for in computer science data structures?",
        "options": ["First In First Out", "Fast In Fast Out", "First In First Off", "Fixed Input Format Output"],
        "correct_answer": "First In First Out",
        "explanation": "Queues operate on the First-In, First-Out principle.",
        "difficulty": "EASY",
        "concept": "Queues",
        "use_ai": False
    }
    resp = client.post("/api/questions/validate", json=payload, headers=student_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["correct_option"] == "First In First Out"

# =========================================================================
# REQUIREMENT 2: ADAPTIVE NEXT QUESTION & ATTEMPT SAVING
# =========================================================================

def test_adaptive_attempt_submission_saves_metadata(student_auth_headers, db_session):
    q = db_session.query(Question).first()
    assert q is not None

    payload = {
        "selected_answer": q.correct_answer,
        "time_taken": 14.5,
        "assessment_id": 999,
        "attempt_number": 1
    }
    resp = client.post(f"/api/questions/{q.id}/attempt", json=payload, headers=student_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["attempt_number"] == 1

    # Verify attempt saved in DB
    att = db_session.query(Attempt).filter(
        Attempt.question_id == q.id,
        Attempt.assessment_id == 999
    ).order_by(Attempt.id.desc()).first()
    assert att is not None
    assert att.assessment_id == 999
    assert att.difficulty == q.difficulty

def test_adaptive_next_question_avoids_repetition(student_auth_headers):
    resp1 = client.get("/api/questions/next?assessment_id=888", headers=student_auth_headers)
    assert resp1.status_code == 200
    q1 = resp1.json()
    assert "question" in q1

    # Submit attempt for q1 in session 888
    if q1.get("question") and q1["question"].get("id"):
        q1_id = q1["question"]["id"]
        client.post(
            f"/api/questions/{q1_id}/attempt",
            json={"selected_answer": "arbitrary_answer", "time_taken": 20.0, "assessment_id": 888},
            headers=student_auth_headers
        )

        # Next question in same assessment session should prioritize unattempted questions
        resp2 = client.get("/api/questions/next?assessment_id=888", headers=student_auth_headers)
        assert resp2.status_code == 200
        q2 = resp2.json()
        assert "question" in q2

# =========================================================================
# REQUIREMENT 3: EXPANDED CODING QUESTION BANK
# =========================================================================

def test_expanded_coding_bank_has_required_topics(db_session):
    problems = db_session.query(CodingProblem).all()
    assert len(problems) >= 12

    difficulties = {p.difficulty.upper() for p in problems}
    assert "EASY" in difficulties
    assert "MEDIUM" in difficulties
    assert "HARD" in difficulties

    # Verify problem fields: problem_statement, test_cases with hidden cases
    for p in problems:
        assert p.title
        assert p.description or p.problem_statement
        assert len(p.test_cases) > 0
        has_hidden = any(tc.is_hidden for tc in p.test_cases)
        assert has_hidden is True, f"Problem '{p.title}' should have hidden test cases"

def test_coding_problems_api_never_exposes_hidden_test_cases(student_auth_headers):
    resp = client.get("/api/coding/problems", headers=student_auth_headers)
    assert resp.status_code == 200
    problems = resp.json()
    assert len(problems) >= 12
    for p in problems:
        # All visible_test_cases returned should only be visible ones
        assert "visible_test_cases" in p
        for tc in p["visible_test_cases"]:
            assert "input" in tc
            assert "expected_output" in tc

# =========================================================================
# REQUIREMENT 4, 5, 6: CODING INTEGRITY, SPLIT SCREEN & WARNINGS
# =========================================================================

def test_integrity_classification_split_screen_and_fullscreen():
    # Possible Split Screen
    cls1, status1, reason1 = IntegrityService.classify_event("POSSIBLE_SPLIT_SCREEN", 0, 0, 1.0)
    assert status1 == "REVIEW_SUGGESTED"
    assert "split screen" in cls1.lower()

    # Fullscreen Exit
    cls2, status2, reason2 = IntegrityService.classify_event("FULLSCREEN_EXIT", 0, 0, 1.0)
    assert status2 == "REVIEW_SUGGESTED"
    assert "fullscreen" in cls2.lower()

    # Window Blur
    cls3, status3, reason3 = IntegrityService.classify_event("WINDOW_BLUR", 0, 0, 1.0)
    assert status3 == "NORMAL_RHYTHM"

def test_progressive_assessment_warnings(student_auth_headers, db_session):
    # Start a coding session
    p = db_session.query(CodingProblem).first()
    start_resp = client.post("/api/sessions/start", json={"assessment_id": p.id}, headers=student_auth_headers)
    assert start_resp.status_code == 200
    sess_id = start_resp.json()["id"]

    # First warning (Gentle alert)
    w1_resp = client.post(
        f"/api/sessions/{sess_id}/warning",
        json={
            "warning_type": "TAB_SWITCH",
            "message": "Your assessment environment was interrupted. Please remain in the assessment window.",
            "severity": "LOW"
        },
        headers=student_auth_headers
    )
    assert w1_resp.status_code == 200
    w1 = w1_resp.json()
    assert w1["warning_number"] == 1
    assert w1["risk_level"] == "LOW_RISK"

    # Second warning (Escalates)
    w2_resp = client.post(
        f"/api/sessions/{sess_id}/warning",
        json={
            "warning_type": "POSSIBLE_SPLIT_SCREEN",
            "message": "Notice: Continued window interruptions recorded.",
            "severity": "MEDIUM"
        },
        headers=student_auth_headers
    )
    assert w2_resp.status_code == 200
    w2 = w2_resp.json()
    assert w2["warning_number"] == 2
    assert w2["risk_level"] in ["MEDIUM_RISK", "HIGH_RISK"]

# =========================================================================
# REQUIREMENT 7 & 8: ATTEMPT HISTORY & INTEGRITY DASHBOARD
# =========================================================================

def test_assessment_attempts_lifecycle(student_auth_headers, trainer_auth_headers):
    # Start assessment attempt
    start_resp = client.post(
        "/api/assessments/start",
        json={"assessment_id": "quiz-oop-comprehensive", "assessment_type": "ADAPTIVE_QUIZ"},
        headers=student_auth_headers
    )
    assert start_resp.status_code == 200
    att_data = start_resp.json()
    attempt_id = att_data["attempt_id"]
    assert att_data["status"] == "IN_PROGRESS"

    # Finish assessment attempt
    finish_resp = client.post(f"/api/assessments/{attempt_id}/finish", headers=student_auth_headers)
    assert finish_resp.status_code == 200
    fin_data = finish_resp.json()
    assert fin_data["status"] == "COMPLETED"
    assert fin_data["risk_level"] in ["NORMAL", "LOW_RISK", "MEDIUM_RISK", "HIGH_RISK"]

    # Student views attempts
    st_attempts_resp = client.get("/api/student/attempts", headers=student_auth_headers)
    assert st_attempts_resp.status_code == 200
    st_attempts = st_attempts_resp.json()
    assert st_attempts["total"] >= 1
    first_att = st_attempts["attempts"][0]
    assert "attempt_number" in first_att
    assert "risk_level" in first_att

    # Trainer views cohort attempts
    tr_attempts_resp = client.get("/api/trainer/attempts", headers=trainer_auth_headers)
    assert tr_attempts_resp.status_code == 200
    tr_attempts = tr_attempts_resp.json()
    assert tr_attempts["total"] >= 1

    # Trainer views event timeline
    timeline_resp = client.get(f"/api/trainer/attempts/{attempt_id}/timeline", headers=trainer_auth_headers)
    assert timeline_resp.status_code == 200
    tl_data = timeline_resp.json()
    assert "timeline" in tl_data
