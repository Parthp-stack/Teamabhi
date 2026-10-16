# Adaptive Learning & Assessment Portal

A production-grade, AI-assisted platform that eliminates fixed learning sequences through Bayesian Knowledge Tracing, executes untrusted student code inside an isolated multi-mode sandbox, collects evidence-based integrity signals for human review without automated verdicts, and provides comprehensive curriculum management, cohort analytics, repository evaluation, and DevOps labs.

---

## 1. Problem Statement

1. **Fixed Learning Paths**: Traditional learning platforms force every student through an identical linear sequence of questions regardless of whether they have already mastered foundational concepts or are struggling with unfulfilled prerequisites.
2. **Unreliable Online Assessments**: Coding assessments often rely on crude, black-box anti-cheat tools that either issue false automated accusations or fail to capture the student's authentic comprehension of the code they submit.
3. **Rigid Course Management**: Trainers lack pedagogical bottleneck visibility and struggle to maintain prerequisite relationships without introducing circular dependency errors.

---

## 2. Platform Architecture & Solutions

- **Dynamic Prerequisite Graph (DAG)**: Concepts are organized in a Directed Acyclic Graph. The adaptive engine evaluates student mastery and selects the weakest eligible prerequisite rather than presenting questions in static order.
- **Explainable Rationale**: Every activity recommendation includes a clear, human-readable rationale explaining why it was selected.
- **Complete Student Dashboard**:
  - Live overall mastery progression gauge & concept competencies (Strong, Developing, Weak, Locked, Current Target).
  - Adaptive learning path with step-by-step progress, prerequisites, and next expected concepts.
  - Interactive Recharts analytics (Mastery by Concept, Mastery Improvement over Time, Correct vs Incorrect attempts, Difficulty performance).
  - Assessment history for quiz attempts and coding submissions with Explain Your Code Viva Voce results modal.
- **Complete Trainer Dashboard & Cohort Analytics**:
  - Cohort Overview metrics (Total students, average mastery, average assessment score, coding performance).
  - Pedagogical bottleneck alert banner highlighting concepts where >30% of students struggle.
  - Concept Mastery cohort table with average mastery and weak student percentage.
  - Searchable and filterable student directory with direct deep dives.
- **Student Detail Deep Dive**:
  - Concept-by-concept mastery breakdown and history.
  - Adaptive learning path inspector.
  - Quiz assessment attempt table.
  - Coding submissions & viva scores with direct links to the Coding Integrity Dashboard.
- **Curriculum & Question Bank Management**:
  - Course, Module, and Concept CRUD.
  - Prerequisite Matrix with real-time Directed Acyclic Graph (DAG) cycle detection.
  - Question Bank with concept & difficulty filters, full edit/create capabilities.
  - AI Question Generation with human preview and approval before saving to question bank.
- **Isolated Multi-Mode Sandbox**: Executes untrusted code inside an isolated sandbox with strict memory, CPU, process, and timeout limits (Docker container or restricted AST fallback).
- **Evidence-Based Integrity Engine**: Chronologically records keystroke, paste, delete, execution, and tab-switch events. It flags evidence (e.g. large pastes, missing write-run-fix cycles) pointing to the exact event index in the replay without making an automated cheating verdict.
- **AI-Driven "Explain Your Code" Viva**: Synthesizes 2–3 technical viva questions specifically based on the student's actual code implementation, evaluates their answers against the code structure, and flags inconsistencies for human review.
- **Optional Advanced Features**:
  - **GitHub Repository Evaluation**: Structural analysis, AST scanning, line-level code review, and viva questions.
  - **Architecture Viva Voce**: Technical evaluation of architectural decisions.
  - **DevOps Laboratory**: Browser-based interactive DevOps tasks (Dockerfile, docker-compose, CI/CD pipeline) with automated AST/regex verification.

---

## 3. Technology Stack

### Frontend
- **React 18 / 19 & Vite**: Ultra-fast component bundling and responsive UI.
- **Tailwind CSS & Lucide Icons**: Modern, accessible UI styling and icons.
- **Monaco Editor (`@monaco-editor/react`)**: Industry-standard IDE code editing.
- **React Flow (`reactflow`)**: Interactive prerequisite DAG with live mastery color status.
- **Recharts**: Knowledge growth and Bayesian tracing trajectory visualization.
- **Axios & React Router**: JWT-intercepted REST communication and role-based routing.

