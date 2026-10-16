from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.concept import Concept

# Difficulty weight factors for explainable mastery updates
DIFFICULTY_WEIGHTS = {
    "EASY": {"correct_boost": 4.0, "wrong_penalty": 8.0},
    "MEDIUM": {"correct_boost": 7.0, "wrong_penalty": 5.0},
    "HARD": {"correct_boost": 12.0, "wrong_penalty": 3.0}
}

class MasteryService:
    @staticmethod
    def get_or_create_mastery(db: Session, student_id: int, concept_id: int) -> StudentMastery:
        """Fetch existing mastery record or initialize with mastery = 0 if no attempts."""
        record = db.query(StudentMastery).filter(
            StudentMastery.student_id == student_id,
            StudentMastery.concept_id == concept_id
        ).first()

        if not record:
            record = StudentMastery(
                student_id=student_id,
                concept_id=concept_id,
                mastery_score=0.0,
                attempts=0,
                correct_attempts=0,
                last_attempt_at=datetime.now(timezone.utc)
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        return record

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
        Explainable Bayesian-inspired knowledge tracing update:
        - Correct easy question: small increase
        - Correct hard question: large increase
        - Wrong easy question: moderate-to-large penalty
        - Wrong hard question: small penalty
        - Bounded strictly within [0, 100] with headroom & floor damping.
        """
        mastery_record = MasteryService.get_or_create_mastery(db, student_id, concept_id)
        current = float(mastery_record.mastery_score)
        diff_key = difficulty.upper() if difficulty else "MEDIUM"
        weights = DIFFICULTY_WEIGHTS.get(diff_key, DIFFICULTY_WEIGHTS["MEDIUM"])

        if is_correct:
            # Diminishing returns headroom factor
            headroom = (100.0 - current) / 100.0
            delta = weights["correct_boost"] * (0.35 + 0.65 * headroom)
            new_score = min(100.0, current + delta)
            mastery_record.correct_attempts += 1
            reason = f"Correct on {diff_key} question: +{delta:.1f}% ({reason_detail})"
        else:
            # Floor damping factor
            floor_room = current / 100.0
            delta = -(weights["wrong_penalty"] * (0.35 + 0.65 * floor_room))
            new_score = max(0.0, current + delta)
            reason = f"Incorrect on {diff_key} question: {delta:.1f}% ({reason_detail})"

        mastery_record.attempts += 1
        mastery_record.mastery_score = round(new_score, 1)
        mastery_record.last_attempt_at = datetime.now(timezone.utc)

        # Record history
        history = MasteryHistory(
            student_id=student_id,
            concept_id=concept_id,
            mastery_score=mastery_record.mastery_score,
            change_amount=round(delta, 1),
            reason=reason,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(history)
        db.commit()
        db.refresh(mastery_record)

        return {
            "concept_id": concept_id,
            "previous_mastery": round(current, 1),
            "new_mastery": mastery_record.mastery_score,
            "delta": round(delta, 1),
            "attempts": mastery_record.attempts,
            "correct_attempts": mastery_record.correct_attempts
        }

    @staticmethod
    def get_concept_status(mastery_score: float, are_prereqs_met: bool) -> str:
        """
        Visual status representation:
        - Locked: Prerequisite is incomplete (< 65%)
        - Strong: Mastery >= 75%
        - Developing: 50% <= Mastery < 75%
        - Weak: Mastery < 50%
        """
        if not are_prereqs_met:
            return "LOCKED"
        if mastery_score >= 75.0:
            return "STRONG"
        if mastery_score >= 50.0:
            return "DEVELOPING"
        return "WEAK"
