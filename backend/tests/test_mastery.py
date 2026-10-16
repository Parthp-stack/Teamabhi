import pytest
from backend.services.mastery_service import MasteryService
from backend.database import SessionLocal, Base, engine
from backend.models.user import User
from backend.models.concept import Concept
from backend.utils.seed_data import seed_database

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    yield db
    db.close()

def test_mastery_incremental_update(db_session):
    student = db_session.query(User).filter(User.email == "student.a@adaptive.edu").first()
    concept = db_session.query(Concept).filter(Concept.name == "Classes").first()
    
    # Test correct answer on medium question
    res_correct = MasteryService.update_mastery(
        db=db_session,
        student_id=student.id,
        concept_id=concept.id,
        is_correct=True,
        difficulty="MEDIUM",
        reason_detail="Test correct"
    )
    assert res_correct["new_mastery"] >= res_correct["previous_mastery"]
    assert res_correct["delta"] > 0

    # Test wrong answer on medium question
    res_wrong = MasteryService.update_mastery(
        db=db_session,
        student_id=student.id,
        concept_id=concept.id,
        is_correct=False,
        difficulty="MEDIUM",
        reason_detail="Test wrong"
    )
    assert res_wrong["new_mastery"] <= res_wrong["previous_mastery"]
    assert res_wrong["delta"] < 0
