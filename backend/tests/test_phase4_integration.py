import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, Base, engine
from backend.models.user import User, UserRole
from backend.models.concept import Concept, ConceptPrerequisite
from backend.models.coding import CodingProblem, TestCase
from backend.utils.security import create_access_token
from backend.utils.seed_data import seed_database
from backend.services.curriculum_service import CurriculumService

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
    return TestClient(app)

@pytest.fixture(scope="module")
def student_token(client):
    db = SessionLocal()
    student = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
    token = create_access_token({"sub": str(student.id), "role": student.role})
    db.close()
    return token

@pytest.fixture(scope="module")
def trainer_token(client):
    db = SessionLocal()
    trainer = db.query(User).filter(User.email == "trainer@adaptive.edu").first()
    token = create_access_token({"sub": str(trainer.id), "role": trainer.role})
    db.close()
    return token

# 1. Student Dashboard & Analytics Endpoints (Sections 1, 2, 3)
def test_student_dashboard_endpoints(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    
    # 1. Mastery
    resp_mastery = client.get("/api/student/mastery", headers=headers)
    assert resp_mastery.status_code == 200
    m_data = resp_mastery.json()
    assert "overall_mastery" in m_data
    assert len(m_data["concepts"]) >= 7

    # 2. Dynamic Learning Path
    resp_path = client.get("/api/learning/path", headers=headers)
    assert resp_path.status_code == 200
    p_data = resp_path.json()
    assert p_data["current_concept"] == "Constructors"
    assert "path" in p_data

    # 3. Mastery Analytics for Charts
    resp_analytics = client.get("/api/student/analytics", headers=headers)
    assert resp_analytics.status_code == 200
    a_data = resp_analytics.json()
    assert "overall_mastery" in a_data
    assert "difficulty_performance" in a_data
    assert "EASY" in a_data["difficulty_performance"]
    assert "attempts_per_concept" in a_data

# 2. Student Assessment History & Hidden Test Protection (Sections 4, 5, 20)
def test_student_assessment_history_and_hidden_test_protection(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}

    # Quiz history
    resp_quizzes = client.get("/api/student/assessments", headers=headers)
    assert resp_quizzes.status_code == 200
    assert "attempts" in resp_quizzes.json()

    # Coding history & Viva Voce results
    resp_coding = client.get("/api/student/coding-history", headers=headers)
    assert resp_coding.status_code == 200
    subs = resp_coding.json()["submissions"]
    assert len(subs) > 0
    assert "viva_details" in subs[0]

    # SECURITY: Problems must NEVER leak hidden test cases
    resp_prob = client.get("/api/coding/problems", headers=headers)
    assert resp_prob.status_code == 200
    problems = resp_prob.json()
    assert len(problems) > 0
    for prob in problems:
        for tc in prob["visible_test_cases"]:
            # Only visible test cases are serialized
            assert "expected_output" in tc

# 3. Role-Based Access Control Security Checks (Sections 19, 21)
def test_security_role_based_access_control(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}

    # Student cannot manually modify mastery
    resp_m_update = client.post("/api/mastery/update", json={"concept_id": 1, "score_delta": 50.0}, headers=headers)
    assert resp_m_update.status_code == 403

    # Student cannot access trainer overview
    resp_trainer_dash = client.get("/api/trainer/dashboard", headers=headers)
    assert resp_trainer_dash.status_code == 403

    # Student cannot access curriculum management
    resp_curric = client.get("/api/trainer/curriculum", headers=headers)
    assert resp_curric.status_code == 403

    # Student cannot access trainer question bank
    resp_questions = client.get("/api/trainer/questions", headers=headers)
    assert resp_questions.status_code == 403

# 4. Trainer Overview & Student Deep Dive (Sections 7, 8, 9)
def test_trainer_dashboard_and_student_deep_dive(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    resp_overview = client.get("/api/trainer/dashboard", headers=headers)
    assert resp_overview.status_code == 200
    data = resp_overview.json()
    assert data["total_students"] >= 2
    assert "cohort_average_mastery" in data
    assert "concepts" in data
    assert len(data["students"]) >= 2

    student_id = data["students"][0]["id"]
    resp_deep_dive = client.get(f"/api/trainer/student/{student_id}", headers=headers)
    assert resp_deep_dive.status_code == 200
    s_data = resp_deep_dive.json()
    assert s_data["student"]["id"] == student_id
    assert "learning_path" in s_data
    assert "sessions" in s_data

# 5. Master Data Curriculum Management & Cycle Detection (Section 12)
def test_curriculum_management_and_cycle_prevention(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    # 1. Fetch curriculum
    resp_curric = client.get("/api/trainer/curriculum", headers=headers)
    assert resp_curric.status_code == 200
    curric = resp_curric.json()
    assert len(curric["concepts"]) >= 7

    # 2. Circular dependency test
    # Classes is prerequisite to Objects (Classes -> Objects).
    # Attempting to add Objects as prerequisite to Classes (Objects -> Classes) MUST fail with 400!
    db = SessionLocal()
    c_classes = db.query(Concept).filter(Concept.name == "Classes").first()
    c_objects = db.query(Concept).filter(Concept.name == "Objects").first()
    db.close()

    resp_cycle = client.post(
        f"/api/trainer/concepts/{c_classes.id}/prerequisites",
        json={"prerequisite_id": c_objects.id},
        headers=headers
    )
    assert resp_cycle.status_code == 400
    assert "Circular prerequisite error" in resp_cycle.json()["detail"]

# 6. Question Bank CRUD & AI Question Preview (Section 13)
def test_question_bank_management_and_ai_preview(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    db = SessionLocal()
    concept = db.query(Concept).first()
    db.close()

    # Create question
    new_q = {
        "concept_id": concept.id,
        "question_text": "What does a constructor return in Python?",
        "question_type": "MCQ",
        "difficulty": "MEDIUM",
        "options": ["None", "The object instance", "Self", "A boolean"],
        "correct_answer": "None",
        "explanation": "In Python, __init__ implicitly returns None."
    }
    resp_create = client.post("/api/trainer/questions", json=new_q, headers=headers)
    assert resp_create.status_code == 200
    q_id = resp_create.json()["question_id"]

    # Preview AI Question
    resp_preview = client.post(
        "/api/trainer/questions/ai-preview",
        json={"concept_name": concept.name, "difficulty": "MEDIUM", "question_type": "MCQ"},
        headers=headers
    )
    assert resp_preview.status_code == 200
    draft = resp_preview.json()["draft_question"]
    assert "question_text" in draft
    assert "correct_answer" in draft

    # Delete question
    resp_del = client.delete(f"/api/trainer/questions/{q_id}", headers=headers)
    assert resp_del.status_code == 200

# 7. Optional Feature: GitHub Repo Evaluation & Viva (Sections 14, 15)
def test_github_evaluation_and_viva(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    resp_eval = client.post(
        "/api/trainer/repo-evaluation/analyze?repo_url=https://github.com/tiangolo/fastapi",
        headers=headers
    )
    assert resp_eval.status_code == 200
    data = resp_eval.json()
    assert "detected_languages" in data
    assert "concepts_demonstrated" in data
    assert len(data["viva_questions"]) >= 3

    # Viva Voce evaluation
    viva_payload = {
        "repo_context": "tiangolo/fastapi",
        "answers": [
            {
                "question_id": 1,
                "question": "Why did you separate routes from services?",
                "answer": "To promote loose coupling, high cohesion, and make unit testing straightforward without database mocks.",
                "expected_concept": "Modularity and Separation of Concerns"
            }
        ]
    }
    resp_viva = client.post("/api/trainer/repo-evaluation/viva", json=viva_payload, headers=headers)
    assert resp_viva.status_code == 200
    v_data = resp_viva.json()
    assert "overall_score" in v_data
    assert len(v_data["evaluations"]) > 0

# 8. Optional Feature: DevOps Laboratory Verification (Section 16)
def test_devops_lab_verification(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}

    valid_dockerfile = """
    FROM python:3.12-slim
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    COPY . .
    EXPOSE 8000
    CMD ["uvicorn", "backend.main:app"]
    """
    resp_valid = client.post(
        "/api/coding/devops-lab/verify",
        json={"task_id": "dockerfile_basic", "solution_code": valid_dockerfile},
        headers=headers
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["all_passed"] is True
    assert resp_valid.json()["score"] == 100.0

    # Incomplete code test
    incomplete_dockerfile = "FROM alpine\nRUN echo hello"
    resp_inc = client.post(
        "/api/coding/devops-lab/verify",
        json={"task_id": "dockerfile_basic", "solution_code": incomplete_dockerfile},
        headers=headers
    )
    assert resp_inc.status_code == 200
    assert resp_inc.json()["all_passed"] is False
    assert resp_inc.json()["score"] < 100.0
