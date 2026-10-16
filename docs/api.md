# API Documentation & Endpoint Reference

All endpoints are prefixed with `/api`. Authentication uses Bearer JWT tokens in the `Authorization` header.

## 1. Authentication (`/api/auth`)
- `POST /api/auth/register`: Register new user (`name`, `email`, `password`, `role`). Returns JWT token.
- `POST /api/auth/login`: Authenticate with `email` and `password`. Returns JWT token.
- `GET /api/auth/me`: Fetch current authenticated profile.

## 2. Courses & Concept Graph (`/api/courses`, `/api/concepts`)
- `GET /api/courses`: List all courses and modules.
- `GET /api/courses/{course_id}`: Get single course details.
- `GET /api/concepts/graph`: Returns React Flow nodes and edges with student mastery status (`MASTERED`, `LEARNING`, `WEAK`, `LOCKED`).
- `GET /api/concepts/{concept_id}`: Returns concept details, prerequisites, dependent topics, and recent performance.

## 3. Knowledge Tracing & Mastery (`/api/mastery`)
- `GET /api/mastery`: Get current student's overall mastery overview and concept list.
- `GET /api/mastery/{student_id}`: Get specific student's overview (Trainer only or self).
- `GET /api/mastery/{student_id}/history`: Chronological mastery log for charting knowledge growth.
- `POST /api/mastery/update`: Diagnostic or manual score update.

## 4. Adaptive Learning Engine (`/api/learning`)
- `GET /api/learning/next`: Calculates student's weakest eligible prerequisite and returns the optimal question + explainable rationale.
- `POST /api/learning/attempt`: Submits answer, runs Bayesian mastery update, records attempt, and returns delta feedback.
- `POST /api/learning/hint`: Requests AI hint for the current question without revealing the solution.

## 5. Coding Sandbox & Submissions (`/api/coding`, `/api/code`)
- `GET /api/coding/problems`: Returns all coding problems with visible test cases only.
- `GET /api/coding/problems/{problem_id}`: Returns specific problem. (Hidden test cases are omitted).
- `POST /api/coding/run`: Executes code against visible test cases in the secure sandbox.
- `POST /api/coding/submit`: Runs code against hidden & visible tests, calculates final score, saves submission, and synthesizes 2-3 technical viva questions via Nemotron / AST analysis.

## 6. Session Recording & Replay (`/api/sessions`)
- `POST /api/sessions/start`: Creates assessment session for student.
- `POST /api/sessions/{session_id}/events`: Buffers batches of keystroke, paste, run, submit, and tab-switch events.
- `POST /api/sessions/{session_id}/end`: Concludes session and triggers integrity signal analysis.
- `GET /api/sessions/{session_id}/replay`: Reconstructs chronological event list, code progress, and linked integrity signals.

## 7. Integrity Signals (`/api/integrity`)
- `GET /api/integrity/sessions/{session_id}/signals`: Returns flagged evidence signals for human review.
- `POST /api/integrity/sessions/{session_id}/analyze`: Manually triggers signal analysis on session events.

## 8. Explain Your Code Viva (`/api/explanation`)
- `GET /api/explanation/submission/{submission_id}/questions`: Retrieves technical questions generated from student's actual code.
- `POST /api/explanation/submit`: Submits student's explanations; evaluated by AI for technical consistency with the code implementation.
- `GET /api/explanation/submission/{submission_id}/results`: Retrieves evaluation scores and technical feedback.

## 9. Trainer Management (`/api/trainer`)
- `GET /api/trainer/dashboard`: System stats, average cohort mastery, weakest concepts, flagged integrity sessions.
- `GET /api/trainer/student/{student_id}`: Comprehensive student breakdown, history logs, submissions, and recorded sessions.
