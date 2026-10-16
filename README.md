# Adaptive Learning & Assessment Portal

A production-grade, AI-assisted platform that eliminates fixed learning sequences through Bayesian Knowledge Tracing, executes untrusted student code inside an isolated sandbox, and collects evidence-based integrity signals for human review without automated verdicts.

---

## 1. Problem Statement

1. **Fixed Learning Paths**: Traditional learning platforms provide every student with an identical sequence of questions regardless of whether they have already mastered foundational concepts or are struggling with unfulfilled prerequisites.
2. **Unreliable Online Assessments**: Coding assessments often rely on crude, black-box anti-cheat tools that either issue false automated accusations or fail to capture the student's authentic comprehension of the code they submit.

---

## 2. Our Solution

- **Dynamic Prerequisite Graph**: Concepts are organized into a Directed Acyclic Graph (DAG). The platform evaluates student mastery and selects the weakest eligible prerequisite rather than presenting questions in static order.
- **Explainable Rationale**: Every activity recommendation includes a clear, human-readable rationale explaining why it was selected.
- **Isolated Multi-Mode Sandbox**: Executes untrusted code inside a sandboxed environment with strict memory, CPU, process, and timeout limits.
- **Evidence-Based Integrity Engine**: Chronologically records keystroke, paste, delete, execution, and tab-switch events. It flags evidence (e.g. large pastes, missing write-run-fix cycles) pointing to the exact event index in the replay without making an automated cheating verdict.
- **AI-Driven "Explain Your Code" Viva**: Synthesizes 2–3 technical viva questions specifically based on the student's actual code implementation, evaluates their answers against the code structure, and flags inconsistencies for human review.

---

## 3. Technology Stack

### Frontend
- **React 18 / 19 & Vite**: Ultra-fast component bundling and responsive UI.
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
| **Trainer** | Dr. Alan Turing | `trainer@adaptive.edu` | `trainer123` | Access to cohort concept analytics, average mastery distributions, and weakest prerequisite bottlenecks. |

---

## 5. Local Installation & Setup

### Prerequisites
- Node.js (v18+ or v22+)
- Python (3.10, 3.11, or 3.12)
- Git
- Docker (optional for containerized sandbox, fallback mode operates out of the box)

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

---

## 6. Running Tests

Run the automated test suite covering authentication, Bayesian mastery tracking, adaptive path differentiation, sandbox timeouts, hostile security blocks, and integrity signals:

```bash
python -m pytest backend/tests
```

All 33 test suites across 7 test files pass with zero warnings (100% test pass rate).

---

## 7. Step-by-Step Hackathon Demo Flow (Phase 2 & Phase 3)
 
 1. **Step 1 — Login as Student A (Adaptive Concept DAG)**:
    - Go to `http://localhost:5173/login` and click **"Student A (Alice Walker)"**.
    - Note the recommendation: **"Practice Target: Constructors"** (40% baseline mastery).
    - Open **Concept Graph**: Notice `Programming Basics`, `Classes`, and `Objects` are green (`STRONG`), while `Constructors` is yellow (`DEVELOPING`), and `Inheritance`, `Polymorphism`, and `Dependency Injection` are locked (`LOCKED`).
 
 2. **Step 2 — Adaptive Question Progression & AI Tutoring**:
    - Click **Adaptive Practice**: The system presents a `Constructors` question with explainable rationale ("Weakest eligible prerequisite, all prerequisites satisfied").
    - Answer the question: Observe the instant Bayesian mastery update (+4.9% on correct answer).
    - Click **"Explain Concept with AI"**: OpenRouter AI generates an interactive concept breakdown with syntax examples and common pitfalls.
 
 3. **Step 3 — Login as Student B (Differentiation Proof)**:
    - Use the demo switcher in the top navbar to switch to **Student B (Bob Martinez)**.
    - Notice the recommendation: **"Practice Target: Classes"** (40% mastery).
    - Notice that `Objects` is locked because `Classes` has not yet reached the 65% prerequisite mastery threshold.
    - **Proof of Adaptivity**: Student A and Student B receive completely different questions and target different concepts based on prerequisite eligibility!
 
 4. **Step 4 — Coding Assessment & Sandbox**:
    - Navigate to **Coding Assessment** (`/student/assessment`).
    - Monaco Editor records typing bursts, deletions, replacements, and browser visibility changes with exact line/column locations.
    - Click **Run Tests**: Executes code against visible test cases inside the isolated sandbox.
    - Click **Submit & Explain Code**: Executes against hidden test cases and initiates the AI viva flow.
 
 5. **Step 5 — Explain Your Code (AI Viva Evaluation)**:
    - System presents 2–3 technical questions specifically generated from the student's actual code structure.
    - Student submits explanations: AI evaluates technical consistency and conceptual understanding.
 
 6. **Step 6 — Dedicated Coding Integrity Dashboard**:
    - Switch to **Trainer (Dr. Alan Turing)** and navigate to **Integrity Dashboard** (`/trainer/integrity`).
    - Searchable session table with filters for `NORMAL_RHYTHM`, `REVIEW_SUGGESTED`, and `INSUFFICIENT_DATA`.
    - **Typing Rhythm Visualizer**: Recharts plot of character burst sizes vs rolling baseline.
    - **Chronological Timeline**: Inspect individual events with line ranges (e.g. `L12:1 → L48:20`) and review classifications.
    - **Trainer Review Panel**: Actions for `Mark Reviewed`, `Dismiss`, and `Add Note` without automatic cheating verdicts.
 
 7. **Step 7 — Session Replay Studio**:
    - Click **Full Replay Studio** to scrub step-by-step through the student's code changes with event indicators.

---

## 8. Documentation Reference

- [Architecture Design & Topology](docs/architecture.md)
- [Database Schema & Relationships](docs/database.md)
- [Security Model & Sandbox Isolation](docs/security.md)
- [API Reference & Endpoint Guide](docs/api.md)
