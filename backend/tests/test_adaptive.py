import pytest
from backend.services.adaptive_engine import AdaptiveEngine
from backend.database import SessionLocal, Base, engine
from backend.models.user import User
from backend.utils.seed_data import seed_database

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    yield db
    db.close()

def test_student_differentiation(db_session):
    student_a = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    student_b = db_session.query(User).filter(User.email == "student.b@adaptive.edu").first()

    act_a = AdaptiveEngine.get_next_learning_activity(db_session, student_a.id)
    act_b = AdaptiveEngine.get_next_learning_activity(db_session, student_b.id)

    # Student A has weak Inheritance / Polymorphism
    assert act_a["status"] == "READY"
    assert act_a["target_concept"]["name"] in ["Inheritance", "Polymorphism"]

    # Student B has high mastery through Polymorphism, so next target is Dependency Injection
    assert act_b["status"] == "READY"
    assert act_b["target_concept"]["name"] == "Dependency Injection"

    # Confirms distinct adaptive learning paths!
    assert act_a["target_concept"]["name"] != act_b["target_concept"]["name"]
