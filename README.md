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
| **Student A** | Alice Walker | `student.a@adaptive.edu` | `student123` | High in Classes/Objects (95/90%), weak in Inheritance (45%) & Polymorphism (30%). Recommends **Inheritance**. |
| **Student B** | Bob Martinez | `student.b@adaptive.edu` | `student123` | High in all foundations (88-95%), eligible for **Dependency Injection** (20%). Recommends **Dependency Injection**. |
| **Trainer** | Dr. Alan Turing | `trainer@adaptive.edu` | `trainer123` | Access to cohort analytics, integrity evidence timeline, and session replays. |

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

All 9 test suites pass with zero warnings.

---

## 7. Step-by-Step Hackathon Demo Flow

1. **Step 1 — Login as Student A**:
   - Go to `http://localhost:5173/login` and click **"Student A (Alice Walker)"**.
   - Note the recommendation: **"Practice Target: Inheritance"** (mastery 45%).
   - Open **Concept Graph**: Notice Classes, Objects, and Constructors are green (`MASTERED`), while Inheritance is orange (`WEAK`).

2. **Step 2 — Adaptive Question Progression**:
   - Click **Adaptive Practice**: The system presents an Inheritance question with explainable rationale.
   - Answer the question: Observe the instant Bayesian mastery update (+8% on correct answer).

3. **Step 3 — Login as Student B (Differentiation Proof)**:
   - Use the demo switcher in the top navbar to switch to **Student B**.
   - Notice the recommendation: **"Practice Target: Dependency Injection"** (mastery 20%).
   - **Proof of Adaptivity**: Student A and Student B receive completely different questions based on individual prerequisite competency!

4. **Step 4 — Coding Assessment & Sandbox**:
   - Navigate to **Coding Assessment**.
   - Edit the Python code in Monaco Editor.
   - Click **Run Tests**: Runs against visible test cases inside the sandbox.
   - Click **Submit & Explain Code**: Runs against hidden tests and triggers the AI viva workflow.

5. **Step 5 — Explain Your Code (Viva)**:
   - The system presents 2–3 questions specifically generated from the student's actual code.
   - Enter answers and submit: AI evaluates technical consistency against the implementation.

6. **Step 6 — Trainer Review & Session Replay**:
   - Switch to **Trainer (Alan Turing)** using the top bar.
   - Open **Session Replay** for the assessment:
     - Left column: Chronological event timeline (focus, paste, run, submit).
     - Center column: Monaco Editor reconstructing code changes with play/pause and scrubber slider.
     - Right column: Evidence signals (e.g. `LARGE_PASTE`, `NO_CYCLE`).
     - Click **"Jump to Event #2"** on the Large Paste signal: The replay scrubber immediately seeks to that exact moment!

---

## 8. Documentation Reference

- [Architecture Design & Topology](docs/architecture.md)
- [Database Schema & Relationships](docs/database.md)
- [Security Model & Sandbox Isolation](docs/security.md)
- [API Reference & Endpoint Guide](docs/api.md)
