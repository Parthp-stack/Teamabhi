from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from backend.models.concept import Concept
from backend.models.question import Question, Attempt
from backend.models.mastery import StudentMastery
from backend.services.mastery_service import MasteryService

PREREQUISITE_THRESHOLD = 65.0  # Mastery score required in prerequisites to unlock dependent concept
MASTERY_THRESHOLD = 75.0       # Threshold above which a concept is considered mastered

class AdaptiveEngine:
    @staticmethod
    def get_student_mastery_map(db: Session, student_id: int) -> Dict[int, float]:
        """Fetch a dictionary of concept_id -> mastery_score for a student."""
        records = db.query(StudentMastery).filter(StudentMastery.student_id == student_id).all()
        return {r.concept_id: float(r.mastery_score) for r in records}

    @classmethod
    def evaluate_prerequisites(
        cls,
        concept: Concept,
        mastery_map: Dict[int, float]
    ) -> Dict[str, Any]:
        """
        Verify if all prerequisite concepts have met the required competency threshold.
        """
        prereqs = concept.prerequisites
        if not prereqs:
            return {"eligible": True, "blocking_prereqs": []}

        blocking = []
        for p in prereqs:
            score = mastery_map.get(p.id, 0.0)
            if score < PREREQUISITE_THRESHOLD:
                blocking.append({
                    "id": p.id,
                    "name": p.name,
                    "mastery": score,
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
        res = cls.get_next_question(db, student_id, course_id)
        return {
            "status": "READY",
            "target_concept": {
                "id": res.get("concept_id"),
                "name": res.get("concept"),
                "current_mastery": res.get("current_mastery", 0.0)
            },
            "rationale": res.get("reason"),
            "question": res.get("question")
        }

    @classmethod
    def get_next_question(
        cls,
        db: Session,
        student_id: int,
        course_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Selects the next adaptive question based on the student's weakest eligible prerequisite.
        Does NOT follow a static sequence.
        """
        query = db.query(Concept).order_by(Concept.order_index.asc())
        if course_id:
            query = query.join(Concept.module).filter(Concept.module.has(course_id=course_id))
        all_concepts: List[Concept] = query.all()

        if not all_concepts:
            return {"status": "NO_CONCEPTS", "message": "No concepts registered in course."}

        mastery_map = cls.get_student_mastery_map(db, student_id)

        # Analyze each concept for eligibility and mastery
        concept_candidates = []
        for c in all_concepts:
            score = mastery_map.get(c.id, 0.0)
            prereq_eval = cls.evaluate_prerequisites(c, mastery_map)
            status = MasteryService.get_concept_status(score, prereq_eval["eligible"])

            concept_candidates.append({
                "concept": c,
                "mastery": score,
                "eligible": prereq_eval["eligible"],
                "blocking": prereq_eval["blocking_prereqs"],
                "status": status
            })

        # Find eligible concepts that have not reached full mastery (< 75%)
        unmastered_eligible = [
            cand for cand in concept_candidates
            if cand["eligible"] and cand["mastery"] < MASTERY_THRESHOLD
        ]

        # Target selection:
        # If there are unmastered eligible concepts, select the one with the LOWEST mastery (weakest eligible)
        if unmastered_eligible:
            target_cand = min(unmastered_eligible, key=lambda x: x["mastery"])
            reason = f"This is currently one of your weakest eligible concepts ({target_cand['concept'].name}: {target_cand['mastery']:.0f}% mastery). All prerequisites have met the {PREREQUISITE_THRESHOLD:.0f}% threshold."
        else:
            # If all eligible are mastered, check if any concept is still eligible or choose lowest
            eligible_pool = [c for c in concept_candidates if c["eligible"]]
            if eligible_pool:
                target_cand = min(eligible_pool, key=lambda x: x["mastery"])
                reason = f"Reinforcement practice on eligible concept '{target_cand['concept'].name}'."
            else:
                target_cand = concept_candidates[0]
                reason = "Beginning initial module prerequisites."

        target_concept = target_cand["concept"]
        target_score = target_cand["mastery"]

        # Select appropriate question difficulty based on current concept score
        if target_score < 40.0:
            preferred_diff = "EASY"
        elif target_score < 70.0:
            preferred_diff = "MEDIUM"
        else:
            preferred_diff = "HARD"

        # Fetch candidate questions for the target concept
        # Prioritize questions the student has not yet answered correctly
        answered_correct_ids = [
            a.question_id for a in db.query(Attempt.question_id).filter(
                Attempt.student_id == student_id,
                Attempt.is_correct == True
            ).all()
        ]

        available_questions = db.query(Question).filter(
            Question.concept_id == target_concept.id
        ).all()

        if not available_questions:
            return {
                "concept": target_concept.name,
                "concept_id": target_concept.id,
                "reason": reason,
                "question": None,
                "message": f"No questions available for {target_concept.name}."
            }

        # Filtering: unattempted correct + preferred difficulty
        pool = [q for q in available_questions if q.id not in answered_correct_ids and q.difficulty == preferred_diff]
        if not pool:
            pool = [q for q in available_questions if q.id not in answered_correct_ids]
        if not pool:
            pool = [q for q in available_questions if q.difficulty == preferred_diff] or available_questions

        selected_q = pool[0]

        # Format response as requested in Section 4
        # Notice: correct_answer and explanation are deliberately omitted before answer submission!
        return {
            "concept": target_concept.name,
            "concept_id": target_concept.id,
            "current_mastery": target_score,
            "reason": reason,
            "question": {
                "id": selected_q.id,
                "concept_id": selected_q.concept_id,
                "concept_name": target_concept.name,
                "question_text": selected_q.question_text,
                "question_type": selected_q.question_type,
                "difficulty": selected_q.difficulty,
                "options": selected_q.options
            }
        }

    @classmethod
    def get_learning_path(cls, db: Session, student_id: int) -> Dict[str, Any]:
        """
        Computes the student's adaptive learning path overview as specified in Section 5.
        """
        all_concepts = db.query(Concept).order_by(Concept.order_index.asc()).all()
        mastery_map = cls.get_student_mastery_map(db, student_id)

        completed_concepts = []
        weak_concepts = []
        concepts_data = []

        total_score = 0.0

        for c in all_concepts:
            score = mastery_map.get(c.id, 0.0)
            total_score += score
            prereq_eval = cls.evaluate_prerequisites(c, mastery_map)
            status = MasteryService.get_concept_status(score, prereq_eval["eligible"])

            if score >= MASTERY_THRESHOLD:
                completed_concepts.append(c.name)
            elif score < 50.0:
                weak_concepts.append(c.name)

            concepts_data.append({
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "mastery": score,
                "status": status,
                "eligible": prereq_eval["eligible"],
                "prerequisites": [p.name for p in c.prerequisites],
                "dependents": [d.name for d in c.dependents]
            })

        avg_mastery = round(total_score / len(all_concepts), 1) if all_concepts else 0.0

        # Compute current target
        next_act = cls.get_next_question(db, student_id)
        current_concept = next_act.get("concept", all_concepts[0].name if all_concepts else "None")
        target_score = next_act.get("current_mastery", 0.0)
        reason = next_act.get("reason", "Weak prerequisite")

        return {
            "current_concept": current_concept,
            "mastery": target_score,
            "overall_mastery": avg_mastery,
            "reason": reason,
            "recommended_next": current_concept,
            "completed_concepts": completed_concepts,
            "weak_concepts": weak_concepts,
            "concepts": concepts_data
        }
