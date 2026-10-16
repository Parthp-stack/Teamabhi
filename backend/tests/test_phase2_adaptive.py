import pytest
import asyncio
from datetime import datetime, timezone
from backend.database import SessionLocal, Base, engine
from backend.models.user import User, UserRole
from backend.models.course import Course, Module
from backend.models.concept import Concept, ConceptPrerequisite
from backend.models.question import Question, Attempt
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.services.mastery_service import MasteryService
from backend.services.adaptive_engine import AdaptiveEngine
from backend.services.ai_service import AIService
from backend.utils.security import hash_password, create_access_token, decode_access_token
from backend.utils.seed_data import seed_database

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    # Clean up any leftover test concepts from previous runs
    session.query(Concept).filter(Concept.name.like("%Test%")).delete()
    session.commit()
    seed_database(session)
    yield session
    session.close()

# 1. Creating concepts (cleans up after itself)
def test_create_concept(db):
    module = db.query(Module).first()
    concept = Concept(
        module_id=module.id,
        name="Temporary Test Concept",
        description="Testing concept creation",
        difficulty="MEDIUM",
        order_index=99
    )
    db.add(concept)
    db.commit()
    db.refresh(concept)
    assert concept.id is not None
    assert concept.name == "Temporary Test Concept"
    
    # Clean up so other tests retain the standard OOP concept graph
    db.delete(concept)
    db.commit()

# 2. Creating prerequisite relationships
def test_create_prerequisite_relationship(db):
    c_classes = db.query(Concept).filter(Concept.name == "Classes").first()
    c_objects = db.query(Concept).filter(Concept.name == "Objects").first()
    
    prereq_ids = [p.id for p in c_objects.prerequisites]
    assert c_classes.id in prereq_ids

# 3. Recording an attempt
def test_record_attempt(db):
    student = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
    question = db.query(Question).first()
    
    attempt = Attempt(
        student_id=student.id,
        question_id=question.id,
        selected_answer=question.correct_answer,
        is_correct=True,
        score=1.0,
        time_taken=10.5
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    assert attempt.id is not None
    assert attempt.is_correct is True

# 4. Updating mastery (Bayesian difficulty weighted)
def test_update_mastery(db):
    student = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
    concept = db.query(Concept).filter(Concept.name == "Constructors").first()
    
    res_easy = MasteryService.update_mastery(
        db, student.id, concept.id, is_correct=True, difficulty="EASY", reason_detail="Test Easy"
    )
    assert res_easy["delta"] > 0
    
    res_hard_wrong = MasteryService.update_mastery(
        db, student.id, concept.id, is_correct=False, difficulty="HARD", reason_detail="Test Hard Wrong"
    )
    assert res_hard_wrong["delta"] < 0
    assert abs(res_hard_wrong["delta"]) < 4.0

# 5. Finding weakest concept
def test_find_weakest_concept(db):
    student = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
    path = AdaptiveEngine.get_learning_path(db, student.id)
    assert "weak_concepts" in path
    assert len(path["weak_concepts"]) > 0

# 6. Respecting prerequisites
def test_respecting_prerequisites(db):
    # Student B has Classes at 40%, which is below the 65% prerequisite threshold
    student_b = db.query(User).filter(User.email == "student.b@adaptive.edu").first()
    c_objects = db.query(Concept).filter(Concept.name == "Objects").first()
    mastery_map = AdaptiveEngine.get_student_mastery_map(db, student_b.id)
    
    eval_res = AdaptiveEngine.evaluate_prerequisites(c_objects, mastery_map)
    assert eval_res["eligible"] is False
    assert len(eval_res["blocking_prereqs"]) > 0

# 7. Selecting the next question based on weakest eligible prerequisite
def test_selecting_next_question(db):
    student_a = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
    res = AdaptiveEngine.get_next_question(db, student_a.id)
    assert res["concept"] == "Constructors"
    assert res["question"] is not None
    assert "question_text" in res["question"]
    assert "correct_answer" not in res["question"]

# 8. Student isolation (different learning paths)
def test_student_isolation_and_different_paths(db):
    student_a = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
    student_b = db.query(User).filter(User.email == "student.b@adaptive.edu").first()
    
    res_a = AdaptiveEngine.get_next_question(db, student_a.id)
    res_b = AdaptiveEngine.get_next_question(db, student_b.id)
    
    assert res_a["concept"] == "Constructors"
    assert res_b["concept"] == "Classes"
    assert res_a["concept"] != res_b["concept"]

# 9. Authentication requirements and JWT token decoding
def test_auth_requirements():
    token = create_access_token({"sub": "99", "role": "STUDENT"})
    decoded = decode_access_token(token)
    assert decoded["sub"] == "99"
    assert decoded["role"] == "STUDENT"

# 10. AI service error handling and graceful fallbacks
def test_ai_service_fallbacks():
    async def run_ai_tests():
        q = await AIService.generate_question("Inheritance", "MEDIUM", "MCQ")
        assert "question_text" in q
        assert "correct_answer" in q
        
        expl = await AIService.explain_concept("Polymorphism", 45.0, "MEDIUM")
        assert "explanation" in expl
        assert "example" in expl
        
        practice = await AIService.generate_practice("Constructors", ["__init__"])
        assert len(practice) >= 1
    
    asyncio.run(run_ai_tests())
