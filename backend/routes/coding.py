from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models.user import User
from backend.models.coding import CodingProblem, TestCase, CodingSubmission
from backend.models.explanation import ExplanationQuestion
from backend.schemas.coding import (
    CodingProblemResponse,
    TestCaseVisible,
    CodeRunRequest,
    CodeRunResponse,
    CodeSubmitRequest,
    CodeSubmitResponse,
    TestResultDetail
)
from backend.utils.security import get_current_user
from backend.services.sandbox_service import SandboxService
from backend.services.ai_service import AIService
from backend.services.integrity_service import IntegrityService

router = APIRouter(prefix="/coding", tags=["Coding Assessment & Sandbox"])

@router.get("/problems", response_model=List[CodingProblemResponse])
def get_coding_problems(db: Session = Depends(get_db)):
    problems = db.query(CodingProblem).all()
    results = []
    for p in problems:
        # Filter for visible test cases only!
        visible = [
            TestCaseVisible(id=tc.id, input=tc.input, expected_output=tc.expected_output)
            for tc in p.test_cases if not tc.is_hidden
        ]
        results.append(CodingProblemResponse(
            id=p.id,
            title=p.title,
            description=p.description,
            difficulty=p.difficulty,
            allowed_languages=p.allowed_languages,
            time_limit=p.time_limit,
            memory_limit=p.memory_limit,
            visible_test_cases=visible
        ))
    return results

@router.get("/problems/{problem_id}", response_model=CodingProblemResponse)
def get_coding_problem(problem_id: int, db: Session = Depends(get_db)):
    p = db.query(CodingProblem).filter(CodingProblem.id == problem_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Coding problem not found")

    # STRICT SECURITY: Never return hidden test cases to the frontend!
    visible = [
        TestCaseVisible(id=tc.id, input=tc.input, expected_output=tc.expected_output)
        for tc in p.test_cases if not tc.is_hidden
    ]

    return CodingProblemResponse(
        id=p.id,
        title=p.title,
        description=p.description,
        difficulty=p.difficulty,
        allowed_languages=p.allowed_languages,
        time_limit=p.time_limit,
        memory_limit=p.memory_limit,
        visible_test_cases=visible
    )

@router.post("/run", response_model=CodeRunResponse)
def run_code_visible_tests(
    req: CodeRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    problem = db.query(CodingProblem).filter(CodingProblem.id == req.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Run ONLY against visible test cases
    visible_tests = [tc for tc in problem.test_cases if not tc.is_hidden]
    if not visible_tests:
        # If no explicit test cases, run empty input
        res = SandboxService.execute_test_case(req.language, req.source_code, "", problem.time_limit)
        return CodeRunResponse(
            status=res["status"],
            stdout=res["stdout"],
            stderr=res["stderr"],
            execution_time=res["execution_time"],
            memory_used=res["memory_used"],
            all_passed=(res["status"] == "PASSED"),
            visible_test_results=[]
        )

    test_results: List[TestResultDetail] = []
    overall_status = "PASSED"
    total_time = 0.0
    max_mem = 0.0

    for tc in visible_tests:
        exec_res = SandboxService.execute_test_case(
            language=req.language,
            source_code=req.source_code,
            stdin_data=tc.input,
            timeout=problem.time_limit
        )

        total_time += exec_res["execution_time"]
        max_mem = max(max_mem, exec_res["memory_used"])

        # Check output correctness (normalized strip)
        actual_out_clean = exec_res["stdout"].strip().replace("\r\n", "\n")
        expected_out_clean = tc.expected_output.strip().replace("\r\n", "\n")

        passed = (exec_res["status"] == "PASSED") and (actual_out_clean == expected_out_clean)

        if exec_res["status"] != "PASSED":
            overall_status = exec_res["status"]
        elif not passed and overall_status == "PASSED":
            overall_status = "FAILED"

        test_results.append(TestResultDetail(
            test_case_id=tc.id,
            passed=passed,
            input=tc.input,
            expected_output=tc.expected_output,
            actual_output=exec_res["stdout"],
            execution_time=exec_res["execution_time"],
            error_message=exec_res["stderr"] if exec_res["stderr"] else None,
            is_hidden=False
        ))

    all_passed = all(t.passed for t in test_results)

    return CodeRunResponse(
        status=overall_status,
        stdout=test_results[0].actual_output if test_results else "",
        stderr=test_results[0].error_message if test_results else "",
        execution_time=round(total_time, 3),
        memory_used=round(max_mem, 1),
        all_passed=all_passed,
        visible_test_results=test_results
    )

@router.post("/submit", response_model=CodeSubmitResponse)
async def submit_code(
    req: CodeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    problem = db.query(CodingProblem).filter(CodingProblem.id == req.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    all_tests = problem.test_cases
    passed_count = 0
    total_tests = len(all_tests)
    overall_status = "PASSED"
    total_time = 0.0
    max_mem = 0.0

    for tc in all_tests:
        exec_res = SandboxService.execute_test_case(
            language=req.language,
            source_code=req.source_code,
            stdin_data=tc.input,
            timeout=problem.time_limit
        )

        total_time += exec_res["execution_time"]
        max_mem = max(max_mem, exec_res["memory_used"])

        actual_out_clean = exec_res["stdout"].strip().replace("\r\n", "\n")
        expected_out_clean = tc.expected_output.strip().replace("\r\n", "\n")

        passed = (exec_res["status"] == "PASSED") and (actual_out_clean == expected_out_clean)

        if passed:
            passed_count += 1
        elif overall_status == "PASSED":
            overall_status = exec_res["status"] if exec_res["status"] != "PASSED" else "FAILED"

    score = round((passed_count / total_tests * 100.0), 1) if total_tests > 0 else 100.0

    # Save submission
    submission = CodingSubmission(
        student_id=current_user.id,
        problem_id=problem.id,
        language=req.language,
        source_code=req.source_code,
        status=overall_status,
        score=score,
        execution_time=round(total_time, 3),
        memory_used=round(max_mem, 1)
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Trigger Explain Your Code question generation via AI
    viva_questions = await AIService.generate_code_questions(
        source_code=req.source_code,
        problem_title=problem.title,
        language=req.language
    )

    for q_data in viva_questions:
        q_obj = ExplanationQuestion(
            submission_id=submission.id,
            question=q_data["question"],
            expected_concept=q_data.get("expected_concept", "Implementation Logic")
        )
        db.add(q_obj)
    db.commit()

    # If session_id was passed, analyze integrity signals for human review
    if req.session_id:
        IntegrityService.analyze_session_events(db, req.session_id)

    msg = f"Submission complete. Passed {passed_count}/{total_tests} test cases."
    if overall_status == "PASSED":
        msg += " Excellent! Please proceed to the 'Explain Your Code' section."
    else:
        msg += f" Result: {overall_status}."

    return CodeSubmitResponse(
        submission_id=submission.id,
        status=overall_status,
        score=score,
        passed_tests=passed_count,
        total_tests=total_tests,
        execution_time=round(total_time, 3),
        memory_used=round(max_mem, 1),
        message=msg
    )
