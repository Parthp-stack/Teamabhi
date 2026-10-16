from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TestCaseVisible(BaseModel):
    id: int
    input: str
    expected_output: str

    class Config:
        from_attributes = True

class CodingProblemResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    allowed_languages: List[str]
    time_limit: float
    memory_limit: int
    visible_test_cases: List[TestCaseVisible] = []
    
    # Comprehensive problem definition fields (Requirement 3)
    problem_statement: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    constraints: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None
    expected_solution_concept: Optional[str] = None
    topic: Optional[str] = None

    class Config:
        from_attributes = True

class TestResultDetail(BaseModel):
    test_case_id: int
    passed: bool
    input: str
    expected_output: str
    actual_output: Optional[str] = None
    execution_time: float
    error_message: Optional[str] = None
    is_hidden: bool = False

class CodeRunRequest(BaseModel):
    problem_id: int
    language: str
    source_code: str

class CodeRunResponse(BaseModel):
    status: str # PASSED, FAILED, COMPILE_ERROR, RUNTIME_ERROR, TIMEOUT, MEMORY_LIMIT, SECURITY_BLOCKED
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    execution_time: float
    memory_used: float
    all_passed: bool
    visible_test_results: List[TestResultDetail] = []

class CodeSubmitRequest(BaseModel):
    problem_id: int
    language: str
    source_code: str
    session_id: Optional[int] = None

class CodeSubmitResponse(BaseModel):
    submission_id: int
    status: str
    score: float
    passed_tests: int
    total_tests: int
    execution_time: float
    memory_used: float
    message: str
