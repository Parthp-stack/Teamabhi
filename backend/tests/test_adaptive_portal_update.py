import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models.user import User, UserRole, StudentProfile, TeacherProfile
from backend.models.course import Course, Module
from backend.models.concept import Concept
from backend.models.question import Question, Attempt
from backend.models.coding import CodingProblem, CodingSubmission
from backend.models.ai_evaluation import AIEvaluation
from backend.services.sandbox_service import SandboxService
from backend.services.mastery_service import MasteryService
from backend.services.adaptive_engine import AdaptiveEngine
from backend.routes.explanation import classify_understanding_verdict
from backend.utils.security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="module")
def student_user(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    return student

@pytest.fixture(scope="module")
def trainer_user(db_session):
    trainer = db_session.query(User).filter(User.email == "trainer@adaptive.edu").first()
    return trainer

@pytest.fixture(scope="module")
def auth_headers(student_user):
    token = create_access_token({"sub": str(student_user.id), "role": "STUDENT"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def trainer_auth_headers(trainer_user):
    token = create_access_token({"sub": str(trainer_user.id), "role": "TRAINER"})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# REQUIREMENT 1 & 2: Curriculum Structure (Subject -> Topic -> Concept)
# ============================================================================
def test_data_structures_curriculum_hierarchy(db_session):
    ds_course = db_session.query(Course).filter(Course.title == "Data Structures").first()
    assert ds_course is not None, "Data Structures course must exist in database"
    assert ds_course.title == "Data Structures"

    modules = db_session.query(Module).filter(Module.course_id == ds_course.id).all()
    module_names = [m.title for m in modules]
    assert "Searching" in module_names
    assert "Sorting" in module_names
    assert "Linked List" in module_names
    assert "Stack" in module_names
    assert "Queue" in module_names

    # Check Searching module concepts: Linear Search, Binary Search, Sentinel Search
    searching_mod = next(m for m in modules if m.title == "Searching")
    searching_concepts = db_session.query(Concept).filter(Concept.module_id == searching_mod.id).all()
    concept_names = [c.name for c in searching_concepts]
    assert "Linear Search" in concept_names
    assert "Binary Search" in concept_names
    assert any("Sentinel" in name for name in concept_names)

    # Verify Concept model fields: explanation, code_snippet, examples
    bin_search = next(c for c in searching_concepts if c.name == "Binary Search")
    assert bin_search.explanation is not None and len(bin_search.explanation) > 10
    assert bin_search.code_snippet is not None and "def binary_search" in bin_search.code_snippet
    assert bin_search.examples is not None


# ============================================================================
# REQUIREMENT 4 & 10: Concept Breakdown API
# ============================================================================
def test_concept_breakdown_endpoint(auth_headers):
    response = client.get("/api/student/concept-breakdown", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "courses" in data
    assert len(data["courses"]) >= 1

    ds_course = next((c for c in data["courses"] if c["name"] == "Data Structures"), None)
    assert ds_course is not None
    assert len(ds_course["modules"]) >= 5

    # Check concept properties
    searching = next(m for m in ds_course["modules"] if m["name"] == "Searching")
    assert len(searching["concepts"]) >= 3
    sample_concept = searching["concepts"][0]
    assert "status" in sample_concept
    assert "mastery_score" in sample_concept
    assert "explanation" in sample_concept
    assert "code_snippet" in sample_concept
    assert "examples" in sample_concept
    assert "recent_attempts" in sample_concept
    assert sample_concept["status"] in ["MASTERED", "DEVELOPING", "LEARNING", "WEAK", "NOT_STARTED", "LOCKED"]


# ============================================================================
# REQUIREMENT 13: Personalized Adaptive Learning Score API
# ============================================================================
def test_personalized_adaptive_score_endpoint(auth_headers):
    response = client.get("/api/student/adaptive-score", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "adaptive_learning_score" in data
    assert isinstance(data["adaptive_learning_score"], (int, float))
    assert 0 <= data["adaptive_learning_score"] <= 100
    assert "topic_mastery" in data
    assert len(data["topic_mastery"]) > 0
    assert "weak_concepts" in data
    assert "strong_concepts" in data
    assert "total_concepts" in data


# ============================================================================
# REQUIREMENT 3 & 5: Adaptive Question Flow with Topic / Concept Filtering & Time Calibration
# ============================================================================
def test_adaptive_question_flow_topic_filtering(db_session, auth_headers):
    searching_mod = db_session.query(Module).filter(Module.title == "Searching").first()
    assert searching_mod is not None

    response = client.get(f"/api/questions/next?module_id={searching_mod.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "concept_name" in data
    assert data.get("topic_name") == "Searching" or data["concept_name"] in ["Linear Search", "Binary Search", "Sentinel Linear Search"]


def test_time_taken_mastery_calibration(db_session, student_user):
    concept = db_session.query(Concept).first()

    # Fast correct (<30s) should give high mastery boost
    m_fast_correct = MasteryService.update_mastery(
        db=db_session,
        student_id=student_user.id,
        concept_id=concept.id,
        is_correct=True,
        difficulty="MEDIUM",
        time_taken=15.0
    )
    # Slow correct (>60s) should give smaller mastery boost
    m_slow_correct = MasteryService.update_mastery(
        db=db_session,
        student_id=student_user.id,
        concept_id=concept.id,
        is_correct=True,
        difficulty="MEDIUM",
        time_taken=95.0
    )
    assert m_fast_correct["delta"] >= m_slow_correct["delta"], "Fast correct answer should yield higher or equal delta than slow correct"

    # Status check
    assert MasteryService.get_concept_status(85.0, are_prereqs_met=True) == "MASTERED"
    assert MasteryService.get_concept_status(40.0, are_prereqs_met=True) == "LEARNING"
    assert MasteryService.get_concept_status(25.0, are_prereqs_met=True) == "WEAK"
    assert MasteryService.get_concept_status(90.0, are_prereqs_met=False) == "LOCKED"


# ============================================================================
# REQUIREMENT 7: 4-Tier Understanding Verdict Classification
# ============================================================================
def test_4_tier_understanding_verdicts():
    # 1. Correct code + understood
    v1 = classify_understanding_verdict(is_code_correct=True, is_understood=True)
    assert v1 == "Correct code + understood"

    # 2. Correct code + poor understanding
    v2 = classify_understanding_verdict(is_code_correct=True, is_understood=False)
    assert v2 == "Correct code + poor understanding"

    # 3. Wrong code + good conceptual understanding
    v3 = classify_understanding_verdict(is_code_correct=False, is_understood=True)
    assert v3 == "Wrong code + good conceptual understanding"

    # 4. Wrong code + poor understanding
    v4 = classify_understanding_verdict(is_code_correct=False, is_understood=False)
    assert v4 == "Wrong code + poor understanding"


# ============================================================================
# REQUIREMENT 8: Multi-Language Sandbox Execution (Python, C, C++, Java, JS)
# ============================================================================
def test_sandbox_multi_language_execution():
    # 1. Python
    py_code = 'print("Hello Python")'
    py_res = SandboxService.execute_test_case(language="python", source_code=py_code, stdin_data="")
    assert py_res["status"] == "PASSED"
    assert "Hello Python" in py_res["stdout"]

    # 2. C++
    cpp_code = '''#include <iostream>
int main() {
    std::cout << "Hello CPP" << std::endl;
    return 0;
}'''
    cpp_res = SandboxService.execute_test_case(language="cpp", source_code=cpp_code, stdin_data="")
    assert cpp_res["status"] == "PASSED"
    assert "Hello CPP" in cpp_res["stdout"]

    # 3. C
    c_code = '''#include <stdio.h>
int main() {
    printf("Hello C\\n");
    return 0;
}'''
    c_res = SandboxService.execute_test_case(language="c", source_code=c_code, stdin_data="")
    assert c_res["status"] == "PASSED"
    assert "Hello C" in c_res["stdout"]

    # 4. Java
    java_code = '''public class Solution {
    public static void main(String[] args) {
        System.out.println("Hello Java");
    }
}'''
    java_res = SandboxService.execute_test_case(language="java", source_code=java_code, stdin_data="")
    assert java_res["status"] == "PASSED"
    assert "Hello Java" in java_res["stdout"]

    # 5. JavaScript (Node.js)
    js_code = 'console.log("Hello JavaScript");'
    js_res = SandboxService.execute_test_case(language="javascript", source_code=js_code, stdin_data="")
    assert js_res["status"] == "PASSED"
    assert "Hello JavaScript" in js_res["stdout"]


# ============================================================================
# REQUIREMENT 6 & 12: AI Evaluation DB Persistence & Student History
# ============================================================================
def test_ai_evaluation_persistence_and_retrieval(db_session, student_user, auth_headers):
    # Verify seeded AIEvaluation exists for student_a
    evals = db_session.query(AIEvaluation).filter(AIEvaluation.student_id == student_user.id).all()
    assert len(evals) >= 1
    sample_eval = evals[0]
    assert sample_eval.understanding_verdict in [
        "Correct code + understood",
        "Correct code + poor understanding",
        "Wrong code + good conceptual understanding",
        "Wrong code + poor understanding",
    ]
    assert sample_eval.score is not None

    # Test student API retrieval
    res = client.get("/api/explanation/evaluations/student", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert "understanding_verdict" in data[0]
    assert "score" in data[0]


# ============================================================================
# REQUIREMENT 9: Separate Student and Trainer Login Portals
# ============================================================================
def test_separate_student_and_trainer_login():
    # Student login
    res_student = client.post("/api/auth/login", json={"email": "student.a@adaptive.edu", "password": "student123"})
    assert res_student.status_code == 200
    st_data = res_student.json()
    assert st_data["user"]["role"] == "STUDENT"

    # Trainer login
    res_trainer = client.post("/api/auth/login", json={"email": "trainer@adaptive.edu", "password": "trainer123"})
    assert res_trainer.status_code == 200
    tr_data = res_trainer.json()
    assert tr_data["user"]["role"] == "TRAINER"
