-- =====================================================================
-- ADAPTIVE LEARNING & AI ASSESSMENT PLATFORM
-- SUPABASE POSTGRESQL PRODUCTION DDL & INITIAL SEED SCRIPT
-- =====================================================================
-- This script creates all required relational tables, foreign key constraints,
-- performance indexes, and initial seed data for hosting on Render with Supabase.
-- Compatible with PostgreSQL 14+, Supabase, and SQLAlchemy.
-- =====================================================================

-- 1. USERS & AUTHENTICATION TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'STUDENT' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. COURSES TABLE
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. MODULES TABLE
CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    order_index INTEGER DEFAULT 0
);

-- 4. CONCEPTS TABLE (DAG Vertices)
CREATE TABLE IF NOT EXISTS concepts (
    id SERIAL PRIMARY KEY,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20) DEFAULT 'MEDIUM',
    order_index INTEGER DEFAULT 0
);

-- 5. CONCEPT PREREQUISITES TABLE (DAG Directed Edges)
CREATE TABLE IF NOT EXISTS concept_prerequisites (
    concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    prerequisite_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    PRIMARY KEY (concept_id, prerequisite_id)
);

-- 6. STUDENT MASTERY TABLE (Bayesian Knowledge Tracing)
CREATE TABLE IF NOT EXISTS student_mastery (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    mastery_score FLOAT DEFAULT 0.0,
    confidence_score FLOAT DEFAULT 0.5,
    status VARCHAR(20) DEFAULT 'LOCKED',
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    CONSTRAINT uq_student_concept UNIQUE (student_id, concept_id)
);

-- 7. MASTERY HISTORY TABLE
CREATE TABLE IF NOT EXISTS mastery_history (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    mastery_score FLOAT NOT NULL,
    delta FLOAT NOT NULL,
    reason VARCHAR(50),
    reason_detail TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. TOPICS TABLE
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL
);

-- 9. QUESTIONS TABLE (Adaptive Question Bank)
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) DEFAULT 'MCQ',
    difficulty VARCHAR(20) DEFAULT 'MEDIUM',
    options JSONB,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    code_snippet TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. ATTEMPTS TABLE (MCQ Historical Attempts)
