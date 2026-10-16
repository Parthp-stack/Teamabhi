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
- `POST /api/mastery/update`: Diagnostic or manual score update (Trainer only, requires `student_id`).

## 4. Adaptive Learning Engine (`/api/learning`, `/api/student`)
- `GET /api/learning/next`: Calculates student's weakest eligible prerequisite and returns optimal question + explainable rationale.
- `GET /api/learning/path`: Returns student's adaptive learning path with completed, current target, prerequisites, and next expected concept.
- `POST /api/learning/attempt`: Submits answer, runs Bayesian update, records attempt, returns delta feedback.
- `POST /api/learning/hint`: Requests AI hint for the current question without revealing the solution.
- `GET /api/student/mastery`: Comprehensive overview of overall mastery and concept competencies.
- `GET /api/student/analytics`: Cohort/student performance analytics (difficulty performance, attempts per concept, mastery timeline).
- `GET /api/student/history`: Quiz assessment attempt history with score and feedback (hidden tests protected).
- `GET /api/student/coding-history`: Coding assessment submissions with test results, runtime, and viva scores.

## 5. Coding Sandbox & Submissions (`/api/coding`, `/api/code`)
- `GET /api/coding/problems`: Returns all coding problems with visible test cases only.
- `GET /api/coding/problems/{problem_id}`: Returns specific problem (hidden test cases are omitted).
- `POST /api/coding/run`: Executes code against visible test cases in the secure sandbox.
- `POST /api/coding/submit`: Runs code against hidden & visible tests, calculates final score, saves submission, and synthesizes 2-3 technical viva questions.
- `POST /api/coding/devops-lab/verify`: Automated AST/regex verification for browser-based DevOps laboratory tasks.

## 6. Session Recording & Replay (`/api/sessions`)
- `POST /api/sessions/start`: Creates assessment session for student.
- `POST /api/sessions/{session_id}/events`: Buffers batches of keystroke, paste, run, submit, and tab-switch events.
- `POST /api/sessions/{session_id}/end`: Concludes session and triggers integrity signal analysis.
- `GET /api/sessions/{session_id}/replay`: Reconstructs chronological event list, code progress, and linked integrity signals.

## 7. Integrity Signals & Human Review (`/api/integrity`)
- `GET /api/integrity/sessions/{session_id}/signals`: Returns flagged evidence signals for human review (Trainer only or session owner).
- `POST /api/integrity/sessions/{session_id}/analyze`: Manually triggers signal analysis on session events.
- `POST /api/integrity/sessions/{session_id}/review`: Updates review workflow status (`REVIEW_SUGGESTED`, `REVIEWED`, `DISMISSED`) with trainer notes.

## 8. Explain Your Code Viva (`/api/explanation`)
- `GET /api/explanation/submission/{submission_id}/questions`: Retrieves technical questions generated from student's actual code.
- `POST /api/explanation/submit`: Submits student's explanations; evaluated by AI for technical consistency with the code implementation.
- `GET /api/explanation/submission/{submission_id}/results`: Retrieves evaluation scores and technical feedback.

## 9. Trainer Management & Curriculum (`/api/trainer`)
- `GET /api/trainer/dashboard`: System stats, average cohort mastery, bottleneck alerts, flagged integrity sessions.
- `GET /api/trainer/curriculum`: Courses, modules, concepts with prerequisite IDs, and question counts.
- `GET /api/trainer/student/{student_id}`: Comprehensive student breakdown, history logs, submissions, and recorded sessions.
- `POST /api/trainer/prerequisites/validate`: Validates concept prerequisite modifications against cycles in the DAG.
- `POST /api/trainer/concepts`: Create new concept with prerequisite associations.
- `PUT /api/trainer/concepts/{concept_id}`: Update concept title, description, order, or prerequisites.
- `GET /api/trainer/questions`: Search and filter question bank by concept and difficulty.
- `POST /api/trainer/questions`: Create question in the question bank.
- `PUT /api/trainer/questions/{question_id}`: Edit question details.
- `DELETE /api/trainer/questions/{question_id}`: Delete question from question bank.
- `POST /api/trainer/questions/preview-ai`: Generate AI question draft for human preview and review.
- `POST /api/trainer/repo-evaluation`: Structural and quality evaluation of a GitHub repository.
- `POST /api/trainer/repo-evaluation/viva`: Automated evaluation of student architectural viva answers.