### Backend
- **Python 3.12 & FastAPI**: High-performance asynchronous API framework.
- **SQLAlchemy 2.0 & Pydantic V2**: Strongly typed ORM and validation models.
- **PostgreSQL / SQLite**: Multi-dialect relational database support with auto-migration.
- **JWT & Bcrypt**: Secure token authentication and salted credential hashing.

### AI Engine (OpenRouter)
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b:free`
- **Abstraction Layer**: Decoupled `AIService` supporting zero-downtime provider substitution with deterministic AST fallbacks.

### Code Sandbox
- **Docker Isolation**: Containers run with `--network none`, `--memory 128m`, `--nano-cpus 500000000`, `--pids-limit 50`, non-root user `sandboxuser`.
- **Process Sandbox Fallback**: AST analysis blocking unsafe syscalls (`os`, `subprocess`, `socket`) when Docker is absent.

---

## 4. Key Demo Accounts

The database comes pre-seeded with three demo profiles to demonstrate adaptive differentiation:

| Role | Name | Email | Password | Baseline State |
|---|---|---|---|---|
| **Student A** | Alice Walker | `student.a@adaptive.edu` | `student123` | Completed Classes (90%) & Objects (85%), weak in Constructors (40%). Prerequisites satisfied. Recommends **Constructors**. |
| **Student B** | Bob Martinez | `student.b@adaptive.edu` | `student123` | Weak in Classes (40%). Objects is locked because Classes < 65% prerequisite threshold. Recommends **Classes**. |
| **Trainer** | Dr. Alan Turing | `trainer@adaptive.edu` | `trainer123` | Full access to cohort concept analytics, curriculum manager, question bank, student deep dives, and session replay studio. |

---

## 5. Local Installation & Startup

### Prerequisites
- Node.js (v18+ or v22+)
- Python (3.10, 3.11, or 3.12)
- Git

### 1. Clone & Setup Environment
```bash
git clone https://github.com/your-org/adaptive-learning-platform.git
cd adaptive-learning-platform

# Copy environment variables
cp .env.example .env
```

### 2. Backend Installation & Startup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run backend with auto-reload (database initializes and seeds automatically)
python -m uvicorn backend.main:app --reload --port 8000
```
Backend will be live at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### 3. Frontend Installation & Startup
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend will be accessible at `http://localhost:5173`.

### Quick Start Scripts
- Windows: Run `.\start.bat` or `.\start.ps1` from the root directory to launch both frontend and backend concurrently.

---

## 6. Running Tests

Run the complete automated test suite covering all 4 Phases:
```bash
python -m pytest backend/tests
```

**Result: 41 passed, 0 failed in 14s (100% test pass rate).**

Test coverage includes:
- Authentication & JWT token issuance (`test_auth.py`)
- Bayesian Knowledge Tracing & mastery updates (`test_mastery.py`, `test_phase2_adaptive.py`)
- Prerequisite DAG resolution & dynamic path generation (`test_adaptive.py`)
- Multi-mode sandbox security and timeout isolation (`test_sandbox.py`)
- Session event recording, rhythm classification, and replay timeline (`test_integrity.py`, `test_integrity_tracking.py`)
- Phase 4 integration: student analytics, trainer curriculum, DAG cycle rejection, AI question draft preview, repo viva evaluation, and DevOps lab verification (`test_phase4_integration.py`)

---

## 7. Step-by-Step Hackathon Demo Walkthrough

### Step 1 — Login as Student A (Adaptive Concept DAG)
1. Go to `http://localhost:5173/login` and click **"Student A (Alice Walker)"**.
2. On the **Student Dashboard**, observe:
   - Overall Mastery: 65.7% with progression gauge.
   - Concept list: `Programming Basics`, `Classes`, and `Objects` are green (`STRONG`), `Constructors` is yellow (`DEVELOPING`), while `Inheritance`, `Polymorphism`, and `Dependency Injection` are locked (`LOCKED`).
   - Learning Path stepper: `Classes` (✓), `Objects` (✓), `Constructors` (→ Current Target).
   - Click the **Analytics** tab to view Recharts visualizations (Mastery by Concept, Correct vs Incorrect attempts, Difficulty performance).

### Step 2 — Adaptive Practice & AI Tutoring
1. Click **Adaptive Practice** in the sidebar.
2. The system presents a `Constructors` question with explainable rationale ("Weakest eligible prerequisite, all prerequisites satisfied").
3. Answer the question: Observe the instant Bayesian mastery update (+4.9% on correct answer).
4. Click **"Explain Concept with AI"**: OpenRouter AI generates an interactive concept breakdown with syntax examples and common pitfalls.