CREATE TABLE IF NOT EXISTS attempts (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    selected_answer TEXT,
    is_correct BOOLEAN DEFAULT FALSE,
    score FLOAT DEFAULT 0.0,
    time_taken FLOAT DEFAULT 0.0,
    assessment_id VARCHAR(100),
    attempt_number INTEGER DEFAULT 1,
    difficulty VARCHAR(20),
    concept_id INTEGER,
    assessment_attempt_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. CODING PROBLEMS TABLE
CREATE TABLE IF NOT EXISTS coding_problems (
    id SERIAL PRIMARY KEY,
    concept_id INTEGER REFERENCES concepts(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    problem_statement TEXT,
    input_format TEXT,
    output_format TEXT,
    constraints TEXT,
    examples JSONB,
    expected_solution_concept VARCHAR(100),
    topic VARCHAR(100),
    difficulty VARCHAR(20) DEFAULT 'MEDIUM',
    starter_code JSONB,
    time_limit_seconds FLOAT DEFAULT 5.0,
    memory_limit_mb INTEGER DEFAULT 128,
    allowed_languages JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. CODING TEST CASES TABLE
CREATE TABLE IF NOT EXISTS coding_test_cases (
    id SERIAL PRIMARY KEY,
    problem_id INTEGER NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
    input TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    explanation TEXT,
    weight FLOAT DEFAULT 1.0
);

-- 13. CODING SESSIONS TABLE (Sessions Audit)
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_id INTEGER REFERENCES coding_problems(id) ON DELETE SET NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    overall_review_status VARCHAR(50) DEFAULT 'INSUFFICIENT_DATA',
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT
);

-- 14. SESSION EVENTS TABLE (Keystroke & Editor Events)
CREATE TABLE IF NOT EXISTS session_events (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_id INTEGER,
    client_event_id VARCHAR(100),
    event_type VARCHAR(50) NOT NULL,
    server_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    client_timestamp TIMESTAMP WITH TIME ZONE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    code_location JSONB,
    revision_id INTEGER,
    inserted_character_count INTEGER DEFAULT 0,
    deleted_character_count INTEGER DEFAULT 0,
    duration FLOAT,
    review_status VARCHAR(50) DEFAULT 'NORMAL_RHYTHM',
    classification VARCHAR(100),
    classification_reason TEXT,
    event_metadata JSONB
);

-- 15. CODE REVISIONS TABLE (Snapshots)
CREATE TABLE IF NOT EXISTS code_revisions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    event_id INTEGER,
    revision_number INTEGER NOT NULL,
    snapshot_type VARCHAR(50) DEFAULT 'INCREMENTAL',
    source_code TEXT NOT NULL,
    diff_summary VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 16. CODING SUBMISSIONS TABLE
CREATE TABLE IF NOT EXISTS coding_submissions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    problem_id INTEGER NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    language VARCHAR(50) NOT NULL,
    source_code TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    passed_test_cases INTEGER DEFAULT 0,
    total_test_cases INTEGER DEFAULT 0,
    execution_time_seconds FLOAT DEFAULT 0.0,
    memory_used_mb FLOAT DEFAULT 0.0,
    compile_error TEXT,
    runtime_error TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 17. INTEGRITY SIGNALS TABLE (Heuristic Flags)
CREATE TABLE IF NOT EXISTS integrity_signals (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES session_events(id) ON DELETE SET NULL,
    signal_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    description TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    review_status VARCHAR(50) DEFAULT 'PENDING',
    trainer_notes TEXT,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE
);

-- 18. EXPLANATION QUESTIONS TABLE (Viva)
CREATE TABLE IF NOT EXISTS explanation_questions (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER NOT NULL REFERENCES coding_submissions(id) ON DELETE CASCADE,
    question_index INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    target_construct VARCHAR(100),
    code_reference TEXT,
    question_type VARCHAR(50) DEFAULT 'OPEN_RESPONSE',
    mcq_options JSONB,
    ideal_explanation_rubric TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 19. EXPLANATION ANSWERS TABLE
CREATE TABLE IF NOT EXISTS explanation_answers (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES explanation_questions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_response TEXT NOT NULL,
    score FLOAT DEFAULT 0.0,
    ai_feedback TEXT,
    evaluated_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'SUBMITTED'
);

-- 20. ASSESSMENT ATTEMPTS TABLE (Requirement 1, 2, 10, 12)
CREATE TABLE IF NOT EXISTS assessment_attempts (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_id VARCHAR(100) NOT NULL,
    assessment_type VARCHAR(50) DEFAULT 'CODING',
    attempt_number INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'IN_PROGRESS',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    score FLOAT DEFAULT 0.0,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    integrity_events_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    risk_score FLOAT DEFAULT 0.0,
    risk_level VARCHAR(50) DEFAULT 'NORMAL',
    current_question_index INTEGER DEFAULT 1
);

-- 21. ASSESSMENT WARNINGS TABLE (Requirement 9)
CREATE TABLE IF NOT EXISTS assessment_warnings (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_id VARCHAR(100),
    attempt_id INTEGER REFERENCES assessment_attempts(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    warning_type VARCHAR(50) NOT NULL,
    warning_number INTEGER DEFAULT 1,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'LOW',
    evidence JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 22. QUESTION ATTEMPTS TABLE (Requirements 1, 2: Navigation & State Preservation)
CREATE TABLE IF NOT EXISTS question_attempts (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_id VARCHAR(100),
    attempt_id INTEGER REFERENCES assessment_attempts(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
    question_number INTEGER NOT NULL,
    selected_answer TEXT,
    previous_answer TEXT,
    answer_status VARCHAR(50) DEFAULT 'UNANSWERED',
    visited BOOLEAN DEFAULT FALSE,
    submitted BOOLEAN DEFAULT FALSE,
    is_changed BOOLEAN DEFAULT FALSE,
    is_correct BOOLEAN,
    score FLOAT DEFAULT 0.0,
    time_taken FLOAT DEFAULT 0.0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 23. STUDENT CONCEPT PROGRESS TABLE
CREATE TABLE IF NOT EXISTS student_concept_progress (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    consecutive_correct INTEGER DEFAULT 0,
    consecutive_incorrect INTEGER DEFAULT 0,
    last_difficulty VARCHAR(20) DEFAULT 'MEDIUM',
    is_remedial BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_concept_progress UNIQUE (student_id, concept_id)
);

-- 24. INTEGRITY EVENTS TABLE (Requirements 4, 5, 6, 7, 8, 12: Dedicated 12-Column Audit)
CREATE TABLE IF NOT EXISTS integrity_events (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assessment_id VARCHAR(100),
    attempt_id INTEGER REFERENCES assessment_attempts(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
    question_number INTEGER,
    event_type VARCHAR(100) NOT NULL,
    action VARCHAR(200),
    details TEXT,
    risk_level VARCHAR(50) DEFAULT 'NORMAL',
    warning TEXT,
    source VARCHAR(50) DEFAULT 'ASSESSMENT',
    event_metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- PERFORMANCE INDEXES (Optimized for Render & Supabase)
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_concepts_module ON concepts(module_id);
CREATE INDEX IF NOT EXISTS idx_questions_concept ON questions(concept_id);
CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id, assessment_id);
CREATE INDEX IF NOT EXISTS idx_sessions_student ON sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_session_events_session ON session_events(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_asst_attempts_student_asst ON assessment_attempts(student_id, assessment_id);
CREATE INDEX IF NOT EXISTS idx_question_attempts_att_qnum ON question_attempts(attempt_id, question_number);
CREATE INDEX IF NOT EXISTS idx_integrity_events_student ON integrity_events(student_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_integrity_events_risk ON integrity_events(risk_level);
CREATE INDEX IF NOT EXISTS idx_integrity_events_type ON integrity_events(event_type);

-- =====================================================================
-- SEED INITIAL DATA (Idempotent: Uses ON CONFLICT DO NOTHING)
-- =====================================================================

-- 1. Default Users (Passwords: Password123!)
INSERT INTO users (id, name, email, hashed_password, role)
VALUES 
    (1, 'Lead Instructor', 'trainer@adaptive.edu', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'TRAINER'),
    (2, 'Alice Student', 'student.a@adaptive.edu', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'STUDENT'),
    (3, 'Bob Learner', 'student.b@adaptive.edu', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'STUDENT')
ON CONFLICT (id) DO NOTHING;

SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));

-- 2. Course
INSERT INTO courses (id, title, description, order_index)
VALUES 
    (1, 'Object Oriented Programming', 'Comprehensive mastery of OOP abstractions, design principles, and memory invariants.', 1)
ON CONFLICT (id) DO NOTHING;

SELECT setval('courses_id_seq', (SELECT MAX(id) FROM courses));

-- 3. Modules
INSERT INTO modules (id, course_id, title, description, order_index)
VALUES 
    (1, 1, 'Module 1: Foundations', 'Variables, Control Flow, and Procedural Foundations', 1),
    (2, 1, 'Module 2: OOP Core', 'Classes, Objects, and Instantiation Lifecycle', 2),
    (3, 1, 'Module 3: Advanced OOP', 'Encapsulation, Inheritance, and Polymorphism', 3),
    (4, 1, 'Module 4: Architectural Patterns', 'Design Patterns and Interface Decoupling', 4)
ON CONFLICT (id) DO NOTHING;

SELECT setval('modules_id_seq', (SELECT MAX(id) FROM modules));

-- 4. Concepts (DAG Vertices)
INSERT INTO concepts (id, module_id, name, description, difficulty, order_index)
VALUES 
    (1, 1, 'Programming Basics', 'Core syntax, variables, primitive types, and control flow structures.', 'EASY', 1),
    (2, 2, 'Classes', 'Blueprints for user-defined types encapsulating state and behavior.', 'EASY', 2),
    (3, 2, 'Objects', 'Concrete heap/stack instances created from class definitions.', 'EASY', 3),
    (4, 2, 'Constructors', 'Initialization routines executing upon object instantiation.', 'EASY', 4),
    (5, 3, 'Encapsulation', 'Hiding internal representations and enforcing state invariants.', 'MEDIUM', 5),
    (6, 3, 'Inheritance', 'Deriving new classes from base types to share structure and logic.', 'MEDIUM', 6),
    (7, 3, 'Polymorphism', 'Dynamic dispatch and uniform interface execution across subtypes.', 'HARD', 7)
ON CONFLICT (id) DO NOTHING;

SELECT setval('concepts_id_seq', (SELECT MAX(id) FROM concepts));

-- 5. Concept Prerequisites (DAG Edges)
INSERT INTO concept_prerequisites (concept_id, prerequisite_id)
VALUES 
    (2, 1), -- Classes requires Programming Basics
    (3, 2), -- Objects requires Classes
    (4, 2), -- Constructors requires Classes
    (5, 3), -- Encapsulation requires Objects
    (6, 2), -- Inheritance requires Classes
    (7, 6)  -- Polymorphism requires Inheritance
ON CONFLICT DO NOTHING;

-- 6. Question Bank (MCQs with JSON options and explanations)
INSERT INTO questions (id, concept_id, question_text, question_type, difficulty, options, correct_answer, explanation)
VALUES 
    (1, 1, 'What is the primary function of a conditional statement in procedural programming?', 'MCQ', 'EASY', 
     '["Branch execution flow based on boolean expressions", "Allocate dynamic heap memory", "Declare a new class definition", "Compile byte code into native machine instructions"]'::jsonb,
     'Branch execution flow based on boolean expressions',
     'Conditional statements (if/else) evaluate boolean expressions to determine which code branch executes.'),

    (2, 2, 'Which of the following best defines a Class in Object-Oriented Programming?', 'MCQ', 'EASY',
     '["A blueprint or template defining variables and methods", "A running instance in active memory", "A primitive data type like integer or float", "An automated garbage collector"]'::jsonb,
     'A blueprint or template defining variables and methods',
     'A class serves as a user-defined blueprint from which individual object instances are created.'),

    (3, 3, 'When an object is instantiated, where is its instance state typically allocated in modern runtime environments?', 'MCQ', 'EASY',
     '["Heap memory", "ROM", "Hard drive swap only", "Network buffer"]'::jsonb,
     'Heap memory',
     'In most object-oriented runtime engines (Python, Java, C#), object instances are allocated on the managed heap.'),

    (4, 4, 'What is the principal purpose of a constructor method in an object-oriented class?', 'MCQ', 'EASY',
     '["Initialize object attributes and establish initial state invariants", "Delete the object from RAM", "Prevent any subclass from inheriting methods", "Recompile source code at runtime"]'::jsonb,
     'Initialize object attributes and establish initial state invariants',
     'Constructors execute immediately upon object creation to guarantee valid starting state.'),

    (5, 5, 'How does Encapsulation protect object integrity?', 'MCQ', 'MEDIUM',
     '["By restricting direct field access and mediating mutations via methods", "By making all fields public and mutable", "By disabling method invocation", "By converting code to procedural C"]'::jsonb,
     'By restricting direct field access and mediating mutations via methods',
     'Encapsulation bundles data and methods while restricting direct external manipulation to prevent invalid states.'),

    (6, 6, 'What capability does Inheritance provide in class design?', 'MCQ', 'MEDIUM',
     '["Reusing and specializing attributes and behaviors from a base class", "Running code across multiple CPU cores simultaneously", "Eliminating all class definitions", "Enforcing 100% test coverage automatically"]'::jsonb,
     'Reusing and specializing attributes and behaviors from a base class',
     'Inheritance allows a subclass to inherit attributes and methods from an existing superclass.'),

    (7, 7, 'Which mechanism enables runtime Polymorphism in object-oriented languages?', 'MCQ', 'HARD',
     '["Dynamic dispatch via method overriding and vtables", "Static compile-time inlining only", "Renaming variables before compilation", "Storing code in plain text files"]'::jsonb,
     'Dynamic dispatch via method overriding and vtables',
     'Polymorphism relies on dynamic dispatch (virtual method tables) to invoke the correct overridden implementation at runtime.')
ON CONFLICT (id) DO NOTHING;

SELECT setval('questions_id_seq', (SELECT MAX(id) FROM questions));

-- 7. Coding Problem
INSERT INTO coding_problems (id, concept_id, title, description, problem_statement, input_format, output_format, constraints, examples, expected_solution_concept, topic, difficulty, starter_code)
VALUES 
    (1, 5, 'Bank Account Invariant Safety', 
     'Implement a robust BankAccount class that enforces strict invariant checks on deposits and withdrawals.',
     'Create a BankAccount class initialized with account_holder and initial_balance. Prevent negative initial balances. Implement deposit(amount) and withdraw(amount) raising ValueError on invalid or exceeding values.',
     'Standard commands: deposit <amount>, withdraw <amount>, balance',
     'Print balance after operations',
     'balance >= 0, amount > 0',
     '[{"input": "100\ndeposit 50\nbalance", "output": "150.0\n150.0", "explanation": "Initial balance 100 + 50 = 150"}]'::jsonb,
     'Encapsulation', 'Object-Oriented Programming', 'EASY',
     '{"python": "class BankAccount:\n    def __init__(self, account_holder: str, initial_balance: float = 0.0):\n        if initial_balance < 0:\n            raise ValueError(\"Initial balance cannot be negative\")\n        self.account_holder = account_holder\n        self.balance = float(initial_balance)\n\n    def deposit(self, amount: float) -> float:\n        if amount <= 0:\n            raise ValueError(\"Deposit amount must be positive\")\n        self.balance += amount\n        return self.balance\n\n    def withdraw(self, amount: float) -> float:\n        if amount <= 0:\n            raise ValueError(\"Withdraw amount must be positive\")\n        if amount > self.balance:\n            raise ValueError(\"Insufficient balance\")\n        self.balance -= amount\n        return self.balance\n\n    def get_balance(self) -> float:\n        return self.balance\n"}'::jsonb
    )
ON CONFLICT (id) DO NOTHING;

SELECT setval('coding_problems_id_seq', (SELECT MAX(id) FROM coding_problems));

-- 8. Test Cases for Problem 1
INSERT INTO coding_test_cases (id, problem_id, input, expected_output, is_hidden, explanation)
VALUES 
    (1, 1, '100\ndeposit 50\nbalance', '150.0\n150.0', FALSE, 'Tests valid deposit operation'),
    (2, 1, '200\nwithdraw 50\nbalance', '150.0\n150.0', FALSE, 'Tests valid withdrawal operation'),
    (3, 1, '500\ndeposit 250\nwithdraw 100\nbalance', '750.0\n650.0\n650.0', TRUE, 'Hidden test case verifying multi-step state mutations')
ON CONFLICT (id) DO NOTHING;

SELECT setval('coding_test_cases_id_seq', (SELECT MAX(id) FROM coding_test_cases));

-- Finished setup notification
SELECT 'Supabase PostgreSQL schema and seed data initialized successfully!' AS result;
