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
            difficulty=p.difficulty or "MEDIUM",
            allowed_languages=p.allowed_languages or ["python", "cpp", "c", "java", "javascript"],
            time_limit=float(p.time_limit or 2.0),
            memory_limit=int(p.memory_limit or 128),
            visible_test_cases=visible,
            problem_statement=p.problem_statement or p.description,
            input_format=p.input_format,
            output_format=p.output_format,
            constraints=p.constraints,
            examples=p.examples,
            expected_solution_concept=p.expected_solution_concept,
            topic=p.topic
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
        difficulty=p.difficulty or "MEDIUM",
        allowed_languages=p.allowed_languages or ["python", "cpp", "c", "java", "javascript"],
        time_limit=float(p.time_limit or 2.0),
        memory_limit=int(p.memory_limit or 128),
        visible_test_cases=visible,
        problem_statement=p.problem_statement or p.description,
        input_format=p.input_format,
        output_format=p.output_format,
        constraints=p.constraints,
        examples=p.examples,
        expected_solution_concept=p.expected_solution_concept,
        topic=p.topic
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

    for idx, q_data in enumerate(viva_questions, 1):
        q_text = q_data.get("question") or q_data.get("question_text", "Explain your implementation logic and architectural design.")
        q_obj = ExplanationQuestion(
            submission_id=submission.id,
            question_index=idx,
            question_text=q_text,
            question=q_text,
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

import re
from pydantic import BaseModel

class DevOpsLabVerifyRequest(BaseModel):
    task_id: str
    solution_code: str

@router.post("/devops-lab/verify")
def verify_devops_lab_task(
    req: DevOpsLabVerifyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Safely verifies browser-based DevOps laboratory assignments without running arbitrary
    commands directly on host. Uses syntax and directive structure validation.
    """
    task_id = req.task_id
    code = req.solution_code
    checks = []

    if task_id == "dockerfile_basic":
        has_from = bool(re.search(r"^\s*FROM\s+python:[\w\.-]+", code, re.M | re.I))
        checks.append({
            "check": "Base image uses official Python image (FROM python:...)",
            "passed": has_from,
            "detail": "Found valid FROM python instruction" if has_from else "Missing or invalid FROM python instruction"
        })

        has_workdir = bool(re.search(r"^\s*WORKDIR\s+/\w+", code, re.M | re.I))
        checks.append({
            "check": "Sets working directory (WORKDIR /...)",
            "passed": has_workdir,
            "detail": "WORKDIR defined" if has_workdir else "Missing WORKDIR instruction"
        })

        has_req_copy = bool(re.search(r"^\s*COPY\s+requirements\.txt", code, re.M | re.I))
        has_pip = bool(re.search(r"^\s*RUN\s+pip\s+install", code, re.M | re.I))
        checks.append({
            "check": "Copies dependencies and executes pip install",
            "passed": has_req_copy and has_pip,
            "detail": "Dependencies properly layered" if (has_req_copy and has_pip) else "Missing COPY requirements.txt or RUN pip install"
        })

        has_code_copy = bool(re.search(r"^\s*COPY\s+(\.|\w+)\s+(\.|\w+)", code, re.M | re.I))
        checks.append({
            "check": "Copies application source code",
            "passed": has_code_copy,
            "detail": "Source code copied" if has_code_copy else "Missing COPY instruction"
        })

        has_expose = bool(re.search(r"^\s*EXPOSE\s+8000", code, re.M | re.I))
        checks.append({
            "check": "Exposes application port 8000 (EXPOSE 8000)",
            "passed": has_expose,
            "detail": "Port 8000 exposed" if has_expose else "Missing EXPOSE 8000 instruction"
        })

        has_cmd = bool(re.search(r"^\s*CMD\s+\[.*uvicorn.*\]", code, re.M | re.I))
        checks.append({
            "check": "Defines default executable entrypoint (CMD uvicorn)",
            "passed": has_cmd,
            "detail": "CMD entrypoint configured" if has_cmd else "Missing CMD with uvicorn start"
        })

    elif task_id == "dockerfile_multistage":
        from_matches = re.findall(r"^\s*FROM\s+.*", code, re.M | re.I)
        has_multistage = len(from_matches) >= 2
        checks.append({
            "check": "Implements multi-stage build (multiple FROM statements)",
            "passed": has_multistage,
            "detail": f"Found {len(from_matches)} build stages" if has_multistage else "Requires at least 2 FROM statements for multi-stage build"
        })

        has_env = bool(re.search(r"^\s*ENV\s+PYTHONUNBUFFERED\s*=\s*1|ENV\s+PYTHONDONTWRITEBYTECODE\s*=\s*1", code, re.M | re.I))
        checks.append({
            "check": "Configures Python environment (PYTHONUNBUFFERED=1)",
            "passed": has_env,
            "detail": "ENV directive present" if has_env else "Missing standard ENV flags"
        })

        has_user = bool(re.search(r"^\s*USER\s+\w+|RUN\s+useradd|adduser", code, re.M | re.I))
        checks.append({
            "check": "Security hardening: Non-root user configuration (USER appuser)",
            "passed": has_user,
            "detail": "Non-root execution configured" if has_user else "Missing non-root user instruction"
        })

        has_expose = bool(re.search(r"^\s*EXPOSE\s+\d+", code, re.M | re.I))
        checks.append({
            "check": "Exposes network port",
            "passed": has_expose,
            "detail": "Port exposed" if has_expose else "Missing EXPOSE instruction"
        })

    elif task_id == "ci_workflow":
        has_triggers = bool(re.search(r"on:\s*\[?.*push.*\]?", code, re.I))
        checks.append({
            "check": "Configures workflow trigger (on: [push, pull_request])",
            "passed": has_triggers,
            "detail": "Triggers defined" if has_triggers else "Missing on: triggers"
        })

        has_checkout = bool(re.search(r"actions/checkout@", code, re.I))
        checks.append({
            "check": "Includes repository checkout step (actions/checkout)",
            "passed": has_checkout,
            "detail": "Checkout step present" if has_checkout else "Missing checkout"
        })

        has_python_setup = bool(re.search(r"actions/setup-python@", code, re.I))
        checks.append({
            "check": "Sets up Python runtime (actions/setup-python)",
            "passed": has_python_setup,
            "detail": "Python setup configured" if has_python_setup else "Missing setup"
        })

        has_test_step = bool(re.search(r"pytest|python -m pytest", code, re.I))
        checks.append({
            "check": "Executes automated tests step (pytest)",
            "passed": has_test_step,
            "detail": "Test execution step found" if has_test_step else "Missing test command"
        })
    else:
        checks.append({
            "check": "Known task identifier",
            "passed": False,
            "detail": f"Unknown task_id: {task_id}"
        })

    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round((passed_count / total_checks * 100), 1) if total_checks > 0 else 0.0
    all_passed = (passed_count == total_checks)

    return {
        "task_id": task_id,
        "score": score,
        "passed_checks": passed_count,
        "total_checks": total_checks,
        "all_passed": all_passed,
        "checks": checks,
        "feedback": "All DevOps verification criteria satisfied! Excellent container configuration." if all_passed else f"Verified {passed_count}/{total_checks} criteria. Please resolve remaining items."
    }
