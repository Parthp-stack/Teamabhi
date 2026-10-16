from sqlalchemy.orm import Session
from backend.models.user import User, UserRole
from backend.models.course import Course, Module
from backend.models.concept import Concept
from backend.models.question import Question
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.coding import CodingProblem, TestCase
from backend.utils.security import hash_password

def seed_database(db: Session):
    # Check if already seeded
    existing_user = db.query(User).first()
    if existing_user:
        return

    print("[Seed] Seeding initial database...")

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

    # 2. OOP Course and Module
    course = Course(
        title="Object-Oriented Programming & System Design",
        description="Comprehensive foundation in modern OOP paradigms, architecture design patterns, and polymorphic structures."
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    module = Module(
        course_id=course.id,
        title="OOP Core Foundations",
        description="Core conceptual blocks from classes to dependency inversion.",
        order_index=1
    )
    db.add(module)
    db.commit()
    db.refresh(module)

    # 3. Concepts
    c_classes = Concept(
        module_id=module.id,
        name="Classes",
        description="Blueprints for data structures, encapsulation of state, and method definitions."
    )
    c_objects = Concept(
        module_id=module.id,
        name="Objects",
        description="Concrete runtime instances of classes holding unique state in memory."
    )
    c_constructors = Concept(
        module_id=module.id,
        name="Constructors",
        description="Special initialization routines for establishing valid object invariants."
    )
    c_inheritance = Concept(
        module_id=module.id,
        name="Inheritance",
        description="Subtyping and code reuse mechanism establishing 'is-a' relationships."
    )
    c_polymorphism = Concept(
        module_id=module.id,
        name="Polymorphism",
        description="Dynamic dispatch and interface contracts allowing uniform treatment of disparate types."
    )
    c_di = Concept(
        module_id=module.id,
        name="Dependency Injection",
        description="Inversion of Control pattern decoupling concrete object creation from business logic."
    )

    db.add_all([c_classes, c_objects, c_constructors, c_inheritance, c_polymorphism, c_di])
    db.commit()

    # 4. Prerequisite Graph:
    # Classes -> Objects -> Constructors -> Inheritance -> Polymorphism -> Dependency Injection
    c_objects.prerequisites.append(c_classes)
    c_constructors.prerequisites.append(c_objects)
    c_inheritance.prerequisites.append(c_constructors)
    c_polymorphism.prerequisites.append(c_inheritance)
    c_di.prerequisites.append(c_polymorphism)
    db.commit()

    # 5. Seed Questions (at least 30 questions)
    questions_data = [
        # --- Classes ---
        {
            "concept": c_classes,
            "type": "MCQ",
            "title": "Core Definition of a Class",
            "description": "Which of the following best defines a 'Class' in Object-Oriented Programming?",
            "difficulty": "EASY",
            "options": [
                "A physical memory allocation in the hardware heap",
                "A blueprint or prototype from which objects are created",
                "A global execution thread running on the CPU",
                "A compiled binary executable file"
            ],
            "correct_answer": "A blueprint or prototype from which objects are created",
            "explanation": "A class defines the attributes and methods that its instantiated objects will possess."
        },
        {
            "concept": c_classes,
            "type": "MCQ",
            "title": "Encapsulation Purpose",
            "description": "What is the primary architectural purpose of encapsulation in a class?",
            "difficulty": "MEDIUM",
            "options": [
                "To speed up database index searches",
                "To bundle data with methods and restrict direct access to internal state",
                "To allow any external function to overwrite internal variables",
                "To avoid defining constructor functions"
            ],
            "correct_answer": "To bundle data with methods and restrict direct access to internal state",
            "explanation": "Encapsulation shields the internal representation of an object from unauthorized external tampering."
        },
        {
            "concept": c_classes,
            "type": "MCQ",
            "title": "Class Attributes vs Instance Attributes",
            "description": "In Python, how does a class attribute differ from an instance attribute?",
            "difficulty": "MEDIUM",
            "options": [
                "Class attributes are shared across all instances; instance attributes are unique to each instance",
                "Class attributes cannot be read after creation",
                "Instance attributes cannot store string values",
                "There is no functional difference"
            ],
            "correct_answer": "Class attributes are shared across all instances; instance attributes are unique to each instance",
            "explanation": "Class variables are shared by all instances, whereas instance variables are attached to 'self'."
        },
        {
            "concept": c_classes,
            "type": "SHORT_ANSWER",
            "title": "Self Parameter Role",
            "description": "What explicit keyword or convention in Python method definitions represents the current instance being manipulated?",
            "difficulty": "EASY",
            "options": ["self", "this", "cls", "super"],
            "correct_answer": "self",
            "explanation": "In Python, 'self' represents the instance of the class."
        },
        {
            "concept": c_classes,
            "type": "MCQ",
            "title": "Access Modifiers Convention",
            "description": "In Python, how is a protected or private attribute conventionally indicated?",
            "difficulty": "EASY",
            "options": [
                "With single or double leading underscores (e.g., _var, __var)",
                "Using the private keyword before the declaration",
                "By declaring the variable inside an XML schema",
                "By appending an exclamation mark (!)"
            ],
            "correct_answer": "With single or double leading underscores (e.g., _var, __var)",
            "explanation": "Python uses _protected (convention) and __private (name mangling) leading underscores."
        },

        # --- Objects ---
        {
            "concept": c_objects,
            "type": "MCQ",
            "title": "Instantiation Process",
            "description": "What occurs in memory when a class is instantiated into an object?",
            "difficulty": "EASY",
            "options": [
                "Memory is allocated in the heap to store the object's instance state",
                "The source code is deleted from the disk",
                "A new operating system process is spawned",
                "All other objects of the same class are reset"
            ],
            "correct_answer": "Memory is allocated in the heap to store the object's instance state",
            "explanation": "Instantiation allocates memory for the new instance and executes initialization logic."
        },
        {
            "concept": c_objects,
            "type": "MCQ",
            "title": "Identity vs Equality",
            "description": "In Python, which operator evaluates object identity (whether two references point to the same memory address)?",
            "difficulty": "MEDIUM",
            "options": [
                "is",
                "==",
                "equals()",
                ":="
            ],
            "correct_answer": "is",
            "explanation": "'is' checks memory reference identity (id(a) == id(b)), while '==' checks value equality."
        },
        {
            "concept": c_objects,
            "type": "MCQ",
            "title": "Object Lifecycle",
            "description": "What component in Python or Java manages the deallocation of objects that have no remaining active references?",
            "difficulty": "MEDIUM",
            "options": [
                "Garbage Collector",
                "Static Linker",
                "Bytecode Transpiler",
                "Dynamic Dispatch Table"
            ],
            "correct_answer": "Garbage Collector",
            "explanation": "The garbage collector detects unreferenced memory and reclaims it automatically."
        },
        {
            "concept": c_objects,
            "type": "SHORT_ANSWER",
            "title": "Checking Instance Type",
            "description": "Which built-in Python function checks if an object is an instance of a specified class or tuple of classes?",
            "difficulty": "EASY",
            "options": ["isinstance", "typeof", "type", "isa"],
            "correct_answer": "isinstance",
            "explanation": "isinstance(object, classinfo) returns True if the object is an instance or subclass."
        },
        {
            "concept": c_objects,
            "type": "MCQ",
            "title": "Mutable vs Immutable Objects",
            "description": "If an object is immutable, what happens when you perform an operation that modifies its value?",
            "difficulty": "HARD",
            "options": [
                "A new object is created in memory with the modified value",
                "The original memory buffer is overwritten in place",
                "The program throws a compile-time segmentation fault",
                "All variables pointing to it are deleted"
            ],
            "correct_answer": "A new object is created in memory with the modified value",
            "explanation": "Immutable objects (like strings, tuples) cannot be altered in place; modifications yield new objects."
        },

        # --- Constructors ---
        {
            "concept": c_constructors,
            "type": "MCQ",
            "title": "Constructor Initialization in Python",
            "description": "Which dunder method serves as the instance initializer in Python classes?",
            "difficulty": "EASY",
            "options": [
                "__init__",
                "__new__",
                "__create__",
                "__construct__"
            ],
            "correct_answer": "__init__",
            "explanation": "__init__ initializes the newly created object instance with parameters."
        },
        {
            "concept": c_constructors,
            "type": "MCQ",
            "title": "Constructors and Object Invariants",
            "description": "Why is validating parameters inside a constructor considered an architectural best practice?",
            "difficulty": "MEDIUM",
            "options": [
                "To guarantee that the object is never in an invalid state (preserving invariants)",
                "To speed up network socket transmission",
                "Because Python disallows methods from raising exceptions",
                "To automatically generate HTML documentation"
            ],
            "correct_answer": "To guarantee that the object is never in an invalid state (preserving invariants)",
            "explanation": "Validating at construction ensures invalid instances never circulate through the system."
        },
        {
            "concept": c_constructors,
            "type": "MCQ",
            "title": "__new__ vs __init__",
            "description": "What is the key difference between __new__ and __init__ in Python?",
            "difficulty": "HARD",
            "options": [
                "__new__ actually allocates and returns the instance, while __init__ initializes it",
                "__init__ allocates memory and __new__ deletes it",
                "__new__ is only available in Python 2",
                "They are exact synonyms with identical signatures"
            ],
            "correct_answer": "__new__ actually allocates and returns the instance, while __init__ initializes it",
            "explanation": "__new__ is the allocator returning the new object, and __init__ configures its state."
        },
        {
            "concept": c_constructors,
            "type": "MCQ",
            "title": "Invoking Parent Constructor",
            "description": "How should a subclass in Python invoke its parent class constructor?",
            "difficulty": "MEDIUM",
            "options": [
                "super().__init__(*args, **kwargs)",
                "parent.init(self)",
                "this.base()",
                "super.constructor()"
            ],
            "correct_answer": "super().__init__(*args, **kwargs)",
            "explanation": "super() delegates method calls to the parent or MRO next-in-line class."
        },
        {
            "concept": c_constructors,
            "type": "SHORT_ANSWER",
            "title": "Default Constructor Behavior",
            "description": "If a class does not define an explicit constructor in Python or C++, what does the language provide?",
            "difficulty": "EASY",
            "options": ["default constructor", "null constructor", "empty constructor"],
            "correct_answer": "default constructor",
            "explanation": "The language synthesizes a default parameterless constructor."
        },

        # --- Inheritance ---
        {
            "concept": c_inheritance,
            "type": "MCQ",
            "title": "Principle of Inheritance",
            "description": "Which relationship type is fundamentally modeled by class inheritance?",
            "difficulty": "EASY",
            "options": [
                "IS-A relationship (e.g., Dog is an Animal)",
                "HAS-A relationship (e.g., Car has an Engine)",
                "USES-A relationship (e.g., Printer uses Paper)",
                "WORKS-WITH relationship"
            ],
            "correct_answer": "IS-A relationship (e.g., Dog is an Animal)",
            "explanation": "Inheritance models the IS-A relationship; composition models HAS-A."
        },
        {
            "concept": c_inheritance,
            "type": "MCQ",
            "title": "Method Resolution Order (MRO)",
            "description": "In Python multiple inheritance, which algorithm determines the order in which classes are searched for an attribute?",
            "difficulty": "HARD",
            "options": [
                "C3 Linearization algorithm",
                "Dijkstra's Shortest Path",
                "Depth-First Search without backtracking",
                "Randomized Round-Robin"
            ],
            "correct_answer": "C3 Linearization algorithm",
            "explanation": "Python uses the C3 Linearization algorithm to compute a deterministic MRO."
        },
        {
            "concept": c_inheritance,
            "type": "MCQ",
            "title": "Liskov Substitution Principle (LSP)",
            "description": "According to LSP, what should be true when substituting a subclass instance for a base class instance?",
            "difficulty": "HARD",
            "options": [
                "The program must continue to function correctly without altering desired properties",
                "The subclass must throw an error whenever an unused method is called",
                "The subclass must override all methods to do nothing",
                "The program must recompile at runtime"
            ],
            "correct_answer": "The program must continue to function correctly without altering desired properties",
            "explanation": "LSP states objects of a superclass should be replaceable with objects of a subclass without breaking correctness."
        },
        {
            "concept": c_inheritance,
            "type": "MCQ",
            "title": "Composition over Inheritance",
            "description": "Why do senior software architects often advise 'Favor object composition over class inheritance'?",
            "difficulty": "MEDIUM",
            "options": [
                "Composition provides loose coupling and flexibility to change behavior at runtime",
                "Inheritance requires more RAM than composition",
                "Composition prevents functions from having return types",
                "Because compilers forbid multiple inheritance completely"
            ],
            "correct_answer": "Composition provides loose coupling and flexibility to change behavior at runtime",
            "explanation": "Inheritance tightly couples parent and child (white-box reuse), whereas composition keeps objects decoupled (black-box reuse)."
        },
        {
            "concept": c_inheritance,
            "type": "SHORT_ANSWER",
            "title": "Diamond Problem Keyword",
            "description": "In languages like C++, what type of inheritance resolves the ambiguity of the diamond problem?",
            "difficulty": "HARD",
            "options": ["virtual", "virtual inheritance", "abstract"],
            "correct_answer": "virtual",
            "explanation": "Virtual inheritance ensures only one copy of the common base class is included."
        },

        # --- Polymorphism ---
        {
            "concept": c_polymorphism,
            "type": "MCQ",
            "title": "Dynamic Dispatch",
            "description": "What is dynamic dispatch (runtime polymorphism)?",
            "difficulty": "MEDIUM",
            "options": [
                "The selection of which polymorphic method implementation to invoke at runtime based on the actual object type",
                "Sending HTTP requests to multiple backend server clusters",
                "Converting integer variables to floating-point numbers automatically",
                "Generating code documentation during deployment"
            ],
            "correct_answer": "The selection of which polymorphic method implementation to invoke at runtime based on the actual object type",
            "explanation": "Dynamic dispatch resolves the actual method to call during runtime using the vtable."
        },
        {
            "concept": c_polymorphism,
            "type": "MCQ",
            "title": "Duck Typing Concept",
            "description": "What does the phrase 'If it walks like a duck and quacks like a duck, it's a duck' describe in dynamic languages like Python?",
            "difficulty": "EASY",
            "options": [
                "Duck typing: object suitability is determined by the presence of methods and properties, not explicit inheritance",
                "A syntax error caused by invalid string formatting",
                "A strict compilation check requiring abstract class inheritance",
                "An algorithm for sorting animal arrays"
            ],
            "correct_answer": "Duck typing: object suitability is determined by the presence of methods and properties, not explicit inheritance",
            "explanation": "Duck typing allows polymorphic code based on behavior rather than declared type hierarchies."
        },
        {
            "concept": c_polymorphism,
            "type": "MCQ",
            "title": "Method Overriding vs Overloading",
            "description": "What distinguishes Method Overriding from Method Overloading?",
            "difficulty": "MEDIUM",
            "options": [
                "Overriding redefines a base class method with the same signature in a subclass; Overloading defines methods with the same name but different parameters in the same class",
                "Overriding happens only in the compiler; Overloading happens in the CPU cache",
                "Overriding is only allowed for private variables",
                "There is no difference"
            ],
            "correct_answer": "Overriding redefines a base class method with the same signature in a subclass; Overloading defines methods with the same name but different parameters in the same class",
            "explanation": "Overriding replaces inherited behavior; overloading allows multiple parameter signatures."
        },
        {
            "concept": c_polymorphism,
            "type": "MCQ",
            "title": "Abstract Base Classes (abc)",
            "description": "In Python, which module is used to define formal interfaces and abstract base classes with mandatory method implementations?",
            "difficulty": "MEDIUM",
            "options": [
                "abc",
                "interface",
                "protocols",
                "virtuals"
            ],
            "correct_answer": "abc",
            "explanation": "The 'abc' module provides ABC and @abstractmethod decorator."
        },
        {
            "concept": c_polymorphism,
            "type": "SHORT_ANSWER",
            "title": "Vtable Definition",
            "description": "In compiled languages like C++, what lookup table structure is created by the compiler to support dynamic dispatch?",
            "difficulty": "HARD",
            "options": ["vtable", "virtual method table", "vptr"],
            "correct_answer": "vtable",
            "explanation": "A vtable (virtual method table) stores pointers to the virtual functions of a class."
        },

        # --- Dependency Injection ---
        {
            "concept": c_di,
            "type": "MCQ",
            "title": "Core Intent of Dependency Injection",
            "description": "What is the primary motivation for utilizing Dependency Injection (DI)?",
            "difficulty": "MEDIUM",
            "options": [
                "To invert control so that a class receives its dependencies from an external assembler rather than creating them internally",
                "To inject SQL statements directly into the backend database",
                "To force all classes to use global singleton variables",
                "To eliminate the need for writing unit tests"
            ],
            "correct_answer": "To invert control so that a class receives its dependencies from an external assembler rather than creating them internally",
            "explanation": "DI decouples the usage of an object from its creation, making code testable and modular."
        },
        {
            "concept": c_di,
            "type": "MCQ",
            "title": "Dependency Inversion Principle (DIP)",
            "description": "The 'D' in SOLID principles states that high-level modules should not depend on low-level modules. Both should depend on what?",
            "difficulty": "MEDIUM",
            "options": [
                "Abstractions (Interfaces or abstract contracts)",
                "Concrete database drivers",
                "Hardware device registers",
                "Raw JSON strings"
            ],
            "correct_answer": "Abstractions (Interfaces or abstract contracts)",
            "explanation": "DIP mandates depending upon abstractions rather than concrete implementations."
        },
        {
            "concept": c_di,
            "type": "MCQ",
            "title": "Constructor Injection vs Service Locator",
            "description": "Why is Constructor Injection generally preferred over the Service Locator pattern?",
            "difficulty": "HARD",
            "options": [
                "Constructor Injection makes dependencies explicit in the API contract, avoiding hidden dependencies",
                "Service Locator runs faster because it bypasses memory management",
                "Constructor Injection is only supported in Python",
                "Service Locator is banned by the ISO C++ standard"
            ],
            "correct_answer": "Constructor Injection makes dependencies explicit in the API contract, avoiding hidden dependencies",
            "explanation": "Constructor injection makes an object's dependencies visible and enforceable at initialization."
        },
        {
            "concept": c_di,
            "type": "MCQ",
            "title": "Unit Testing with DI",
            "description": "How does Dependency Injection fundamentally simplify unit testing of complex business logic?",
            "difficulty": "EASY",
            "options": [
                "It allows mocking or stubbing external dependencies (e.g. database, payment gateway) easily",
                "It eliminates the need for test assertion statements",
                "It automatically generates test cases without code",
                "It bypasses all exception checks"
            ],
            "correct_answer": "It allows mocking or stubbing external dependencies (e.g. database, payment gateway) easily",
            "explanation": "Mock implementations can be passed into the subject under test without modifying production code."
        },
        {
            "concept": c_di,
            "type": "SHORT_ANSWER",
            "title": "Inversion of Control Acronym",
            "description": "What common three-letter architectural acronym represents the broader design paradigm of which Dependency Injection is a subtype?",
            "difficulty": "EASY",
            "options": ["IoC", "IOC", "ioc"],
            "correct_answer": "IoC",
            "explanation": "Inversion of Control (IoC) is the overarching principle."
        }
    ]

    for q in questions_data:
        question_obj = Question(
            concept_id=q["concept"].id,
            type=q["type"],
            title=q["title"],
            description=q["description"],
            difficulty=q["difficulty"],
            options=q.get("options"),
            correct_answer=q["correct_answer"],
            explanation=q.get("explanation")
        )
        db.add(question_obj)
    db.commit()

    # 6. Seed Student Mastery Profiles
    # Student A:
    # High: Classes (95%), Objects (90%), Constructors (80%)
    # Weak: Inheritance (45%), Polymorphism (30%), Dependency Injection (10%)
    student_a_masteries = [
        (c_classes.id, 95.0, 10, 9),
        (c_objects.id, 90.0, 8, 7),
        (c_constructors.id, 80.0, 6, 5),
        (c_inheritance.id, 45.0, 5, 2),
        (c_polymorphism.id, 30.0, 4, 1),
        (c_di.id, 10.0, 1, 0),
    ]
    for cid, score, att, corr in student_a_masteries:
        sm = StudentMastery(
            student_id=student_a.id,
            concept_id=cid,
            mastery=score,
            attempts=att,
            correct_attempts=corr
        )
        hist = MasteryHistory(
            student_id=student_a.id,
            concept_id=cid,
            mastery=score,
            change_amount=score,
            reason="Diagnostic Baseline Assessment"
        )
        db.add(sm)
        db.add(hist)

    # Student B:
    # High: Classes (95%), Objects (93%), Constructors (91%), Inheritance (90%), Polymorphism (88%)
    # Next/Weak: Dependency Injection (20%)
    student_b_masteries = [
        (c_classes.id, 95.0, 12, 11),
        (c_objects.id, 93.0, 10, 9),
        (c_constructors.id, 91.0, 9, 8),
        (c_inheritance.id, 90.0, 8, 7),
        (c_polymorphism.id, 88.0, 8, 7),
        (c_di.id, 20.0, 2, 0),
    ]
    for cid, score, att, corr in student_b_masteries:
        sm = StudentMastery(
            student_id=student_b.id,
            concept_id=cid,
            mastery=score,
            attempts=att,
            correct_attempts=corr
        )
        hist = MasteryHistory(
            student_id=student_b.id,
            concept_id=cid,
            mastery=score,
            change_amount=score,
            reason="Diagnostic Baseline Assessment"
        )
        db.add(sm)
        db.add(hist)

    # 7. Seed 5 Coding Problems with hidden & visible test cases
    p1 = CodingProblem(
        title="Bank Account Transaction Manager",
        description="""Design a `BankAccount` class that models basic deposit, withdrawal, and balance enquiry operations with invariant validation.

Implement the class with:
- Constructor: `__init__(self, account_holder: str, initial_balance: float = 0.0)`
  - Raises `ValueError` if `initial_balance < 0`.
- Methods:
  - `deposit(self, amount: float) -> float`: Adds amount to balance. Raises `ValueError` if `amount <= 0`. Returns updated balance.
  - `withdraw(self, amount: float) -> float`: Deducts amount from balance. Raises `ValueError` if `amount <= 0` or if `amount > balance`. Returns updated balance.
  - `get_balance(self) -> float`: Returns current balance.

Input format from standard input:
First line: initial balance
Subsequent lines: command string e.g. "deposit 50" or "withdraw 20" or "balance"
Print balance after each command.""",
        difficulty="EASY",
        allowed_languages=["python", "cpp"],
        time_limit=2.0,
        memory_limit=128
    )

    p2 = CodingProblem(
        title="Employee Hierarchy with Polymorphic Payroll",
        description="""Design a polymorphic payroll system with a base `Employee` class and subclasses `SalariedEmployee` and `HourlyEmployee`.

Base class `Employee`:
- `__init__(self, name: str, emp_id: int)`
- `calculate_pay(self) -> float`: Abstract method (raises `NotImplementedError` or abstract in C++).

Subclass `SalariedEmployee(Employee)`:
- `__init__(self, name: str, emp_id: int, annual_salary: float)`
- `calculate_pay(self) -> float`: Returns `annual_salary / 12` rounded to 2 decimal places.

Subclass `HourlyEmployee(Employee)`:
- `__init__(self, name: str, emp_id: int, hourly_rate: float, hours_worked: float)`
- `calculate_pay(self) -> float`:
  - Standard hours <= 40 paid at `hourly_rate`.
  - Overtime (> 40 hours) paid at `1.5 * hourly_rate`.
  - Returns total pay rounded to 2 decimal places.""",
        difficulty="MEDIUM",
        allowed_languages=["python", "cpp"],
        time_limit=2.0,
        memory_limit=128
    )

    p3 = CodingProblem(
        title="Shape Area & Perimeter Calculator",
        description="""Demonstrate runtime polymorphism by building an abstract `Shape` class and concrete subclasses `Rectangle` and `Circle`.

Base class `Shape`:
- Abstract methods: `area() -> float` and `perimeter() -> float`

Subclass `Rectangle(Shape)`:
- `__init__(self, width: float, height: float)`
- Computes rectangle area and perimeter.

Subclass `Circle(Shape)`:
- `__init__(self, radius: float)`
- Computes circle area (`3.14159 * r^2`) and perimeter (`2 * 3.14159 * r`).

Both area and perimeter must be formatted to 2 decimal places.""",
        difficulty="EASY",
        allowed_languages=["python", "cpp"],
        time_limit=2.0,
        memory_limit=128
    )

    p4 = CodingProblem(
        title="Notification Service with Dependency Injection",
        description="""Implement an inverted dependency pattern for a `NotificationDispatcher`.

Define an interface/base `MessageSender`:
- `send(self, recipient: str, message: str) -> str`

Implement concrete senders:
- `EmailSender`: returns `"EMAIL to {recipient}: {message}"`
- `SmsSender`: returns `"SMS to {recipient}: {message}"`

Implement `NotificationDispatcher`:
- `__init__(self, sender: MessageSender)`: Constructor injects sender.
- `notify(self, recipient: str, message: str) -> str`: Calls the injected sender's `send()` method.""",
        difficulty="MEDIUM",
        allowed_languages=["python", "cpp"],
        time_limit=2.0,
        memory_limit=128
    )

    p5 = CodingProblem(
        title="Robust Stack with Max Value Tracking",
        description="""Implement a `MinMaxStack` class with constructor initialization and O(1) retrieval of current minimum and maximum elements.

Methods:
- `push(val: int)`: Pushes val to stack.
- `pop() -> int`: Pops and returns top element (raises `IndexError` if empty).
- `get_max() -> int`: Returns maximum value currently in stack in O(1) time.
- `get_min() -> int`: Returns minimum value currently in stack in O(1) time.""",
        difficulty="HARD",
        allowed_languages=["python", "cpp"],
        time_limit=2.0,
        memory_limit=128
    )

    db.add_all([p1, p2, p3, p4, p5])
    db.commit()

    # Seed test cases for Problem 1
    tc1_vis1 = TestCase(
        problem_id=p1.id,
        input="100\ndeposit 50\nbalance",
        expected_output="150.0\n150.0",
        is_hidden=False
    )
    tc1_vis2 = TestCase(
        problem_id=p1.id,
        input="200\nwithdraw 50\nbalance",
        expected_output="150.0\n150.0",
        is_hidden=False
    )
    tc1_hid1 = TestCase(
        problem_id=p1.id,
        input="500\ndeposit 250\nwithdraw 100\nwithdraw 50\nbalance",
        expected_output="750.0\n650.0\n600.0\n600.0",
        is_hidden=True
    )
    tc1_hid2 = TestCase(
        problem_id=p1.id,
        input="1000\nwithdraw 1000\nbalance",
        expected_output="0.0\n0.0",
        is_hidden=True
    )

    # Seed test cases for Problem 2
    tc2_vis1 = TestCase(
        problem_id=p2.id,
        input="SALARIED Alice 101 120000",
        expected_output="Alice: 10000.0",
        is_hidden=False
    )
    tc2_vis2 = TestCase(
        problem_id=p2.id,
        input="HOURLY Bob 102 20 45",
        expected_output="Bob: 950.0",
        is_hidden=False
    )
    tc2_hid1 = TestCase(
        problem_id=p2.id,
        input="HOURLY Charlie 103 25 35",
        expected_output="Charlie: 875.0",
        is_hidden=True
    )
    tc2_hid2 = TestCase(
        problem_id=p2.id,
        input="SALARIED Diana 104 96000",
        expected_output="Diana: 8000.0",
        is_hidden=True
    )

    # Seed test cases for Problem 3
    tc3_vis1 = TestCase(
        problem_id=p3.id,
        input="RECTANGLE 4 5",
        expected_output="Area: 20.00, Perimeter: 18.00",
        is_hidden=False
    )
    tc3_hid1 = TestCase(
        problem_id=p3.id,
        input="CIRCLE 3",
        expected_output="Area: 28.27, Perimeter: 18.85",
        is_hidden=True
    )

    # Seed test cases for Problem 4
    tc4_vis1 = TestCase(
        problem_id=p4.id,
        input="EMAIL user@example.com Welcome",
        expected_output="EMAIL to user@example.com: Welcome",
        is_hidden=False
    )
    tc4_hid1 = TestCase(
        problem_id=p4.id,
        input="SMS +1234567890 VerificationCode:4291",
        expected_output="SMS to +1234567890: VerificationCode:4291",
        is_hidden=True
    )

    # Seed test cases for Problem 5
    tc5_vis1 = TestCase(
        problem_id=p5.id,
        input="push 10\npush 20\npush 5\nmax\nmin",
        expected_output="20\n5",
        is_hidden=False
    )
    tc5_hid1 = TestCase(
        problem_id=p5.id,
        input="push 15\npush 30\npop\nmax\nmin",
        expected_output="30\n15\n15",
        is_hidden=True
    )

    db.add_all([
        tc1_vis1, tc1_vis2, tc1_hid1, tc1_hid2,
        tc2_vis1, tc2_vis2, tc2_hid1, tc2_hid2,
        tc3_vis1, tc3_hid1,
        tc4_vis1, tc4_hid1,
        tc5_vis1, tc5_hid1
    ])
    db.commit()

    print("[Seed] Successfully seeded OOP Course, 6 concepts, 30 questions, 5 coding problems, and demo profiles for Trainer, Student A, and Student B!")
