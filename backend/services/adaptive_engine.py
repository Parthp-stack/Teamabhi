from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from backend.models.course import Course
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
        course_id: Optional[int] = None,
        module_id: Optional[int] = None,
        concept_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Selects the next adaptive question based on:
        1. Targeted topic/concept if specified (e.g. Practice Searching, Practice Binary Search)
        2. Student's weakest eligible prerequisite or active weak concept
        3. Prior performance (wrong answer -> retry concept; repeated wrong -> simpler question; fast correct -> higher difficulty)
        """
        query = db.query(Concept).order_by(Concept.order_index.asc())
        if concept_id:
            query = query.filter(Concept.id == concept_id)
        elif module_id:
            query = query.filter(Concept.module_id == module_id)
        elif course_id:
            query = query.join(Concept.module).filter(Concept.module.has(course_id=course_id))
        else:
            first_course = db.query(Course).order_by(Course.id.asc()).first()
            if first_course:
                query = query.join(Concept.module).filter(Concept.module.has(course_id=first_course.id))

        all_concepts: List[Concept] = query.all()

        if not all_concepts:
            return {"status": "NO_CONCEPTS", "message": "No concepts registered for this criteria."}

        mastery_map = cls.get_student_mastery_map(db, student_id)

        # Analyze each concept for eligibility and mastery
        concept_candidates = []
        for c in all_concepts:
            score = mastery_map.get(c.id, 0.0)
            prereq_eval = cls.evaluate_prerequisites(c, mastery_map)
            # If concept_id or module_id was directly selected for focused practice, permit practice
            eligible = prereq_eval["eligible"] if not (concept_id or module_id) else True
            status = MasteryService.get_concept_status(score, eligible)

            concept_candidates.append({
                "concept": c,
                "mastery": score,
                "eligible": eligible,
                "blocking": prereq_eval["blocking_prereqs"],
                "status": status
            })

        # Check recent attempts to see if student just got a question wrong
        recent_attempt = db.query(Attempt).filter(
            Attempt.student_id == student_id
        ).order_by(Attempt.created_at.desc()).first()

        recent_concept_id = recent_attempt.question.concept_id if recent_attempt and recent_attempt.question else None
        recent_wrong = (recent_attempt is not None and not recent_attempt.is_correct)

        # Target selection:
        # If student recently failed a concept and that concept is in our candidate pool, prioritize it!
        target_cand = None
        if recent_wrong and recent_concept_id:
            for cand in concept_candidates:
                if cand["concept"].id == recent_concept_id:
                    target_cand = cand
                    reason = f"Targeting reinforcement for '{cand['concept'].name}' after recent incorrect attempt."
                    break

        if not target_cand:
            # Find eligible concepts that have not reached full mastery (< 75%)
            unmastered_eligible = [
                cand for cand in concept_candidates
                if cand["eligible"] and cand["mastery"] < MASTERY_THRESHOLD
            ]

            if unmastered_eligible:
                target_cand = min(unmastered_eligible, key=lambda x: x["mastery"])
                reason = f"Prioritizing your weakest eligible concept ({target_cand['concept'].name}: {target_cand['mastery']:.0f}% mastery)."
            else:
                eligible_pool = [c for c in concept_candidates if c["eligible"]]
                if eligible_pool:
                    target_cand = min(eligible_pool, key=lambda x: x["mastery"])
                    reason = f"Reinforcement practice on eligible concept '{target_cand['concept'].name}'."
                else:
                    target_cand = concept_candidates[0]
                    reason = "Beginning initial module prerequisites."

        target_concept = target_cand["concept"]
        target_score = target_cand["mastery"]

        # Check recent attempts on this specific concept to calibrate difficulty
        concept_attempts = db.query(Attempt).join(Question).filter(
            Attempt.student_id == student_id,
            Question.concept_id == target_concept.id
        ).order_by(Attempt.created_at.desc()).limit(3).all()

        consecutive_wrong = sum(1 for a in concept_attempts if not a.is_correct)
        last_att = concept_attempts[0] if concept_attempts else None

        # Difficulty calibration:
        # If repeated wrong (>= 2): force EASY and provide remedial focus
        if consecutive_wrong >= 2:
            preferred_diff = "EASY"
            reason += " Repeated mistakes detected; providing foundational question with pedagogical guidance."
        elif last_att and last_att.is_correct and last_att.time_taken and last_att.time_taken < 30.0:
            # Fast + Correct -> promote difficulty
            preferred_diff = "HARD" if target_score >= 50.0 else "MEDIUM"
            reason += " Strong fast performance on previous question; advancing to higher difficulty."
        elif last_att and last_att.is_correct and last_att.time_taken and last_att.time_taken >= 60.0:
            # Slow + Correct -> maintain steady difficulty
            preferred_diff = "MEDIUM" if target_score >= 40.0 else "EASY"
            reason += " Correct but deliberate response; reinforcing current competency level."
        elif target_score < 40.0:
            preferred_diff = "EASY"
        elif target_score < 70.0:
            preferred_diff = "MEDIUM"
        else:
            preferred_diff = "HARD"

        # Fetch candidate questions for the target concept
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

        return {
            "concept": target_concept.name,
            "concept_id": target_concept.id,
            "topic_id": target_concept.module_id,
            "topic_name": target_concept.module.title if target_concept.module else "",
            "current_mastery": target_score,
            "status": target_cand["status"],
            "reason": reason,
            "concept_explanation": target_concept.explanation,
            "concept_code_snippet": target_concept.code_snippet,
            "question": {
                "id": selected_q.id,
                "concept_id": selected_q.concept_id,
                "topic_id": selected_q.topic_id,
                "concept_name": target_concept.name,
                "question_text": selected_q.question_text,
                "question_type": selected_q.question_type,
                "difficulty": selected_q.difficulty,
                "language": selected_q.language,
                "code_snippet": selected_q.code_snippet,
                "options": selected_q.options
            }
        }


    @classmethod
    def get_learning_path(cls, db: Session, student_id: int, course_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Computes the student's adaptive learning path overview as specified in Section 5.
        """
        query = db.query(Concept).order_by(Concept.order_index.asc())
        if course_id:
            query = query.join(Concept.module).filter(Concept.module.has(course_id=course_id))
        else:
            first_course = db.query(Course).order_by(Course.id.asc()).first()
            if first_course:
                query = query.join(Concept.module).filter(Concept.module.has(course_id=first_course.id))

        all_concepts = query.all()
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
        next_act = cls.get_next_question(db, student_id, course_id=course_id)
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
            "concepts": concepts_data,
            "path": concepts_data
        }
