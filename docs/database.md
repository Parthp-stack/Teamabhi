# Database Schema & Relational Specifications

## Entity Relationship Overview

The schema is built for PostgreSQL with full support for SQLite development fallback via SQLAlchemy 2.0.

### 1. `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Auto | Unique user ID |
| `name` | String(100) | Not Null | Display name |
| `email` | String(255) | Unique, Index | User email address |
| `password_hash` | String(255) | Not Null | Bcrypt hashed password |
| `role` | String(20) | Not Null | `STUDENT` or `TRAINER` |
| `created_at` | DateTime | UTC | Registration timestamp |

### 2. `courses` & `modules`
- `courses`: `id`, `title`, `description`, `created_at`
- `modules`: `id`, `course_id` (FK), `title`, `description`, `order_index`

### 3. `concepts` & `concept_prerequisites`
- `concepts`: `id`, `module_id` (FK), `name`, `description`
- `concept_prerequisites`: Junction table forming the Directed Acyclic Graph:
  - `concept_id` (FK -> concepts.id)
  - `prerequisite_id` (FK -> concepts.id)

### 4. `questions` & `attempts`
- `questions`: `id`, `concept_id` (FK), `type` (MCQ, SHORT_ANSWER, CODING), `title`, `description`, `difficulty`, `options` (JSON), `correct_answer`, `explanation`
- `attempts`: `id`, `student_id` (FK), `question_id` (FK), `answer`, `correct`, `timestamp`

### 5. `student_mastery` & `mastery_history`
- `student_mastery`: `id`, `student_id` (FK), `concept_id` (FK), `mastery` (Float 0-100), `attempts`, `correct_attempts`, `updated_at`
- `mastery_history`: `id`, `student_id` (FK), `concept_id` (FK), `mastery`, `change_amount`, `reason`, `timestamp`

### 6. `coding_problems` & `test_cases`
- `coding_problems`: `id`, `title`, `description`, `difficulty`, `allowed_languages` (JSON), `time_limit`, `memory_limit`
- `test_cases`: `id`, `problem_id` (FK), `input`, `expected_output`, `is_hidden` (Boolean). **Hidden test cases are strictly filtered server-side and never returned to the frontend.**

### 7. `coding_submissions`
- `id`, `student_id` (FK), `problem_id` (FK), `language`, `source_code`, `status`, `score`, `execution_time`, `memory_used`, `created_at`

### 8. `sessions` & `session_events`
- `sessions`: `id`, `student_id` (FK), `assessment_id` (FK), `started_at`, `ended_at`
- `session_events`: `id`, `session_id` (FK), `event_type` (`KEYSTROKE`, `DELETE`, `PASTE`, `RUN`, `SUBMIT`, `FOCUS`, `BLUR`, `TAB_SWITCH`), `timestamp`, `metadata` (JSON)

### 9. `integrity_signals`
- `id`, `session_id` (FK), `event_id` (FK -> session_events.id), `signal_type` (`LARGE_PASTE`, `FAST_CODE`, `NO_CYCLE`, `TAB_SWITCH`, `UNIFORM_TYPING`), `severity` (`LOW`, `MEDIUM`, `HIGH`), `description`, `timestamp`

### 10. `explanation_questions` & `explanation_answers`
- `explanation_questions`: `id`, `submission_id` (FK), `question`, `expected_concept`
- `explanation_answers`: `id`, `explanation_question_id` (FK), `student_answer`, `evaluation`, `score` (0-10), `created_at`
