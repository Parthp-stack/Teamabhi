from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from backend.models.course import Course
from backend.models.concept import Concept
from backend.models.question import Question, Attempt
from backend.models.mastery import StudentMastery
from backend.models.assessment_attempt import AssessmentAttempt, AssessmentWarning, QuestionAttempt
from backend.models.integrity import IntegrityEvent
from backend.models.coding import CodingSubmission
from backend.services.mastery_service import MasteryService
from backend.services.mcq_validation_service import MCQValidationService

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
        concept_id: Optional[int] = None,
        assessment_id: Optional[int] = None,
        attempt_id: Optional[int] = None,
        previous_concept: Optional[str] = None,
        last_was_correct: Optional[bool] = None,
        last_difficulty: Optional[str] = None,
        consecutive_wrong: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Selects the next adaptive question based on:
        1. Targeted topic/concept if specified
        2. Student's weakest eligible prerequisite or active weak concept
        3. Prior performance (wrong answer -> retry concept; repeated wrong -> simpler question; fast correct -> higher difficulty)
        4. Strict MCQ validation (no malformed or ambiguous questions enter active assessment)
        5. Session history & questions already shown in this attempt (prevents repeats)
        """
        query = db.query(Concept).order_by(Concept.order_index.asc())
        if concept_id:
            query = query.filter(Concept.id == concept_id)
        elif previous_concept:
            query = query.filter(Concept.name.ilike(f"%{previous_concept}%"))
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
            eligible = prereq_eval["eligible"] if not (concept_id or module_id or previous_concept) else True
            status = MasteryService.get_concept_status(score, eligible)

            concept_candidates.append({
                "concept": c,
                "mastery": score,
                "eligible": eligible,
                "blocking": prereq_eval["blocking_prereqs"],
                "status": status
            })

        # Track questions already shown in this attempt / session to prevent repeats
        session_attempted_ids = set()
        last_qa = None
        consecutive_wrong_count = consecutive_wrong if consecutive_wrong is not None else 0
        recent_concept_id = None
        recent_wrong = False
        recent_correct = False

        if last_was_correct is not None:
            recent_correct = last_was_correct
            recent_wrong = (not last_was_correct)

        if attempt_id:
            qa_rows = db.query(QuestionAttempt).filter(
                QuestionAttempt.attempt_id == attempt_id
            ).order_by(QuestionAttempt.question_number.desc()).all()
            for qa_item in qa_rows:
                session_attempted_ids.add(qa_item.question_id)
            if qa_rows:
                last_qa = qa_rows[0]
                recent_concept_id = last_qa.question.concept_id if last_qa.question else None
                if last_was_correct is None:
                    recent_wrong = (last_qa.is_correct is False)
                    recent_correct = (last_qa.is_correct is True)
                if recent_concept_id and consecutive_wrong is None:
                    consecutive_wrong_count = sum(1 for q_att in qa_rows if q_att.question and q_att.question.concept_id == recent_concept_id and q_att.is_correct is False)

        if not last_qa and last_was_correct is None:
            recent_attempt_query = db.query(Attempt).filter(Attempt.student_id == student_id)
            if assessment_id:
                recent_attempt_query = recent_attempt_query.filter(Attempt.assessment_id == assessment_id)
            recent_attempt = recent_attempt_query.order_by(Attempt.created_at.desc()).first()
            if recent_attempt and recent_attempt.question:
                recent_concept_id = recent_attempt.question.concept_id
                recent_wrong = (recent_attempt.is_correct is False)
                recent_correct = (recent_attempt.is_correct is True)

        # Target concept selection:
        target_cand = None
        if recent_wrong and recent_concept_id:
            for cand in concept_candidates:
                if cand["concept"].id == recent_concept_id:
                    target_cand = cand
                    reason = f"Targeting reinforcement for '{cand['concept'].name}' after recent incorrect answer."
                    break

        if not target_cand:
            unmastered_eligible = [
                cand for cand in concept_candidates
                if cand["eligible"] and cand["mastery"] < MASTERY_THRESHOLD
            ]
            if unmastered_eligible:
                target_cand = min(unmastered_eligible, key=lambda x: x["mastery"])
                reason = f"Prioritizing weakest eligible concept ({target_cand['concept'].name}: {target_cand['mastery']:.0f}% mastery)."
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

        # Difficulty calibration:
        is_remedial = (consecutive_wrong_count >= 2)
        if is_remedial:
            preferred_diff = "EASY"
            reason += " Repeated mistakes detected; providing foundational question with pedagogical guidance."
        elif recent_correct and (last_difficulty == "EASY" or target_score >= 50.0):
            preferred_diff = "HARD" if target_score >= 70.0 else "MEDIUM"
            reason += " Strong performance on previous question; advancing difficulty."
        elif target_score < 40.0:
            preferred_diff = "EASY"
        elif target_score < 70.0:
            preferred_diff = "MEDIUM"
        else:
            preferred_diff = "HARD"

        # Fetch candidate questions for target concept
        answered_correct_ids = [
            a.question_id for a in db.query(Attempt.question_id).filter(
                Attempt.student_id == student_id,
                Attempt.is_correct == True
            ).all()
        ]

        if assessment_id and not attempt_id:
            session_attempt_rows = db.query(Attempt.question_id).filter(
                Attempt.student_id == student_id,
                Attempt.assessment_id == assessment_id
            ).all()
            for r in session_attempt_rows:
                session_attempted_ids.add(r[0])


        available_questions = db.query(Question).filter(
            Question.concept_id == target_concept.id
        ).all()

        # REQUIREMENT 1: Filter out any invalid MCQs before making them available
        valid_questions = [
            q for q in available_questions
            if q.question_type != "MCQ" or MCQValidationService.is_mcq_valid(q)
        ]

        if not valid_questions:
            return {
                "concept": target_concept.name,
                "concept_id": target_concept.id,
                "reason": reason,
                "question": None,
                "message": f"No valid questions currently available for {target_concept.name}."
            }

        # REQUIREMENT 2: Select next question based on correctness, current difficulty, and avoid repeating questions
        # 1. Unattempted in this session + preferred difficulty
        pool = [q for q in valid_questions if q.id not in session_attempted_ids and q.id not in answered_correct_ids and q.difficulty == preferred_diff]
        # 2. Unattempted in this session + any difficulty
        if not pool:
            pool = [q for q in valid_questions if q.id not in session_attempted_ids and q.id not in answered_correct_ids]
        # 3. Any unattempted in this session
        if not pool:
            pool = [q for q in valid_questions if q.id not in session_attempted_ids]
        # 4. Fallback: question matching preferred difficulty
        if not pool:
            pool = [q for q in valid_questions if q.difficulty == preferred_diff]
        # 5. Last resort fallback to any valid question
        if not pool:
            pool = valid_questions

        selected_q = pool[0]

        return {
            "concept": target_concept.name,
            "concept_id": target_concept.id,
            "topic_id": target_concept.module_id,
            "topic_name": target_concept.module.title if target_concept.module else "",
            "current_mastery": target_score,
            "status": target_cand["status"],
            "reason": reason,
            "is_remedial": is_remedial,
            "consecutive_wrong": consecutive_wrong,
            "calibrated_difficulty": preferred_diff,
            "assessment_id": assessment_id,
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

    @classmethod
    def analyze_previous_attempts(
        cls,
        db: Session,
        student_id: int,
        course_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Requirement 11: PREVIOUS ATTEMPT -> ADAPTIVE LEARNING
        Analyzes student's previous attempts across:
        - Weak concepts (< 50% mastery or low accuracy)
        - Strong concepts (>= 75% mastery)
        - Incorrect answers count
        - Difficulty performance (EASY, MEDIUM, HARD accuracy)
        - Coding performance (passed vs failed submissions)
        - Integrity events evaluated separately
        IMPORTANT: Academic knowledge weakness and Integrity events are maintained as separate dimensions!
        """
        concepts_query = db.query(Concept).order_by(Concept.order_index.asc())
        if course_id:
            concepts_query = concepts_query.join(Concept.module).filter(Concept.module.has(course_id=course_id))
        all_concepts = concepts_query.all()

        mastery_map = cls.get_student_mastery_map(db, student_id)
        attempts = db.query(Attempt).filter(Attempt.student_id == student_id).all()
        q_attempts = db.query(QuestionAttempt).filter(QuestionAttempt.student_id == student_id).all()
        coding_subs = db.query(CodingSubmission).filter(CodingSubmission.student_id == student_id).all()

        weak_concepts = []
        strong_concepts = []
        for c in all_concepts:
            score = mastery_map.get(c.id, 0.0)
            if score >= 75.0:
                strong_concepts.append({"concept_id": c.id, "concept_name": c.name, "mastery": score})
            elif score < 50.0:
                weak_concepts.append({"concept_id": c.id, "concept_name": c.name, "mastery": score})

        diff_stats = {
            "EASY": {"total": 0, "correct": 0, "accuracy": 0.0},
            "MEDIUM": {"total": 0, "correct": 0, "accuracy": 0.0},
            "HARD": {"total": 0, "correct": 0, "accuracy": 0.0}
        }
        total_incorrect = 0
        for a in attempts:
            diff = (a.question.difficulty if a.question and a.question.difficulty else "MEDIUM").upper()
            if diff in diff_stats:
                diff_stats[diff]["total"] += 1
                if a.is_correct:
                    diff_stats[diff]["correct"] += 1
                else:
                    total_incorrect += 1

        for d in diff_stats.values():
            d["accuracy"] = round((d["correct"] / d["total"] * 100), 1) if d["total"] > 0 else 0.0

        coding_passed = sum(1 for s in coding_subs if s.status == "PASSED")
        coding_failed = len(coding_subs) - coding_passed

        integ_events = db.query(IntegrityEvent).filter(IntegrityEvent.student_id == student_id).all()
        asst_attempts = db.query(AssessmentAttempt).filter(AssessmentAttempt.student_id == student_id).all()

        total_integ = len(integ_events)
        total_warnings = sum(1 for e in integ_events if e.warning is not None and len(e.warning.strip()) > 0)
        max_risk_level = "NORMAL"
        for att in asst_attempts:
            if att.risk_level == "HIGH_RISK":
                max_risk_level = "HIGH"
                break
            elif att.risk_level == "MEDIUM_RISK" and max_risk_level != "HIGH":
                max_risk_level = "MEDIUM"
            elif att.risk_level == "LOW_RISK" and max_risk_level == "NORMAL":
                max_risk_level = "LOW"

        return {
            "student_id": student_id,
            "separation_guarantee": True,
            "academic_performance": {
                "weak_concepts": weak_concepts,
                "strong_concepts": strong_concepts,
                "incorrect_answers_count": total_incorrect,
                "total_questions_attempted": len(attempts) + len(q_attempts),
                "difficulty_performance": diff_stats,
                "coding_submissions": {
                    "total": len(coding_subs),
                    "passed": coding_passed,
                    "failed": coding_failed
                }
            },
            "integrity_performance": {
                "total_integrity_events": total_integ,
                "warnings_count": total_warnings,
                "risk_level": max_risk_level,
                "note": "Integrity events are tracked independently and do not degrade academic mastery."
            }
        }

