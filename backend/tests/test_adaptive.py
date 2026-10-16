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

    # Student A has completed Classes (90%) and Objects (85%), but weak in Constructors (40%)
    assert act_a["status"] == "READY"
    assert act_a["target_concept"]["name"] == "Constructors"

    # Student B has weak Classes (40%), so Objects is locked; next target is Classes
    assert act_b["status"] == "READY"
    assert act_b["target_concept"]["name"] == "Classes"

    # Confirms distinct adaptive learning paths!
    assert act_a["target_concept"]["name"] != act_b["target_concept"]["name"]
