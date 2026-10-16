import json
import re
import httpx
from typing import Dict, Any, List, Optional
from backend.config import settings

class AIService:
    @staticmethod
    def _get_headers() -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": settings.FRONTEND_URL,
            "X-Title": "Adaptive Learning & Assessment Portal"
        }
        if settings.OPENROUTER_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OPENROUTER_API_KEY}"
        return headers

    @classmethod
    async def _call_openrouter(cls, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Optional[str]:
        """Call OpenRouter with Nemotron model with timeout and error handling."""
        if not settings.OPENROUTER_API_KEY:
            return None

        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 1200
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(url, json=payload, headers=cls._get_headers())
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return content
                else:
                    print(f"[AIService] OpenRouter call failed ({response.status_code}): {response.text}")
                    return None
        except Exception as e:
            print(f"[AIService] Error communicating with OpenRouter: {e}")
            return None

    @classmethod
    async def generate_question(
        cls,
        concept: str,
        difficulty: str = "MEDIUM",
        question_type: str = "MCQ"
    ) -> Dict[str, Any]:
        """
        Generate a pedagogical question using AI based on concept, difficulty, and question type.
        """
        system_prompt = (
            "You are an expert computer science professor. Generate a high quality question on the specified topic. "
            "Output strictly in valid JSON format: "
            "{\"question_text\": \"...\", \"question_type\": \"...\", \"difficulty\": \"...\", \"options\": [\"...\", \"...\"], \"correct_answer\": \"...\", \"explanation\": \"...\"}"
        )
        user_prompt = (
            f"Concept: {concept}\n"
            f"Difficulty: {difficulty}\n"
            f"Question Type: {question_type}\n"
            "Generate the question strictly as JSON."
        )

        raw = await cls._call_openrouter(system_prompt, user_prompt)
        if raw:
            try:
                clean = re.sub(r"```json\s*", "", raw)
                clean = re.sub(r"```\s*", "", clean).strip()
                parsed = json.loads(clean)
                if "question_text" in parsed and "correct_answer" in parsed:
                    return parsed
            except Exception as e:
                print(f"[AIService] Failed to parse generated question JSON: {e}")

        # Deterministic fallback
        return cls._fallback_generate_question(concept, difficulty, question_type)

    @classmethod
    async def explain_concept(
        cls,
        concept: str,
        student_mastery: float = 0.0,
        difficulty: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Produce a tailored pedagogical explanation, code snippet, common mistake, and quick check.
        """
        system_prompt = (
            "You are an empathetic, expert tutor in Object-Oriented Programming. "
            "Explain the requested concept tailored to a student's current proficiency level. "
            "Output strictly in valid JSON: "
            "{\"concept\": \"...\", \"explanation\": \"...\", \"example\": \"...\", \"common_mistake\": \"...\", \"practice_question\": \"...\"}"
        )
        user_prompt = (
            f"Concept: {concept}\n"
            f"Student Mastery Level: {student_mastery}%\n"
            f"Target Difficulty: {difficulty}\n"
            "Provide explanation, code example, common pitfall, and a quick check question strictly in JSON."
        )

        raw = await cls._call_openrouter(system_prompt, user_prompt)
        if raw:
            try:
                clean = re.sub(r"```json\s*", "", raw)
                clean = re.sub(r"```\s*", "", clean).strip()
                parsed = json.loads(clean)
                if "explanation" in parsed:
                    return parsed
            except Exception as e:
                print(f"[AIService] Failed to parse explain_concept JSON: {e}")

        # Deterministic fallback
        return {
            "concept": concept,
            "explanation": f"{concept} is a foundational pillar of Object-Oriented Programming that establishes reliable software architecture and abstraction boundaries.",
            "example": f"# Python example of {concept}\nclass Example:\n    def __init__(self, value):\n        self.value = value",
            "common_mistake": f"Failing to respect {concept} invariants or confusing interface contracts with concrete implementation details.",
            "practice_question": f"How does {concept} help improve code maintainability and decouple dependencies?"
        }

    @classmethod
    async def generate_practice(
        cls,
        concept: str,
        student_weak_areas: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate additional targeted practice questions for a weak concept.
        """
        weak_str = ", ".join(student_weak_areas) if student_weak_areas else "Core conceptual fundamentals"
        system_prompt = (
            "You are a computer science instructor generating 2 practice questions for a student struggling with specific concepts. "
            "Output strictly a JSON list of objects: [{\"question_text\": \"...\", \"options\": [\"...\"], \"correct_answer\": \"...\", \"explanation\": \"...\"}]"
        )
        user_prompt = f"Concept: {concept}\nWeak Areas: {weak_str}\nGenerate 2 questions."

        raw = await cls._call_openrouter(system_prompt, user_prompt)
        if raw:
            try:
                clean = re.sub(r"```json\s*", "", raw)
                clean = re.sub(r"```\s*", "", clean).strip()
                parsed = json.loads(clean)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
            except Exception as e:
                print(f"[AIService] Practice generation parse error: {e}")

        # Deterministic fallback
        return [
            {
                "question_text": f"What is the main design goal of applying {concept} in scalable software?",
                "options": ["Improving modularity and testability", "Decreasing RAM clock speed", "Encrypting database records", "Eliminating all classes"],
                "correct_answer": "Improving modularity and testability",
                "explanation": f"{concept} promotes modularity and separation of concerns."
            },
            {
                "question_text": f"In {concept}, which invariant is critical to maintain across runtime state mutations?",
                "options": ["Internal consistency and encapsulation boundaries", "Hardcoded absolute file paths", "Zero memory allocation", "Manual thread dispatch"],
                "correct_answer": "Internal consistency and encapsulation boundaries",
                "explanation": "Preserving invariants ensures objects never reach an invalid or corrupted state."
            }
        ]

    @classmethod
    def _fallback_generate_question(cls, concept: str, difficulty: str, question_type: str) -> Dict[str, Any]:
        """Deterministic question fallback for offline testing or without API key."""
        if question_type == "TRUE_FALSE":
            return {
                "question_text": f"In {concept}, can state mutation be performed safely when encapsulation invariants are respected?",
                "question_type": "TRUE_FALSE",
                "difficulty": difficulty,
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation": f"Encapsulation guarantees that mutations preserve valid {concept} state."
            }
        elif question_type == "SHORT_ANSWER":
            return {
                "question_text": f"Name the key principle in Object-Oriented design that {concept} reinforces.",
                "question_type": "SHORT_ANSWER",
                "difficulty": difficulty,
                "options": ["encapsulation", "abstraction", "modularity"],
                "correct_answer": "abstraction",
                "explanation": f"{concept} provides structured abstraction over implementation mechanics."
            }
        else:
            return {
                "question_text": f"What is the primary architectural benefit of utilizing {concept} in system design?",
                "question_type": "MCQ",
                "difficulty": difficulty,
                "options": [
                    f"Decoupling interface contracts and reinforcing {concept} modularity",
                    "Forcing the application to execute only in single-threaded mode",
                    "Eliminating the need for unit testing",
                    "Disabling hardware garbage collection"
                ],
                "correct_answer": f"Decoupling interface contracts and reinforcing {concept} modularity",
                "explanation": f"{concept} isolates internal mechanics and establishes robust contracts."
            }
