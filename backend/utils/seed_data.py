from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from backend.models.user import User, UserRole
from backend.models.course import Course, Module
from backend.models.concept import Concept, ConceptPrerequisite
from backend.models.question import Question, Attempt
from backend.models.explanation import ExplanationQuestion, ExplanationAnswer
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.coding import CodingProblem, TestCase, CodingSubmission
from backend.models.session import Session as CodingSession, SessionEvent, CodeRevision
from backend.models.integrity import IntegritySignal
from backend.utils.security import hash_password

def seed_database(db: Session):
    existing_user = db.query(User).first()
    if existing_user:
        prob = db.query(CodingProblem).first()
        if not prob:
            student_a = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
            student_b = db.query(User).filter(User.email == "student.b@adaptive.edu").first()
            if student_a and student_b:
                seed_coding_and_integrity(db, student_a, student_b)
        seed_phase4_assessments_and_submissions(db)
        return

    print("[Seed Phase 2] Seeding initial database for Adaptive Learning & AI...")

    # 1. Demo Users
    trainer = User(
        name="Dr. Alan Turing",
        email="trainer@adaptive.edu",
        password_hash=hash_password("trainer123"),
        role=UserRole.TRAINER.value
    )
    student_a = User(
        name="Alice Walker (Student A)",
        email="student.a@adaptive.edu",
        password_hash=hash_password("student123"),
        role=UserRole.STUDENT.value
    )
    student_b = User(
        name="Bob Martinez (Student B)",
        email="student.b@adaptive.edu",
        password_hash=hash_password("student123"),
        role=UserRole.STUDENT.value
    )
    db.add_all([trainer, student_a, student_b])
    db.commit()
    db.refresh(trainer)
    db.refresh(student_a)
    db.refresh(student_b)

    # 2. Course: Object Oriented Programming
    course = Course(
        title="Object Oriented Programming",
        description="Mastery-based curriculum covering foundational programming blocks, encapsulation, inheritance hierarchies, runtime polymorphism, and dependency injection.",
        created_by=trainer.id
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    # 3. Five Modules as specified in Phase 2
    m1 = Module(course_id=course.id, title="Programming Basics", description="Variables, control structures, and procedural execution.", order_index=1)
    m2 = Module(course_id=course.id, title="Classes and Objects", description="State encapsulation, instantiation, and constructors.", order_index=2)
    m3 = Module(course_id=course.id, title="Inheritance", description="Subtyping, code reuse, and method overriding.", order_index=3)
    m4 = Module(course_id=course.id, title="Polymorphism", description="Dynamic dispatch, interfaces, and contract abstraction.", order_index=4)
    m5 = Module(course_id=course.id, title="Dependency Injection", description="Inversion of control and decoupling component creation.", order_index=5)

    db.add_all([m1, m2, m3, m4, m5])
    db.commit()
    db.refresh(m1)
    db.refresh(m2)
    db.refresh(m3)
    db.refresh(m4)
    db.refresh(m5)

    # 4. Concepts along the requested DAG:
    # Programming Basics -> Classes -> Objects -> Constructors -> Inheritance -> Polymorphism -> Dependency Injection
    c_basics = Concept(module_id=m1.id, name="Programming Basics", description="Core computational variables, logic branching, and procedural primitives.", difficulty="EASY", order_index=1)
    c_classes = Concept(module_id=m2.id, name="Classes", description="Class templates, member attributes, methods, and data encapsulation.", difficulty="EASY", order_index=2)
    c_objects = Concept(module_id=m2.id, name="Objects", description="Memory allocation, runtime identity, and instance state management.", difficulty="EASY", order_index=3)
    c_constructors = Concept(module_id=m2.id, name="Constructors", description="Initialization routines, invariant enforcement, and default parameters.", difficulty="MEDIUM", order_index=4)
    c_inheritance = Concept(module_id=m3.id, name="Inheritance", description="IS-A hierarchies, parent method delegation, and subclass specialization.", difficulty="MEDIUM", order_index=5)
    c_polymorphism = Concept(module_id=m4.id, name="Polymorphism", description="Dynamic dispatch tables, duck typing, and uniform interface handling.", difficulty="MEDIUM", order_index=6)
    c_di = Concept(module_id=m5.id, name="Dependency Injection", description="Inversion of Control (IoC), constructor injection, and decoupled design.", difficulty="HARD", order_index=7)

    db.add_all([c_basics, c_classes, c_objects, c_constructors, c_inheritance, c_polymorphism, c_di])
    db.commit()
    for c in [c_basics, c_classes, c_objects, c_constructors, c_inheritance, c_polymorphism, c_di]:
        db.refresh(c)

    # 5. Build Prerequisite Backbone:
    # Programming Basics -> Classes -> Objects -> Constructors -> Inheritance -> Polymorphism -> Dependency Injection
    prereqs = [
        (c_classes.id, c_basics.id),
        (c_objects.id, c_classes.id),
        (c_constructors.id, c_objects.id),
        (c_inheritance.id, c_constructors.id),
        (c_polymorphism.id, c_inheritance.id),
        (c_di.id, c_polymorphism.id)
    ]
    for cid, pid in prereqs:
        cp = ConceptPrerequisite(concept_id=cid, prerequisite_id=pid)
        db.add(cp)
    db.commit()

    # 6. Comprehensive Questions Pool (MCQ, TRUE_FALSE, SHORT_ANSWER across EASY, MEDIUM, HARD)
    raw_questions = [
        # --- Programming Basics ---
        {
            "concept": c_basics,
            "type": "MCQ",
            "text": "What is the primary role of a variable in programming?",
            "difficulty": "EASY",
            "options": ["A named storage location in memory holding a value", "A physical cable connecting CPU to RAM", "An operating system process scheduler", "A permanent hardware chip"],
            "answer": "A named storage location in memory holding a value",
            "explanation": "Variables reserve space in system memory to store mutable or immutable runtime state."
        },
        {
            "concept": c_basics,
            "type": "TRUE_FALSE",
            "text": "In Python, a function must always contain at least one return statement to be valid.",
            "difficulty": "EASY",
            "options": ["True", "False"],
            "answer": "False",
            "explanation": "Functions without an explicit return statement implicitly return None upon reaching the end."
        },
        {
            "concept": c_basics,
            "type": "SHORT_ANSWER",
            "text": "Which boolean logical operator returns True only when both operands are truthy?",
            "difficulty": "EASY",
            "options": ["and", "AND", "&&"],
            "answer": "and",
            "explanation": "The 'and' operator requires both conditions to evaluate to True."
        },
        {
            "concept": c_basics,
            "type": "MCQ",
            "text": "What is the algorithmic time complexity of accessing an element in an array by its index?",
            "difficulty": "MEDIUM",
            "options": ["O(1) constant time", "O(n) linear time", "O(log n) logarithmic time", "O(n^2) quadratic time"],
            "answer": "O(1) constant time",
            "explanation": "Direct indexing calculates memory offset in O(1) time."
        },
        {
            "concept": c_basics,
            "type": "MCQ",
            "text": "What occurs when recursion does not terminate due to a missing base condition?",
            "difficulty": "HARD",
            "options": ["Call stack overflow exception", "Database table deadlock", "Hard drive file corruption", "Instant reboot of the host machine"],
            "answer": "Call stack overflow exception",
            "explanation": "Each recursive call consumes a stack frame; without a base case, recursion exhausts allocated stack memory."
        },

        # --- Classes ---
        {
            "concept": c_classes,
            "type": "MCQ",
            "text": "Which statement best describes a Class in Object-Oriented Programming?",
            "difficulty": "EASY",
            "options": ["A blueprint or template defining the structure and behavior of objects", "An allocated instance existing in runtime heap memory", "A network socket connection", "A compiled machine code instruction"],
            "answer": "A blueprint or template defining the structure and behavior of objects",
            "explanation": "A class serves as the architectural schema from which concrete object instances are manufactured."
        },
        {
            "concept": c_classes,
            "type": "TRUE_FALSE",
            "text": "Encapsulation prevents unauthorized direct modification of an object's internal fields from external code.",
            "difficulty": "EASY",
            "options": ["True", "False"],
            "answer": "True",
            "explanation": "Encapsulation bundles state with methods and provides controlled access modifiers or getters/setters."
        },
        {
            "concept": c_classes,
            "type": "SHORT_ANSWER",
            "text": "What parameter is conventionally passed as the first argument to instance methods in Python classes?",
            "difficulty": "EASY",
            "options": ["self", "this", "cls"],
            "answer": "self",
            "explanation": "'self' references the current instance executing the method."
        },
        {
            "concept": c_classes,
            "type": "MCQ",
            "text": "How do class attributes differ from instance attributes in object models?",
            "difficulty": "MEDIUM",
            "options": [
                "Class attributes are shared across all instances; instance attributes belong exclusively to one object",
                "Class attributes can only hold numbers; instance attributes can hold text",
                "Instance attributes cannot be modified after creation",
                "There is no difference in memory or scope"
            ],
            "answer": "Class attributes are shared across all instances; instance attributes belong exclusively to one object",
            "explanation": "Class variables reside on the class object, while instance variables are bound to individual instance dictionaries."
        },
        {
            "concept": c_classes,
            "type": "MCQ",
            "text": "What is the primary benefit of declaring properties with getters and setters instead of public raw variables?",
            "difficulty": "HARD",
            "options": [
                "It enables data validation and lazy calculation without breaking the public interface contract",
                "It forces the compiler to run twice as fast",
                "It automatically encrypts the data using AES-256",
                "It prevents garbage collection from ever running"
            ],
            "answer": "It enables data validation and lazy calculation without breaking the public interface contract",
            "explanation": "Encapsulating access via properties allows enforcing validation invariants without changing caller syntax."
        },

        # --- Objects ---
        {
            "concept": c_objects,
            "type": "MCQ",
            "text": "What is an Object in relation to a Class?",
            "difficulty": "EASY",
            "options": [
                "An instantiated entity with state and identity in memory",
                "A syntax keyword reserved by the compiler",
                "An abstract flowchart drawn by a software architect",
                "A file stored permanently on a magnetic disk"
            ],
            "answer": "An instantiated entity with state and identity in memory",
            "explanation": "An object is a live instance of a class occupying memory."
        },
        {
            "concept": c_objects,
            "type": "TRUE_FALSE",
            "text": "Two distinct objects created from the same class with identical attribute values always share the same memory reference.",
            "difficulty": "MEDIUM",
            "options": ["True", "False"],
            "answer": "False",
            "explanation": "Each object instantiation allocates distinct heap memory; equality (==) does not mean identity (is)."
        },
        {
            "concept": c_objects,
            "type": "SHORT_ANSWER",
            "text": "Which Python built-in function returns the unique integer memory identifier of an active object?",
            "difficulty": "MEDIUM",
            "options": ["id", "id()", "identity"],
            "answer": "id",
            "explanation": "The id() function returns the identity (memory address in CPython) of the object."
        },
        {
            "concept": c_objects,
            "type": "MCQ",
            "text": "What mechanism automatically reclaims heap memory when an object has zero active references?",
            "difficulty": "MEDIUM",
            "options": ["Garbage Collector", "Bytecode Decompiler", "Dynamic Linker", "Process Mutex"],
            "answer": "Garbage Collector",
            "explanation": "Garbage collection tracks reference counts and cyclical graphs to free unreferenced memory."
        },
        {
            "concept": c_objects,
            "type": "MCQ",
            "text": "What occurs when attempting to modify an attribute of an immutable object such as a tuple or frozen dataclass?",
            "difficulty": "HARD",
            "options": [
                "A TypeError or runtime exception is raised preventing mutation",
                "The operating system reboots",
                "The entire variable is silently set to zero",
                "The CPU cache is invalidated and rebuilt"
            ],
            "answer": "A TypeError or runtime exception is raised preventing mutation",
            "explanation": "Immutable objects disallow in-place field alteration, safeguarding against unintended side-effects."
        },

        # --- Constructors ---
        {
            "concept": c_constructors,
            "type": "MCQ",
            "text": "What is the primary function of a Constructor in OOP?",
            "difficulty": "EASY",
            "options": [
                "To initialize the newly created object's state and validate initial invariants",
                "To delete the class from the source code",
                "To compile the Python script into a binary executable",
                "To establish an internet TCP connection"
            ],
            "answer": "To initialize the newly created object's state and validate initial invariants",
            "explanation": "Constructors set initial attribute values and verify validity."
        },
        {
            "concept": c_constructors,
            "type": "SHORT_ANSWER",
            "text": "What is the standard constructor initializer method name in Python classes?",
            "difficulty": "EASY",
            "options": ["__init__", "init", "__init__()"],
            "answer": "__init__",
            "explanation": "__init__ is called immediately after instance creation."
        },
        {
            "concept": c_constructors,
            "type": "TRUE_FALSE",
            "text": "In Python, a constructor can return an explicit custom string or integer value instead of the instance.",
            "difficulty": "MEDIUM",
            "options": ["True", "False"],
            "answer": "False",
            "explanation": "__init__ must return None; returning any other value causes a TypeError."
        },
        {
            "concept": c_constructors,
            "type": "MCQ",
            "text": "How should a subclass constructor invoke its parent class constructor in Python 3?",
            "difficulty": "MEDIUM",
            "options": ["super().__init__(*args, **kwargs)", "parent.init(self)", "this.super()", "Base.create()"],
            "answer": "super().__init__(*args, **kwargs)",
            "explanation": "super().__init__() calls the parent initializer according to Method Resolution Order (MRO)."
        },
        {
            "concept": c_constructors,
            "type": "MCQ",
            "text": "What is the distinction between __new__ and __init__ in Python's object lifecycle?",
            "difficulty": "HARD",
            "options": [
                "__new__ is the allocator returning the new instance; __init__ initializes that instance's attributes",
                "__init__ allocates memory; __new__ is called only during garbage collection",
                "__new__ only works for integers and strings",
                "There is no difference"
            ],
            "answer": "__new__ is the allocator returning the new instance; __init__ initializes that instance's attributes",
            "explanation": "__new__ is a static allocator method returning an instance; __init__ receives that instance as self to populate fields."
        },

        # --- Inheritance ---
        {
            "concept": c_inheritance,
            "type": "MCQ",
            "text": "Which fundamental relationship type is modeled by Class Inheritance?",
            "difficulty": "EASY",
            "options": ["IS-A relationship (e.g. Dog is an Animal)", "HAS-A relationship (e.g. Car has an Engine)", "USES-A relationship", "RUNS-ON relationship"],
            "answer": "IS-A relationship (e.g. Dog is an Animal)",
            "explanation": "Inheritance establishes subtype taxonomy; composition establishes HAS-A."
        },
        {
            "concept": c_inheritance,
            "type": "TRUE_FALSE",
            "text": "Method Overriding allows a subclass to provide a specific implementation of a method already defined in its superclass.",
            "difficulty": "EASY",
            "options": ["True", "False"],
            "answer": "True",
            "explanation": "Overriding replaces or extends parent class behavior for the specialized subclass."
        },
        {
            "concept": c_inheritance,
            "type": "SHORT_ANSWER",
            "text": "What principle in SOLID states that objects of a superclass should be replaceable with objects of a subclass without breaking correctness?",
            "difficulty": "MEDIUM",
            "options": ["Liskov Substitution Principle", "LSP", "Liskov", "liskov substitution"],
            "answer": "Liskov Substitution Principle",
            "explanation": "LSP ensures subtype behavioral consistency."
        },
        {
            "concept": c_inheritance,
            "type": "MCQ",
            "text": "What design guideline suggests using object composition instead of deep class inheritance hierarchies?",
            "difficulty": "MEDIUM",
            "options": ["Favor composition over inheritance", "Always inherit at least five levels deep", "Avoid using methods in subclasses", "Make all variables public"],
            "answer": "Favor composition over inheritance",
            "explanation": "Composition offers loose coupling and runtime flexibility compared to brittle inheritance hierarchies."
        },
        {
            "concept": c_inheritance,
            "type": "MCQ",
            "text": "In Python multiple inheritance, which algorithm determines the deterministic sequence of classes searched for an attribute?",
            "difficulty": "HARD",
            "options": ["C3 Linearization algorithm (MRO)", "Breadth-First Search with pruning", "Dijkstra's shortest path", "Randomized lookup table"],
            "answer": "C3 Linearization algorithm (MRO)",
            "explanation": "Python computes Method Resolution Order using the C3 Linearization algorithm."
        },

        # --- Polymorphism ---
        {
            "concept": c_polymorphism,
            "type": "MCQ",
            "text": "What is Polymorphism in Object-Oriented Design?",
            "difficulty": "EASY",
            "options": [
                "The ability of different classes to respond to the same method invocation in their own specific way",
                "Converting integer numbers to binary strings",
                "Encrypting source code files on disk",
                "Running multiple programs on different CPU cores simultaneously"
            ],
            "answer": "The ability of different classes to respond to the same method invocation in their own specific way",
            "explanation": "Polymorphism enables treating disparate concrete types uniformly through a common protocol."
        },
        {
            "concept": c_polymorphism,
            "type": "TRUE_FALSE",
            "text": "Duck Typing means Python checks an object's suitability based on the presence of methods and properties, rather than its explicit inheritance ancestry.",
            "difficulty": "EASY",
            "options": ["True", "False"],
            "answer": "True",
            "explanation": "'If it walks like a duck and quacks like a duck, it's a duck' defines dynamic polymorphism."
        },
        {
            "concept": c_polymorphism,
            "type": "SHORT_ANSWER",
            "text": "What standard Python library module is imported to define Abstract Base Classes and abstract methods?",
            "difficulty": "MEDIUM",
            "options": ["abc", "ABC", "abstract"],
            "answer": "abc",
            "explanation": "The 'abc' module provides the ABC base and @abstractmethod decorator."
        },
        {
            "concept": c_polymorphism,
            "type": "MCQ",
            "text": "What is Dynamic Dispatch (Runtime Polymorphism)?",
            "difficulty": "MEDIUM",
            "options": [
                "Selecting which polymorphic method implementation to execute at runtime based on actual object type",
                "Sending HTTP requests to multiple remote cloud servers",
                "Generating random test data at compile time",
                "Switching between CPU threads"
            ],
            "answer": "Selecting which polymorphic method implementation to execute at runtime based on actual object type",
            "explanation": "Dynamic dispatch resolves method addresses at runtime via virtual method tables or dynamic attribute lookups."
        },
        {
            "concept": c_polymorphism,
            "type": "MCQ",
            "text": "In compiled languages like C++, what internal data structure is generated by the compiler to implement dynamic dispatch for virtual functions?",
            "difficulty": "HARD",
            "options": ["vtable (virtual method table)", "Abstract Syntax Tree", "B-Tree index", "Circular doubly linked list"],
            "answer": "vtable (virtual method table)",
            "explanation": "A vtable contains pointers to virtual functions corresponding to the actual runtime class."
        },

        # --- Dependency Injection ---
        {
            "concept": c_di,
            "type": "MCQ",
            "text": "What is the core architectural objective of Dependency Injection (DI)?",
            "difficulty": "MEDIUM",
            "options": [
                "To invert control so objects receive their dependencies from the outside rather than creating them directly internally",
                "To inject malicious SQL queries into databases",
                "To force all classes to be global singletons",
                "To eliminate writing unit tests"
            ],
            "answer": "To invert control so objects receive their dependencies from the outside rather than creating them directly internally",
            "explanation": "DI decouples creation of dependencies from usage, drastically improving modularity and testability."
        },
        {
            "concept": c_di,
            "type": "TRUE_FALSE",
            "text": "Dependency Injection makes unit testing significantly easier because external services (databases, APIs) can be substituted with mock objects.",
            "difficulty": "EASY",
            "options": ["True", "False"],
            "answer": "True",
            "explanation": "Mock dependencies can easily be passed into class constructors during testing."
        },
        {
            "concept": c_di,
            "type": "SHORT_ANSWER",
            "text": "What broader architectural principle does Dependency Injection implement, often abbreviated as IoC?",
            "difficulty": "EASY",
            "options": ["Inversion of Control", "inversion of control", "IoC", "IOC"],
            "answer": "Inversion of Control",
            "explanation": "Inversion of Control (IoC) delegates control flow and dependency management to an external coordinator."
        },
        {
            "concept": c_di,
            "type": "MCQ",
            "text": "Which form of Dependency Injection is generally regarded as best practice for enforcing non-optional dependencies?",
            "difficulty": "MEDIUM",
            "options": ["Constructor Injection", "Setter Injection", "Field / Reflection Injection", "Global Variable Locator"],
            "answer": "Constructor Injection",
            "explanation": "Constructor injection makes required dependencies explicit and guarantees the object is never partially initialized."
        },
        {
            "concept": c_di,
            "type": "MCQ",
            "text": "The Dependency Inversion Principle (the 'D' in SOLID) mandates that high-level modules and low-level modules should both depend upon what?",
            "difficulty": "HARD",
            "options": ["Abstractions (Interfaces or abstract contracts)", "Concrete low-level driver implementations", "Global singleton variables", "Operating system file paths"],
            "answer": "Abstractions (Interfaces or abstract contracts)",
            "explanation": "High-level policy should not depend on low-level detail; both should depend on abstract contracts."
        }
    ]

    for q in raw_questions:
        q_obj = Question(
            concept_id=q["concept"].id,
            question_text=q["text"],
            question_type=q["type"],
            difficulty=q["difficulty"],
            options=q.get("options"),
            correct_answer=q["answer"],
            explanation=q.get("explanation"),
            created_at=datetime.now(timezone.utc)
        )
        db.add(q_obj)
    db.commit()

    # 7. Student-Specific Adaptation Demo Baseline (Section 9):
    # Student A:
    # - Programming Basics: 95
    # - Classes: 90
    # - Objects: 85
    # - Constructors: 40  <-- WEAKEST ELIGIBLE PREREQUISITE!
    # - Inheritance: 20
    # - Polymorphism: 10
    # - DI: 0
    # Next recommended target for Student A MUST BE Constructors!
    student_a_scores = [
        (c_basics.id, 95.0, 10, 9),
        (c_classes.id, 90.0, 10, 9),
        (c_objects.id, 85.0, 8, 7),
        (c_constructors.id, 40.0, 5, 2),
        (c_inheritance.id, 20.0, 4, 1),
        (c_polymorphism.id, 10.0, 2, 0),
        (c_di.id, 0.0, 0, 0)
    ]
    for cid, score, att, corr in student_a_scores:
        sm = StudentMastery(
            student_id=student_a.id,
            concept_id=cid,
            mastery_score=score,
            attempts=att,
            correct_attempts=corr,
            last_attempt_at=datetime.now(timezone.utc)
        )
        mh = MasteryHistory(
            student_id=student_a.id,
            concept_id=cid,
            mastery_score=score,
            change_amount=score,
            reason="Diagnostic Initial Assessment",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(sm)
        db.add(mh)

    # Student B:
    # - Programming Basics: 80
    # - Classes: 40  <-- WEAKEST ELIGIBLE PREREQUISITE (Prereq for Objects & Constructors)!
    # - Objects: 30
    # - Constructors: 20
    # - Inheritance: 10
    # - Polymorphism: 5
    # - DI: 0
    # Next recommended target for Student B MUST BE Classes!
    student_b_scores = [
        (c_basics.id, 80.0, 8, 6),
        (c_classes.id, 40.0, 6, 2),
        (c_objects.id, 30.0, 4, 1),
        (c_constructors.id, 20.0, 3, 0),
        (c_inheritance.id, 10.0, 2, 0),
        (c_polymorphism.id, 5.0, 1, 0),
        (c_di.id, 0.0, 0, 0)
    ]
    for cid, score, att, corr in student_b_scores:
        sm = StudentMastery(
            student_id=student_b.id,
            concept_id=cid,
            mastery_score=score,
            attempts=att,
            correct_attempts=corr,
            last_attempt_at=datetime.now(timezone.utc)
        )
        mh = MasteryHistory(
            student_id=student_b.id,
            concept_id=cid,
            mastery_score=score,
            change_amount=score,
            reason="Diagnostic Initial Assessment",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(sm)
        db.add(mh)

    db.commit()
    seed_coding_and_integrity(db, student_a, student_b)

def seed_coding_and_integrity(db: Session, student_a, student_b):
    if db.query(CodingProblem).count() > 0:
        return

    # 8. Seed Coding Problem: "Encapsulated Bank Account"
    prob = CodingProblem(
        title="Encapsulated Bank Account",
        description="""Implement an object-oriented BankAccount class in Python or C++ that encapsulates balance state and validates operational invariants:

Requirements:
1. `__init__(self, account_holder: str, initial_balance: float = 0.0)`
   - Raises `ValueError` if `initial_balance < 0`.
2. `deposit(self, amount: float) -> float`
   - Raises `ValueError` if `amount <= 0`.
   - Returns updated balance.
3. `withdraw(self, amount: float) -> float`
   - Raises `ValueError` if `amount <= 0` or `amount > balance`.
   - Returns updated balance.
4. `get_balance(self) -> float`
   - Returns current balance.

Input Format for Sandbox Execution:
Line 1: Initial balance (float)
Subsequent Lines: Commands e.g. "deposit 50.0", "withdraw 20.0", "balance"
""",
        difficulty="MEDIUM",
        allowed_languages=["python", "cpp"],
        time_limit=2.0,
        memory_limit=128
    )
    db.add(prob)
    db.commit()
    db.refresh(prob)

    # Test cases: 2 visible, 2 hidden
    tc1 = TestCase(problem_id=prob.id, input="100.0\ndeposit 50.0\nwithdraw 30.0\nbalance\n", expected_output="150.0\n120.0\n120.0", is_hidden=False)
    tc2 = TestCase(problem_id=prob.id, input="0.0\ndeposit 10.0\nbalance\n", expected_output="10.0\n10.0", is_hidden=False)
    tc3 = TestCase(problem_id=prob.id, input="500.0\nwithdraw 100.0\nwithdraw 200.0\nbalance\n", expected_output="400.0\n200.0\n200.0", is_hidden=True)
    tc4 = TestCase(problem_id=prob.id, input="25.5\ndeposit 74.5\nwithdraw 50.0\nbalance\n", expected_output="100.0\n50.0\n50.0", is_hidden=True)
    db.add_all([tc1, tc2, tc3, tc4])
    db.commit()

    # 9. Seed Demo Assessment Sessions for Coding Integrity Dashboard
    t_base = datetime.now(timezone.utc) - timedelta(hours=2)

    # Session 1: Student A (Alice) -> Large paste observed (REVIEW_SUGGESTED)
    sess_a = CodingSession(
        student_id=student_a.id,
        assessment_id=prob.id,
        started_at=t_base,
        ended_at=t_base + timedelta(minutes=12),
        overall_review_status="REVIEW_SUGGESTED",
        is_reviewed=False
    )
    db.add(sess_a)
    db.commit()
    db.refresh(sess_a)

    ev_a_start = SessionEvent(session_id=sess_a.id, student_id=student_a.id, assessment_id=prob.id, event_type="SESSION_START", server_timestamp=t_base, timestamp=t_base, classification="Session lifecycle", review_status="NORMAL_RHYTHM")
    ev_a_type1 = SessionEvent(session_id=sess_a.id, student_id=student_a.id, assessment_id=prob.id, event_type="TYPE", server_timestamp=t_base + timedelta(seconds=15), timestamp=t_base + timedelta(seconds=15), inserted_character_count=18, code_location={"start_line": 1, "start_column": 1, "end_line": 1, "end_column": 19}, duration=1.2, classification="Normal typing", review_status="NORMAL_RHYTHM")
    ev_a_type2 = SessionEvent(session_id=sess_a.id, student_id=student_a.id, assessment_id=prob.id, event_type="TYPE", server_timestamp=t_base + timedelta(seconds=30), timestamp=t_base + timedelta(seconds=30), inserted_character_count=24, code_location={"start_line": 2, "start_column": 5, "end_line": 2, "end_column": 29}, duration=0.9, classification="Normal typing", review_status="NORMAL_RHYTHM")
    ev_a_run1 = SessionEvent(session_id=sess_a.id, student_id=student_a.id, assessment_id=prob.id, event_type="RUN", server_timestamp=t_base + timedelta(seconds=60), timestamp=t_base + timedelta(seconds=60), classification="Code execution", review_status="NORMAL_RHYTHM")
    ev_a_edit = SessionEvent(session_id=sess_a.id, student_id=student_a.id, assessment_id=prob.id, event_type="EDIT_AFTER_RUN", server_timestamp=t_base + timedelta(seconds=90), timestamp=t_base + timedelta(seconds=90), inserted_character_count=15, code_location={"start_line": 3, "start_column": 9, "end_line": 3, "end_column": 24}, classification="Iterative edit after run", review_status="NORMAL_RHYTHM")
    
    # Large Paste Event (+1,240 characters)
    ev_a_paste = SessionEvent(
        session_id=sess_a.id,
        student_id=student_a.id,
        assessment_id=prob.id,
        event_type="PASTE",
        server_timestamp=t_base + timedelta(seconds=140),
        timestamp=t_base + timedelta(seconds=140),
        inserted_character_count=1240,
        code_location={"start_line": 12, "start_column": 1, "end_line": 48, "end_column": 20},
        duration=0.1,
        classification="Large paste",
        review_status="REVIEW_SUGGESTED",
        classification_reason="Observed paste event inserted substantial content (1,240 characters).",
        event_metadata={"charCount": 1240, "preview": "class BankAccount:\n    def __init__(self..."}
    )
    ev_a_submit = SessionEvent(session_id=sess_a.id, student_id=student_a.id, assessment_id=prob.id, event_type="SUBMIT", server_timestamp=t_base + timedelta(seconds=180), timestamp=t_base + timedelta(seconds=180), classification="Code submission", review_status="NORMAL_RHYTHM")
    
    db.add_all([ev_a_start, ev_a_type1, ev_a_type2, ev_a_run1, ev_a_edit, ev_a_paste, ev_a_submit])
    db.commit()

    # Integrity Signal pointing directly to ev_a_paste
    sig_a = IntegritySignal(
        session_id=sess_a.id,
        event_id=ev_a_paste.id,
        signal_type="LARGE_PASTE",
        severity="HIGH",
        description="Evidence for review: Large code paste of 1,240 characters detected at 14:12:20.",
        timestamp=ev_a_paste.timestamp,
        review_status="PENDING"
    )
    db.add(sig_a)

    # Session 2: Student B (Bob) -> Consistent rhythm (NORMAL_RHYTHM)
    t_b_base = datetime.now(timezone.utc) - timedelta(hours=1)
    sess_b = CodingSession(
        student_id=student_b.id,
        assessment_id=prob.id,
        started_at=t_b_base,
        ended_at=t_b_base + timedelta(minutes=15),
        overall_review_status="NORMAL_RHYTHM",
        is_reviewed=False
    )
    db.add(sess_b)
    db.commit()
    db.refresh(sess_b)

    b_events = []
    b_events.append(SessionEvent(session_id=sess_b.id, student_id=student_b.id, assessment_id=prob.id, event_type="SESSION_START", server_timestamp=t_b_base, timestamp=t_b_base, classification="Session lifecycle", review_status="NORMAL_RHYTHM"))
    for i in range(10):
        t_ev = t_b_base + timedelta(seconds=10 + i * 15)
        b_events.append(SessionEvent(
            session_id=sess_b.id,
            student_id=student_b.id,
            assessment_id=prob.id,
            event_type="TYPE",
            server_timestamp=t_ev,
            timestamp=t_ev,
            inserted_character_count=14,
            code_location={"start_line": i + 1, "start_column": 1, "end_line": i + 1, "end_column": 15},
            duration=0.8,
            classification="Normal typing",
            review_status="NORMAL_RHYTHM",
            classification_reason="Typing rhythm consistent with observed activity."
        ))
    b_events.append(SessionEvent(session_id=sess_b.id, student_id=student_b.id, assessment_id=prob.id, event_type="RUN", server_timestamp=t_b_base + timedelta(seconds=200), timestamp=t_b_base + timedelta(seconds=200), classification="Code execution", review_status="NORMAL_RHYTHM"))
    b_events.append(SessionEvent(session_id=sess_b.id, student_id=student_b.id, assessment_id=prob.id, event_type="SUBMIT", server_timestamp=t_b_base + timedelta(seconds=240), timestamp=t_b_base + timedelta(seconds=240), classification="Code submission", review_status="NORMAL_RHYTHM"))
    db.add_all(b_events)

    # Session 3: Incomplete / brief session (INSUFFICIENT_DATA)
    sess_c = CodingSession(
        student_id=student_a.id,
        assessment_id=prob.id,
        started_at=datetime.now(timezone.utc) - timedelta(minutes=20),
        ended_at=datetime.now(timezone.utc) - timedelta(minutes=19),
        overall_review_status="INSUFFICIENT_DATA",
        is_reviewed=False
    )
    db.add(sess_c)
    db.commit()
    db.refresh(sess_c)

    c_events = [
        SessionEvent(session_id=sess_c.id, student_id=student_a.id, assessment_id=prob.id, event_type="SESSION_START", server_timestamp=sess_c.started_at, timestamp=sess_c.started_at, classification="Session lifecycle", review_status="NORMAL_RHYTHM"),
        SessionEvent(session_id=sess_c.id, student_id=student_a.id, assessment_id=prob.id, event_type="TYPE", server_timestamp=sess_c.started_at + timedelta(seconds=5), timestamp=sess_c.started_at + timedelta(seconds=5), inserted_character_count=6, duration=0.4, classification="Normal typing", review_status="NORMAL_RHYTHM"),
        SessionEvent(session_id=sess_c.id, student_id=student_a.id, assessment_id=prob.id, event_type="SESSION_END", server_timestamp=sess_c.ended_at, timestamp=sess_c.ended_at, classification="Session lifecycle", review_status="NORMAL_RHYTHM")
    ]
    db.add_all(c_events)
    db.commit()

    print("[Seed Phase 3] Successfully seeded Course, 5 Modules, 7 Concepts, 35 Questions, Coding Problem & Test Cases, and 3 Demo Integrity Sessions.")
    seed_phase4_assessments_and_submissions(db)

def seed_phase4_assessments_and_submissions(db: Session):
    student_a = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
    student_b = db.query(User).filter(User.email == "student.b@adaptive.edu").first()
    prob = db.query(CodingProblem).first()

    if not student_a or not student_b or not prob:
        return

    now = datetime.now(timezone.utc)

    # 1. Seed Submissions & Viva Voce Evaluations if absent
    if db.query(CodingSubmission).count() == 0:
        sub_a1 = CodingSubmission(
            student_id=student_a.id,
            problem_id=prob.id,
            language="python",
            source_code='''class BankAccount:
    def __init__(self, account_holder: str, initial_balance: float = 0.0):
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self._holder = account_holder
        self._balance = initial_balance

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self._balance += amount
        return self._balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0 or amount > self._balance:
            raise ValueError("Invalid withdrawal amount")
        self._balance -= amount
        return self._balance

    def get_balance(self) -> float:
        return self._balance
''',
            status="PASSED",
            score=100.0,
            execution_time=0.045,
            memory_used=14.2,
            created_at=now - timedelta(hours=3)
        )
        db.add(sub_a1)
        db.commit()
        db.refresh(sub_a1)

        # Attach viva questions and evaluations for sub_a1
        vq1 = ExplanationQuestion(
            submission_id=sub_a1.id,
            question="How does your implementation enforce encapsulation of the account balance?",
            expected_concept="Encapsulation and private state mutation"
        )
        vq2 = ExplanationQuestion(
            submission_id=sub_a1.id,
            question="What happens in memory and state when an invalid withdrawal is attempted?",
            expected_concept="Exception handling and invariant preservation"
        )
        db.add_all([vq1, vq2])
        db.commit()
        db.refresh(vq1)
        db.refresh(vq2)

        ans1 = ExplanationAnswer(
            explanation_question_id=vq1.id,
            student_answer="I prefixed _balance with an underscore to designate it as an internal encapsulated attribute and only mutate it through validated deposit/withdraw methods.",
            evaluation="Strong technical grasp of state encapsulation and boundary defense.",
            score=9.5
        )
        ans2 = ExplanationAnswer(
            explanation_question_id=vq2.id,
            student_answer="A ValueError is raised before any mutation occurs, ensuring that the balance remains invariant and transactionally consistent.",
            evaluation="Clear explanation of exception handling preserving class state.",
            score=9.0
        )
        db.add_all([ans1, ans2])

        # Student B submission
        sub_b1 = CodingSubmission(
            student_id=student_b.id,
            problem_id=prob.id,
            language="python",
            source_code='''class BankAccount:
    def __init__(self, holder, balance=0):
        self.holder = holder
        self.balance = balance
    def deposit(self, amt):
        self.balance += amt
        return self.balance
    def withdraw(self, amt):
        if amt <= self.balance:
            self.balance -= amt
        return self.balance
    def get_balance(self):
        return self.balance
''',
            status="PASSED",
            score=75.0,
            execution_time=0.048,
            memory_used=14.1,
            created_at=now - timedelta(hours=6)
        )
        db.add(sub_b1)
        db.commit()
        db.refresh(sub_b1)

        vq_b1 = ExplanationQuestion(
            submission_id=sub_b1.id,
            question="Why is direct attribute access to balance risky in multi-component systems?",
            expected_concept="Encapsulation"
        )
        db.add(vq_b1)
        db.commit()
        db.refresh(vq_b1)

        ans_b1 = ExplanationAnswer(
            explanation_question_id=vq_b1.id,
            student_answer="Because external code could set balance to negative without validation.",
            evaluation="Accurate basic identification of invariant violation risk.",
            score=7.0
        )
        db.add(ans_b1)
        db.commit()

    # 2. Seed Quiz Attempts if absent
    if db.query(Attempt).count() == 0:
        questions = db.query(Question).all()
        q_map = {q.concept.name: q for q in questions if q.concept}

        attempts_list = []
        # Student A attempts (advanced in Basics, Classes, Objects, struggling on Inheritance)
        if "Classes" in q_map:
            attempts_list.append(Attempt(
                student_id=student_a.id,
                question_id=q_map["Classes"].id,
                selected_answer=q_map["Classes"].correct_answer,
                is_correct=True,
                score=1.0,
                time_taken=14.2,
                created_at=now - timedelta(days=2, hours=4)
            ))
        if "Objects" in q_map:
            attempts_list.append(Attempt(
                student_id=student_a.id,
                question_id=q_map["Objects"].id,
                selected_answer=q_map["Objects"].correct_answer,
                is_correct=True,
                score=1.0,
                time_taken=18.5,
                created_at=now - timedelta(days=1, hours=8)
            ))
        if "Constructors" in q_map:
            attempts_list.append(Attempt(
                student_id=student_a.id,
                question_id=q_map["Constructors"].id,
                selected_answer=q_map["Constructors"].correct_answer,
                is_correct=True,
                score=1.0,
                time_taken=22.0,
                created_at=now - timedelta(hours=14)
            ))
        if "Inheritance" in q_map:
            attempts_list.append(Attempt(
                student_id=student_a.id,
                question_id=q_map["Inheritance"].id,
                selected_answer="Incorrect option",
                is_correct=False,
                score=0.0,
                time_taken=28.4,
                created_at=now - timedelta(hours=2)
            ))

        # Student B attempts (good in Basics, struggling on Classes/Objects)
        if "Programming Basics" in q_map:
            attempts_list.append(Attempt(
                student_id=student_b.id,
                question_id=q_map["Programming Basics"].id,
                selected_answer=q_map["Programming Basics"].correct_answer,
                is_correct=True,
                score=1.0,
                time_taken=11.0,
                created_at=now - timedelta(days=1, hours=10)
            ))
        if "Classes" in q_map:
            attempts_list.append(Attempt(
                student_id=student_b.id,
                question_id=q_map["Classes"].id,
                selected_answer="Incorrect option",
                is_correct=False,
                score=0.0,
                time_taken=25.0,
                created_at=now - timedelta(hours=5)
            ))

        db.add_all(attempts_list)
        db.commit()

    # 3. Ensure MasteryHistory has rich progression points
    hist_count_a = db.query(MasteryHistory).filter(MasteryHistory.student_id == student_a.id).count()
    if hist_count_a < 4:
        concept_classes = db.query(Concept).filter(Concept.name == "Classes").first()
        concept_constructors = db.query(Concept).filter(Concept.name == "Constructors").first()
        cid1 = concept_classes.id if concept_classes else 2
        cid2 = concept_constructors.id if concept_constructors else 4

        progression_a = [
            MasteryHistory(student_id=student_a.id, concept_id=cid1, mastery_score=50.0, change_amount=50.0, reason="Initial Diagnostic", timestamp=now - timedelta(days=3)),
            MasteryHistory(student_id=student_a.id, concept_id=cid1, mastery_score=72.0, change_amount=22.0, reason="Correct Quiz Attempt", timestamp=now - timedelta(days=2)),
            MasteryHistory(student_id=student_a.id, concept_id=cid1, mastery_score=90.0, change_amount=18.0, reason="Advanced Concept Practice", timestamp=now - timedelta(days=1)),
            MasteryHistory(student_id=student_a.id, concept_id=cid2, mastery_score=80.0, change_amount=40.0, reason="Constructors Coding Lab", timestamp=now - timedelta(hours=12))
        ]
        db.add_all(progression_a)
        db.commit()

    print("[Seed Phase 4] Successfully ensured rich student quiz attempts, coding submissions, viva evaluations, and historical knowledge tracing.")

if __name__ == "__main__":
    from backend.database import SessionLocal
    db = SessionLocal()
    seed_database(db)
    db.close()

