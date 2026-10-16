import json
import re
import logging
from typing import Dict, Any, List, Optional
from backend.services.ai_service import AIService

logger = logging.getLogger("mcq_validation")

class MCQValidationService:
    VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}

    @classmethod
    def validate_mcq_deterministic(cls, mcq_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic backend validation for Multiple Choice Questions.
        Detects:
        - Malformed data
        - Missing or blank question text
        - Missing or invalid options (< 2 options or non-list)
        - Duplicate options
        - Missing correct answer
        - Correct answer not matching any option
        - Multiple matching options
        - Missing explanation
        - Invalid difficulty
        """
        errors = []

        # 1. Check question text
        q_text = str(mcq_data.get("question_text") or mcq_data.get("question") or "").strip()
        if not q_text:
            errors.append("Question text is missing or empty.")
        elif len(q_text) < 10:
            errors.append("Question text is too short or ambiguous (minimum 10 characters required).")

        # 2. Check options
        options = mcq_data.get("options")
        if not isinstance(options, list):
            errors.append("Options must be a list of choices.")
            clean_options = []
        else:
            clean_options = [str(opt).strip() for opt in options if opt is not None]
            if len(clean_options) < 2:
                errors.append("At least two options are required for an MCQ.")

            # Check for duplicate options
            seen_options = set()
            duplicates = set()
            for opt in clean_options:
                opt_lower = opt.lower()
                if opt_lower in seen_options:
                    duplicates.add(opt)
                seen_options.add(opt_lower)
            if duplicates:
                errors.append(f"Duplicate options detected: {list(duplicates)}")

        # 3. Check correct answer
        correct_answer = str(mcq_data.get("correct_answer") or mcq_data.get("correct_option") or "").strip()
        if not correct_answer:
            errors.append("Correct answer is missing.")
        else:
            # Match against options
            matching_options = [opt for opt in clean_options if opt.lower() == correct_answer.lower()]
            if not matching_options:
                # Also check single letter keys like 'A', 'B', 'C', 'D'
                letter_match = None
                if len(correct_answer) == 1 and correct_answer.upper() in "ABCD":
                    idx = ord(correct_answer.upper()) - ord('A')
                    if 0 <= idx < len(clean_options):
                        letter_match = clean_options[idx]
                if letter_match:
                    correct_answer = letter_match
                else:
                    errors.append(f"Correct answer '{correct_answer}' does not match any available option.")
            elif len(matching_options) > 1:
                errors.append("Multiple options match the designated correct answer.")

        # 4. Check difficulty
        difficulty = str(mcq_data.get("difficulty") or "MEDIUM").strip().upper()
        if difficulty not in cls.VALID_DIFFICULTIES:
            difficulty = "MEDIUM"

        # 5. Check explanation
        explanation = str(mcq_data.get("explanation") or "").strip()
        if not explanation:
            errors.append("Explanation is missing. A pedagogical rationale is required.")

        # 6. Check concept/topic
        concept = mcq_data.get("concept") or mcq_data.get("concept_name") or mcq_data.get("concept_id")
        if not concept:
            errors.append("Concept or topic assignment is required.")

        is_valid = len(errors) == 0
        return {
            "valid": is_valid,
            "correct_option": correct_answer if is_valid else None,
            "confidence": 1.0 if is_valid else 0.0,
            "reason": "MCQ passed all deterministic validation rules." if is_valid else "; ".join(errors),
            "errors": errors,
            "difficulty": difficulty,
            "concept": str(concept) if concept else "General",
            "validation_mode": "DETERMINISTIC"
        }

    @classmethod
    async def validate_mcq_with_ai(cls, mcq_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-assisted review of generated or candidate MCQs using OpenRouter.
        Verifies answer key correctness, absence of multiple correct choices,
        and pedagogical clarity.
        Gracefully falls back to deterministic validation if AI API is unavailable.
        """
        # First perform deterministic validation
        det_result = cls.validate_mcq_deterministic(mcq_data)
        if not det_result["valid"]:
            # If deterministic check fails, no need to ask AI; return invalid immediately
            return det_result

        # If deterministic passed, optionally verify with AI
        q_text = str(mcq_data.get("question_text") or mcq_data.get("question") or "")
        options = mcq_data.get("options", [])
        correct_answer = det_result["correct_option"]
        concept = det_result["concept"]
        difficulty = det_result["difficulty"]

        system_prompt = (
            "You are an expert Computer Science evaluator and psychometrician. "
            "Your job is to validate a Multiple Choice Question (MCQ). "
            "Check that: "
            "1. The question is unambiguous and technically correct. "
            "2. Exactly ONE option is factually correct. "
            "3. The designated correct answer is indeed the single right answer. "
            "4. There are no misleading or duplicate correct answers among the distractors. "
            "Return strictly valid JSON with this exact schema: "
            "{"
            "  \"valid\": true/false, "
            "  \"correct_option\": \"<the exact correct option text>\", "
            "  \"confidence\": <float between 0.0 and 1.0>, "
            "  \"reason\": \"<brief explanation of verdict>\", "
            "  \"difficulty\": \"EASY|MEDIUM|HARD\", "
            "  \"concept\": \"<concept name>\" "
            "}"
        )

        user_prompt = (
            f"Concept: {concept}\n"
            f"Difficulty: {difficulty}\n"
            f"Question: {q_text}\n"
            f"Options: {json.dumps(options)}\n"
            f"Designated Correct Answer: {correct_answer}\n"
            f"Explanation: {mcq_data.get('explanation', '')}\n\n"
            "Review this question and output the verdict strictly in JSON."
        )

        try:
            raw_ai = await AIService._call_openrouter(system_prompt, user_prompt, temperature=0.1)
            if raw_ai:
                clean = re.sub(r"```json\s*", "", raw_ai)
                clean = re.sub(r"```\s*", "", clean).strip()
                parsed = json.loads(clean)

                if isinstance(parsed, dict) and "valid" in parsed:
                    return {
                        "valid": bool(parsed.get("valid")),
                        "correct_option": str(parsed.get("correct_option") or correct_answer),
                        "confidence": float(parsed.get("confidence", 0.95)),
                        "reason": str(parsed.get("reason", "Validated by AI evaluator.")),
                        "difficulty": str(parsed.get("difficulty", difficulty)).upper(),
                        "concept": str(parsed.get("concept", concept)),
                        "validation_mode": "AI_ENHANCED"
                    }
        except Exception as e:
            logger.warning(f"[MCQValidationService] AI validation unavailable or timed out: {e}. Falling back to deterministic.")

        # Graceful fallback: return deterministic result
        det_result["validation_mode"] = "DETERMINISTIC_FALLBACK"
        return det_result

    @classmethod
    def is_mcq_valid(cls, question_obj: Any) -> bool:
        """
        Fast filter check to ensure only valid MCQs enter the active assessment.
        Accepts a Question ORM instance or dictionary.
        """
        if hasattr(question_obj, "question_text"):
            data = {
                "question_text": question_obj.question_text,
                "options": question_obj.options,
                "correct_answer": question_obj.correct_answer,
                "explanation": question_obj.explanation,
                "difficulty": question_obj.difficulty,
                "concept": question_obj.concept.name if getattr(question_obj, "concept", None) else "General"
            }
        elif isinstance(question_obj, dict):
            data = question_obj
        else:
            return False

        res = cls.validate_mcq_deterministic(data)
        return res["valid"]
