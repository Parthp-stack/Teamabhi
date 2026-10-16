from backend.database import Base
from backend.models.user import User, UserRole, StudentProfile, TeacherProfile
from backend.models.course import Course, Module
from backend.models.concept import Concept, ConceptPrerequisite
from backend.models.question import Question, Attempt
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.coding import CodingProblem, TestCase, CodingSubmission
from backend.models.session import Session, SessionEvent, CodeRevision
from backend.models.integrity import IntegritySignal, IntegrityEvent
from backend.models.explanation import ExplanationQuestion, ExplanationAnswer
from backend.models.ai_evaluation import AIEvaluation
from backend.models.assessment_attempt import AssessmentAttempt, AssessmentWarning, QuestionAttempt, StudentConceptProgress

# Entity aliases for database and curriculum flexibility
Subject = Course
Topic = Module
CodingAttempt = CodingSubmission
CodingActivityEvent = SessionEvent


__all__ = [
    "Base",
    "User",
    "UserRole",
    "StudentProfile",
    "TeacherProfile",
    "Course",
    "Module",
    "Subject",
    "Topic",
    "Concept",
    "ConceptPrerequisite",
    "Question",
    "Attempt",
    "QuestionAttempt",
    "StudentMastery",
    "MasteryHistory",
    "CodingProblem",
    "TestCase",
    "CodingSubmission",
    "CodingAttempt",
    "Session",
    "SessionEvent",
    "CodingActivityEvent",
    "CodeRevision",
    "IntegritySignal",
    "IntegrityEvent",
    "ExplanationQuestion",
    "ExplanationAnswer",
    "AIEvaluation",
    "AssessmentAttempt",
    "AssessmentWarning",
    "StudentConceptProgress"
]