### Step 3 — Login as Student B (Differentiation Proof)
1. Use the demo switcher in the top navbar to switch to **Student B (Bob Martinez)**.
2. On the Dashboard, observe:
   - Target Concept: **Classes** (40% mastery).
   - `Objects` is locked because `Classes` has not yet reached the 65% prerequisite threshold.
   - **Proof of Adaptivity**: Student A and Student B receive completely different questions and target different concepts based on prerequisite eligibility!

### Step 4 — Coding Assessment & AI Viva Voce
1. Navigate to **Coding Assessment** (`/student/assessment`).
2. Monaco Editor records typing bursts, deletions, replacements, and browser visibility changes.
3. Click **Run Tests**: Executes code against visible test cases inside the isolated sandbox.
4. Click **Submit & Explain Code**: Executes against hidden test cases and initiates the AI viva flow.
5. Answer the technical viva questions generated specifically from your code implementation.

### Step 5 — Complete Trainer Dashboard & Cohort Analytics
1. Switch to **Trainer (Dr. Alan Turing)** and navigate to **Trainer Dashboard** (`/trainer/dashboard`).
2. Review the **Class Overview** cards (Total Students: 2, Average Mastery: 53.6%, Avg Assessment: 85%, Coding Score: 78%).
3. Notice the **Pedagogical Bottleneck Alert**: flags `Constructors` and `Inheritance` where students need reinforcement.
4. Review the cohort concept mastery table and filter students by score or concept.

### Step 6 — Student Detail Deep Dive
1. From the Trainer Dashboard, click **View Profile** on Alice Walker (`/trainer/student/1`).
2. Inspect her concept mastery breakdown, quiz assessment history, and coding submissions.
3. Click **Inspect Integrity Session**: directly opens the recorded coding session in the Integrity Dashboard.

### Step 7 — Coding Integrity Dashboard & Replay Studio
1. Navigate to **Integrity Dashboard** (`/trainer/integrity`).
2. Filter sessions by review status (`NORMAL_RHYTHM`, `REVIEW_SUGGESTED`, `INSUFFICIENT_DATA`).
3. View the **Typing Rhythm Visualizer** and **Chronological Event Timeline**.
4. Open the **Replay Studio** to scrub step-by-step through the student's code changes.
5. Use the human review workflow: add notes, mark reviewed, or dismiss.

### Step 8 — Curriculum & Question Bank Management
1. Navigate to **Curriculum Management** (`/trainer/curriculum`).
2. **Concept & Prerequisite DAG Editor**: Select a concept and modify prerequisites. If a circular prerequisite is selected (e.g. A requires B and B requires A), the system detects and rejects the cycle immediately.
3. **Question Bank**: Filter questions by concept and difficulty, create or edit questions with options and explanations.
4. **AI Question Preview**: Generate a new draft question with AI, review and inspect the question/options/explanation, and approve it before saving to the question bank.

### Step 9 — Optional Features: GitHub Repo Evaluation & DevOps Lab
1. Navigate to **Repo Evaluation & DevOps** (`/trainer/repo-eval`).
2. **GitHub Repository Evaluation**: Enter a repository (e.g. `tiangolo/fastapi`) to analyze structure, detected languages, demonstrated concepts, and line-level review comments.
3. **Architecture Viva Voce**: Answer architecture questions and view instant technical evaluation.
4. **DevOps Laboratory**: Select a task (e.g. `Create Dockerfile`), write or inspect the configuration, and click **Verify Solution** for instant automated AST/regex verification.

---

## 8. Security & RBAC Verification

- **Role-Based Access Control**:
  - `STUDENT`: Can access own mastery, learning path, quiz/coding assessments, and viva. Blocked from viewing hidden test cases, trainer routes, or other students' data.
  - `TRAINER`: Can access cohort analytics, student deep dives, curriculum editor, question bank, and coding integrity sessions. Blocked from modifying student passwords or bypassing sandbox boundaries.
- **Mastery Integrity**: Students cannot directly modify mastery scores via API (`POST /api/mastery/update` requires `require_trainer` and an explicit `student_id`).
- **Hidden Test Protection**: Coding problems served to students exclude `is_hidden=True` test cases.
- **Sandbox Security**: Code execution is sandboxed with memory limits, process limits, CPU quotas, and AST blacklisting of dangerous modules.

---

## 9. Documentation Reference

- [Architecture Design & Topology](docs/architecture.md)
- [Database Schema & Relationships](docs/database.md)
- [Security Model & Sandbox Isolation](docs/security.md)
- [API Reference & Endpoint Guide](docs/api.md)
