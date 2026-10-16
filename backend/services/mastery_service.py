from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.concept import Concept
from typing import Dict, Any, List

# Difficulty weight factors for mastery updates
DIFFICULTY_WEIGHTS = {
    "EASY": {"correct_boost": 5.0, "wrong_penalty": 7.0},
    "MEDIUM": {"correct_boost": 8.0, "wrong_penalty": 6.0},
    "HARD": {"correct_boost": 12.0, "wrong_penalty": 4.0}
}

class MasteryService:
    @staticmethod
    def get_or_create_mastery(db: Session, student_id: int, concept_id: int) -> StudentMastery:
        mastery = db.query(StudentMastery).filter(
            StudentMastery.student_id == student_id,
            StudentMastery.concept_id == concept_id
        ).first()

        if not mastery:
            mastery = StudentMastery(
                student_id=student_id,
                concept_id=concept_id,
                mastery=0.0,
                attempts=0,
                correct_attempts=0
            )
            db.add(mastery)
            db.commit()
            db.refresh(mastery)
        return mastery

    @staticmethod
    def update_mastery(
        db: Session,
        student_id: int,
        concept_id: int,
        is_correct: bool,
        difficulty: str = "MEDIUM",
        reason_detail: str = ""
    ) -> Dict[str, Any]:
        """
        Bayesian-inspired incremental knowledge tracing update.
        Prevents unrealistic instant jumps from 0 to 100.
        Adjusts delta based on difficulty and current mastery level.
        """
        mastery_record = MasteryService.get_or_create_mastery(db, student_id, concept_id)
        current = mastery_record.mastery
        weights = DIFFICULTY_WEIGHTS.get(difficulty.upper(), DIFFICULTY_WEIGHTS["MEDIUM"])

        if is_correct:
            # Diminishing returns as mastery approaches 100
            headroom = (100.0 - current) / 100.0
            delta = weights["correct_boost"] * (0.4 + 0.6 * headroom)
            new_mastery = min(100.0, current + delta)
            mastery_record.correct_attempts += 1
            reason = f"Correct on {difficulty} question: +{delta:.1f}% ({reason_detail})"
        else:
            # Floor damping as mastery approaches 0
            floor_room = current / 100.0
            delta = -(weights["wrong_penalty"] * (0.4 + 0.6 * floor_room))
            new_mastery = max(0.0, current + delta)
            reason = f"Incorrect on {difficulty} question: {delta:.1f}% ({reason_detail})"

        mastery_record.attempts += 1
        mastery_record.mastery = round(new_mastery, 1)
        mastery_record.updated_at = datetime.now(timezone.utc)

        # Record history
        history = MasteryHistory(
            student_id=student_id,
            concept_id=concept_id,
            mastery=mastery_record.mastery,
            change_amount=round(delta, 1),
            reason=reason
        )
        db.add(history)
        db.commit()
        db.refresh(mastery_record)

        return {
            "concept_id": concept_id,
            "previous_mastery": round(current, 1),
            "new_mastery": mastery_record.mastery,
            "delta": round(delta, 1),
            "total_attempts": mastery_record.attempts,
            "correct_attempts": mastery_record.correct_attempts
        }

    @staticmethod
    def get_concept_status(mastery_score: float, are_prereqs_met: bool) -> str:
        if not are_prereqs_met and mastery_score < 40.0:
            return "LOCKED"
        if mastery_score >= 80.0:
            return "MASTERED"
        if mastery_score >= 50.0:
            return "LEARNING"
        return "WEAK"
