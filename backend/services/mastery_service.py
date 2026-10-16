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
        reason_detail: str = "",
        time_taken: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Explainable Bayesian-inspired knowledge tracing update with time-based calibration:
        - Correct easy question: small increase
        - Correct hard question: large increase
        - Wrong easy question: moderate-to-large penalty
        - Wrong hard question: small penalty
        - Fast + correct: stronger mastery (+25% speed bonus)
        - Slow + correct: modest mastery gain (-15% speed penalty)
        - Fast + wrong: hurried slip factor
        - Slow + wrong: deeper misconception factor
        - Bounded strictly within [0, 100] with headroom & floor damping.
        """
        mastery_record = MasteryService.get_or_create_mastery(db, student_id, concept_id)
        current = float(mastery_record.mastery_score)
        diff_key = difficulty.upper() if difficulty else "MEDIUM"
        weights = DIFFICULTY_WEIGHTS.get(diff_key, DIFFICULTY_WEIGHTS["MEDIUM"])

        # Time-based factor evaluation
        time_note = ""
        time_mult = 1.0
        if time_taken is not None and time_taken > 0:
            if is_correct:
                if time_taken < 30.0:
                    time_mult = 1.25
                    time_note = f" (Fast {time_taken:.1f}s: +25% speed bonus)"
                elif time_taken >= 60.0:
                    time_mult = 0.85
                    time_note = f" (Slow {time_taken:.1f}s: modest increase)"
                else:
                    time_note = f" ({time_taken:.1f}s)"
            else:
                if time_taken < 15.0:
                    time_mult = 0.90
                    time_note = f" (Hurried {time_taken:.1f}s: possible careless mistake)"
                elif time_taken >= 45.0:
                    time_mult = 1.15
                    time_note = f" (Prolonged {time_taken:.1f}s: concept needs review)"
                else:
                    time_note = f" ({time_taken:.1f}s)"

        if is_correct:
            # Diminishing returns headroom factor
            headroom = (100.0 - current) / 100.0
            delta = weights["correct_boost"] * (0.35 + 0.65 * headroom) * time_mult
            new_score = min(100.0, current + delta)
            mastery_record.correct_attempts += 1
            reason = f"Correct on {diff_key} question: +{delta:.1f}%{time_note} ({reason_detail})"
        else:
            # Floor damping factor
            floor_room = current / 100.0
            delta = -(weights["wrong_penalty"] * (0.35 + 0.65 * floor_room) * time_mult)
            new_score = max(0.0, current + delta)
            reason = f"Incorrect on {diff_key} question: {delta:.1f}%{time_note} ({reason_detail})"

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
            "correct_attempts": mastery_record.correct_attempts,
            "time_feedback": time_note.strip()
        }

    @staticmethod
    def get_concept_status(mastery_score: float, are_prereqs_met: bool, attempts: int = 1) -> str:
        """
        Visual status representation:
        - LOCKED: Prerequisite incomplete (< 65%)
        - NOT_STARTED: 0 attempts
        - MASTERED: Mastery >= 80% (or >= 75%)
        - DEVELOPING: 60% <= Mastery < 80%
        - LEARNING: 30% <= Mastery < 60%
        - WEAK: Mastery < 50% with attempts
        """
        if not are_prereqs_met:
            return "LOCKED"
        if attempts == 0 and mastery_score == 0.0:
            return "NOT_STARTED"
        if mastery_score >= 75.0:
            return "MASTERED"
        if mastery_score >= 60.0:
            return "DEVELOPING"
        if mastery_score >= 35.0:
            return "LEARNING"
        return "WEAK"

