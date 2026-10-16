from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from backend.models.concept import Concept
from backend.models.question import Question, Attempt
from backend.models.mastery import StudentMastery
from backend.services.mastery_service import MasteryService

PREREQUISITE_THRESHOLD = 65.0 # Mastery score required in prerequisites to unlock dependent concept

class AdaptiveEngine:
    @staticmethod
    def get_student_concept_mastery_map(db: Session, student_id: int) -> Dict[int, float]:
        masteries = db.query(StudentMastery).filter(StudentMastery.student_id == student_id).all()
        return {m.concept_id: m.mastery for m in masteries}

    @staticmethod
    def evaluate_concept_eligibility(
        concept: Concept,
        mastery_map: Dict[int, float]
    ) -> Dict[str, Any]:
        """
        Check if all prerequisites for this concept have met the competency threshold.
        """
        prereqs = concept.prerequisites
        if not prereqs:
            return {"eligible": True, "blocking_prereqs": []}

        blocking = []
        for p in prereqs:
            p_score = mastery_map.get(p.id, 0.0)
            if p_score < PREREQUISITE_THRESHOLD:
                blocking.append({
                    "id": p.id,
                    "name": p.name,
                    "mastery": p_score,
                    "required": PREREQUISITE_THRESHOLD
                })

        return {
            "eligible": len(blocking) == 0,
            "blocking_prereqs": blocking
        }

    @classmethod
    def get_next_learning_activity(
        cls,
        db: Session,
        student_id: int,
        course_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculates the next adaptive learning target and selects the optimal question.
        Returns explainable rationale for why this question/concept was recommended.
        """
        # 1. Fetch all concepts
        query = db.query(Concept)
        if course_id:
            query = query.join(Concept.module).filter(Concept.module.has(course_id=course_id))
        all_concepts = query.all()

        if not all_concepts:
            return {"status": "NO_CONCEPTS_AVAILABLE", "message": "No concepts registered in course"}

        # 2. Get student mastery scores
        mastery_map = cls.get_student_concept_mastery_map(db, student_id)

        # 3. Analyze eligibility and weak concepts
        concept_analysis: List[Dict[str, Any]] = []
        for c in all_concepts:
            score = mastery_map.get(c.id, 0.0)
            eligibility = cls.evaluate_concept_eligibility(c, mastery_map)
            status = MasteryService.get_concept_status(score, eligibility["eligible"])

            concept_analysis.append({
                "concept": c,
                "mastery": score,
                "eligible": eligibility["eligible"],
                "blocking_prereqs": eligibility["blocking_prereqs"],
                "status": status
            })

        # 4. Filter for eligible concepts that still require learning (< 85% mastery)
        eligible_unmastered = [
            ca for ca in concept_analysis
            if ca["eligible"] and ca["mastery"] < 85.0
        ]

        # If all eligible are mastered, take any eligible with lowest mastery, or first
        if not eligible_unmastered:
            eligible_pool = [ca for ca in concept_analysis if ca["eligible"]]
            if eligible_pool:
                target_record = min(eligible_pool, key=lambda x: x["mastery"])
            else:
                target_record = concept_analysis[0]
        else:
            # Pick lowest mastery among eligible (Weakest Prerequisite / Lowest Eligible Concept)
            target_record = min(eligible_unmastered, key=lambda x: x["mastery"])

        target_concept = target_record["concept"]
        target_mastery = target_record["mastery"]

        # Explainable Rationale
        rationale = (
            f"Selected '{target_concept.name}' (current mastery: {target_mastery:.1f}%). "
            f"All prerequisites have met the {PREREQUISITE_THRESHOLD}% threshold. "
            f"This is your current weakest eligible concept on the learning graph."
        )

        # 5. Select appropriate difficulty based on current mastery
        if target_mastery < 40.0:
            preferred_diff = "EASY"
        elif target_mastery < 75.0:
            preferred_diff = "MEDIUM"
        else:
            preferred_diff = "HARD"

        # 6. Fetch questions for target concept
        # Filter out questions already answered correctly
        answered_correct_ids = [
            a.question_id for a in db.query(Attempt.question_id).filter(
                Attempt.student_id == student_id,
                Attempt.correct == True
            ).all()
        ]

        available_questions = db.query(Question).filter(
            Question.concept_id == target_concept.id
        ).all()

        if not available_questions:
            return {
                "status": "NO_QUESTIONS",
                "target_concept": {
                    "id": target_concept.id,
                    "name": target_concept.name,
                    "mastery": target_mastery
                },
                "rationale": rationale,
                "question": None
            }

        # Filter by preferred difficulty and unmastered first
        preferred_pool = [q for q in available_questions if q.id not in answered_correct_ids and q.difficulty == preferred_diff]
        if not preferred_pool:
            preferred_pool = [q for q in available_questions if q.id not in answered_correct_ids]
        if not preferred_pool:
            # Fallback to any question of preferred difficulty or any question
            preferred_pool = [q for q in available_questions if q.difficulty == preferred_diff] or available_questions

        selected_question = preferred_pool[0]

        return {
            "status": "READY",
            "target_concept": {
                "id": target_concept.id,
                "name": target_concept.name,
                "description": target_concept.description,
                "current_mastery": target_mastery,
                "status": target_record["status"]
            },
            "rationale": rationale,
            "question": {
                "id": selected_question.id,
                "concept_id": selected_question.concept_id,
                "concept_name": target_concept.name,
                "type": selected_question.type,
                "title": selected_question.title,
                "description": selected_question.description,
                "difficulty": selected_question.difficulty,
                "options": selected_question.options
            }
        }
