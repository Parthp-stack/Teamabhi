import sys
from pathlib import Path
_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from backend.models.user import User, UserRole, StudentProfile, TeacherProfile
from backend.models.course import Course, Module
from backend.models.concept import Concept, ConceptPrerequisite
from backend.models.question import Question, Attempt
from backend.models.mastery import StudentMastery, MasteryHistory
from backend.models.coding import CodingProblem, TestCase, CodingSubmission
from backend.models.explanation import ExplanationQuestion, ExplanationAnswer
from backend.models.ai_evaluation import AIEvaluation

def seed_data_structures_curriculum(db: Session):
    # Check if Data Structures course already exists
    ds_course = db.query(Course).filter(Course.title == "Data Structures").first()
    trainer = db.query(User).filter(User.role == UserRole.TRAINER.value).first()
    student_a = db.query(User).filter(User.email == "student.a@adaptive.edu").first()
    student_b = db.query(User).filter(User.email == "student.b@adaptive.edu").first()

    # Ensure Profiles exist
    if trainer and not trainer.teacher_profile:
        tp = TeacherProfile(user_id=trainer.id, department="Computer Science & Engineering", bio="Professor of Computer Systems and Adaptive Learning Architect.")
        db.add(tp)
        db.commit()

    if student_a and not student_a.student_profile:
        sp_a = StudentProfile(user_id=student_a.id, enrollment_number="DS-2026-A01", target_subject="Data Structures", preferences={"learning_speed": "FAST", "preferred_language": "python"})
        db.add(sp_a)
        db.commit()

    if student_b and not student_b.student_profile:
        sp_b = StudentProfile(user_id=student_b.id, enrollment_number="DS-2026-B02", target_subject="Data Structures", preferences={"learning_speed": "MODERATE", "preferred_language": "cpp"})
        db.add(sp_b)
        db.commit()

    if ds_course:
        print("[Seed] Data Structures curriculum already registered.")
        return

    print("[Seed] Creating complete Data Structures curriculum with Searching, Sorting, Linked Lists, Stacks & Queues...")

    # 1. Course: Data Structures
    course = Course(
        title="Data Structures",
        description="Comprehensive mastery-based curriculum covering Searching, Sorting, Linked Lists, Stacks, and Queues with prerequisite knowledge tracing.",
        created_by=trainer.id if trainer else None
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    # 2. Topics / Modules
    m_search = Module(course_id=course.id, title="Searching", description="Linear, Binary, and Sentinel retrieval algorithms.", order_index=1)
    m_sort = Module(course_id=course.id, title="Sorting", description="Comparison and divide-and-conquer sorting mechanics.", order_index=2)
    m_ll = Module(course_id=course.id, title="Linked List", description="Dynamic pointer-linked linear structures.", order_index=3)
    m_stack = Module(course_id=course.id, title="Stack", description="LIFO collections and matching algorithms.", order_index=4)
    m_queue = Module(course_id=course.id, title="Queue", description="FIFO collections and ring buffer dispatchers.", order_index=5)

    db.add_all([m_search, m_sort, m_ll, m_stack, m_queue])
    db.commit()
    for m in [m_search, m_sort, m_ll, m_stack, m_queue]:
        db.refresh(m)

    # 3. Concepts
    # Searching
    c_lin_search = Concept(
        module_id=m_search.id,
        name="Linear Search",
        description="Sequential scan comparing elements until a match is found.",
        difficulty="EASY",
        order_index=1,
        explanation="Iterates sequentially through every element until the target is found or array end is reached. Time complexity O(n), auxiliary space O(1).",
        examples=["Finding a name in an unsorted list", "Single-pass minimum or maximum scan"],
        code_snippet="def linear_search(arr, target):\n    for i in range(len(arr)):\n        if arr[i] == target:\n            return i\n    return -1"
    )
    c_bin_search = Concept(
        module_id=m_search.id,
        name="Binary Search",
        description="Divide-and-conquer search on sorted collections.",
        difficulty="MEDIUM",
        order_index=2,
        explanation="Efficient search on sorted collections. Compares the target against the middle element, discarding half the search interval on each comparison. Time complexity O(log n), auxiliary space O(1).",
        examples=["Lookup in a sorted array", "Logarithmic threshold boundary finding"],
        code_snippet="def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1"
    )
    c_sen_search = Concept(
        module_id=m_search.id,
        name="Sentinel Search",
        description="Linear search variant using a boundary sentinel element.",
        difficulty="MEDIUM",
        order_index=3,
        explanation="Linear search optimization where target is placed as a sentinel at the array end, removing the index boundary check in the loop body.",
        examples=["High-throughput scan minimizing CPU branch misprediction"],
        code_snippet="def sentinel_search(arr, target):\n    n = len(arr)\n    last = arr[-1]\n    arr[-1] = target\n    i = 0\n    while arr[i] != target:\n        i += 1\n    arr[-1] = last\n    if i < n - 1 or arr[-1] == target:\n        return i\n    return -1"
    )

    # Sorting
    c_bubble = Concept(
        module_id=m_sort.id,
        name="Bubble Sort",
        description="Pairwise adjacent comparisons and swaps.",
        difficulty="EASY",
        order_index=4,
        explanation="Repeatedly steps through the list, compares adjacent elements and swaps them if out of order. O(n^2) worst case, O(1) space.",
        examples=["Nearly sorted arrays", "Pedagogical sorting foundation"],
        code_snippet="def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n - i - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr"
    )
    c_merge = Concept(
        module_id=m_sort.id,
        name="Merge Sort",
        description="Divide-and-conquer stable logarithmic sorting.",
        difficulty="MEDIUM",
        order_index=5,
        explanation="Divides array into halves, recursively sorts each half, and merges the sorted halves. O(n log n) guaranteed time, O(n) space.",
        examples=["External tape/disk sorting", "Stable record collation"],
        code_snippet="def merge(left, right):\n    res = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]: res.append(left[i]); i += 1\n        else: res.append(right[j]); j += 1\n    res.extend(left[i:]); res.extend(right[j:])\n    return res"
    )
    c_quick = Concept(
        module_id=m_sort.id,
        name="Quick Sort",
        description="Partition-based in-place recursive sorting.",
        difficulty="HARD",
        order_index=6,
        explanation="Picks a pivot element and partitions array into elements less than and greater than pivot. O(n log n) average, in-place O(log n) stack space.",
        examples=["General purpose fast system sort", "Primitive array sorting"],
        code_snippet="def quick_sort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + mid + quick_sort(right)"
    )

    # Linked List
    c_sll = Concept(
        module_id=m_ll.id,
        name="Singly Linked List",
        description="Forward pointer node chain.",
        difficulty="EASY",
        order_index=7,
        explanation="Sequence of elements where each element points to the next node. O(1) prepend, O(n) arbitrary access.",
        examples=["Dynamic stack implementation", "Symbol table chaining"],
        code_snippet="class Node:\n    def __init__(self, val):\n        self.val = val\n        self.next = None"
    )
    c_dll = Concept(
        module_id=m_ll.id,
        name="Doubly Linked List",
        description="Bidirectional pointer node chain.",
        difficulty="MEDIUM",
        order_index=8,
        explanation="Each node maintains references to both next and previous nodes, supporting O(1) deletions given node reference.",
        examples=["LRU Cache doubly-linked eviction list", "Text editor line buffer"],
        code_snippet="class DNode:\n    def __init__(self, val):\n        self.val = val\n        self.prev = None\n        self.next = None"
    )

    # Stack
    c_stack_ops = Concept(
        module_id=m_stack.id,
        name="Stack Operations",
        description="LIFO push, pop, and top inspection.",
        difficulty="EASY",
        order_index=9,
        explanation="Last-In-First-Out data structure providing O(1) push, pop, and peek operations.",
        examples=["Browser back button history", "Call stack activation frames"],
        code_snippet="class Stack:\n    def __init__(self):\n        self._items = []\n    def push(self, item): self._items.append(item)\n    def pop(self): return self._items.pop()\n    def peek(self): return self._items[-1]"
    )
    c_parens = Concept(
        module_id=m_stack.id,
        name="Valid Parentheses",
        description="Bracket delimiter syntax validation using stack.",
        difficulty="MEDIUM",
        order_index=10,
        explanation="Verifies matching pairs of bracket delimiters in valid opening and closing ordering.",
        examples=["Compiler syntax parsing", "Mathematical equation verification"],
        code_snippet="def is_valid(s):\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top: return False\n        else: stack.append(char)\n    return not stack"
    )

    # Queue
    c_q_basics = Concept(
        module_id=m_queue.id,
        name="Queue Basics",
        description="FIFO enqueue and dequeue.",
        difficulty="EASY",
        order_index=11,
        explanation="First-In-First-Out sequence where elements are added at rear and removed from front. O(1) time.",
        examples=["Job print queue", "BFS graph traversal buffer"],
        code_snippet="from collections import deque\nq = deque()\nq.append('task1') # enqueue\nfront = q.popleft() # dequeue"
    )
    c_circ_q = Concept(
        module_id=m_queue.id,
        name="Circular Queue",
        description="Fixed-size ring buffer avoiding array shifts.",
        difficulty="MEDIUM",
        order_index=12,
        explanation="Ring buffer where last position connects to first position, optimizing FIFO cache usage.",
        examples=["Hardware audio DMA buffers", "Network packet routing rings"],
        code_snippet="class CircularQueue:\n    def __init__(self, k):\n        self.data = [0] * k\n        self.head = self.tail = -1\n        self.size = k"
    )

    all_concepts = [
        c_lin_search, c_bin_search, c_sen_search,
        c_bubble, c_merge, c_quick,
        c_sll, c_dll,
        c_stack_ops, c_parens,
        c_q_basics, c_circ_q
    ]
    db.add_all(all_concepts)
    db.commit()
    for c in all_concepts:
        db.refresh(c)

    # 4. Prerequisite DAG
    prereqs = [
        (c_bin_search.id, c_lin_search.id),
        (c_sen_search.id, c_lin_search.id),
        (c_merge.id, c_bubble.id),
        (c_quick.id, c_merge.id),
        (c_dll.id, c_sll.id),
        (c_parens.id, c_stack_ops.id),
        (c_circ_q.id, c_q_basics.id)
    ]
    for cid, pid in prereqs:
        db.add(ConceptPrerequisite(concept_id=cid, prerequisite_id=pid))
    db.commit()

    # 5. Seed Practice Questions for each concept
    questions = [
        # Linear Search
        Question(
            concept_id=c_lin_search.id,
            topic_id=m_search.id,
            question_text="What is the worst-case time complexity of linear search on an unsorted array of size n?",
            question_type="MCQ",
            difficulty="EASY",
            options=["O(1)", "O(log n)", "O(n)", "O(n^2)"],
            correct_answer="O(n)",
            explanation="In the worst case, the target element is at the very end of the array or not present at all, requiring n comparisons."
        ),
        Question(
            concept_id=c_lin_search.id,
            topic_id=m_search.id,
            question_text="Under what condition does linear search achieve its best-case time complexity of O(1)?",
            question_type="MCQ",
            difficulty="EASY",
            options=["When array is sorted in reverse", "When the target is the first element", "When the target is in the middle", "When all elements are negative"],
            correct_answer="When the target is the first element",
            explanation="If the target is at index 0, linear search terminates immediately after the very first comparison."
        ),

        # Binary Search
        Question(
            concept_id=c_bin_search.id,
            topic_id=m_search.id,
            question_text="Which prerequisite MUST be satisfied by an array before applying binary search?",
            question_type="MCQ",
            difficulty="EASY",
            options=["Elements must be stored as strings", "Array must be sorted in monotonic order", "Array must contain only prime numbers", "Array must have power-of-two length"],
            correct_answer="Array must be sorted in monotonic order",
            explanation="Binary search relies on monotonicity to reliably eliminate half of the search interval each step."
        ),
        Question(
            concept_id=c_bin_search.id,
            topic_id=m_search.id,
            question_text="In binary search, what formula prevents integer 32-bit overflow when calculating the midpoint of 'left' and 'right'?",
            question_type="MCQ",
            difficulty="MEDIUM",
            options=["(left + right) / 2", "left + (right - left) / 2", "(left * right) / 2", "right - (left / 2)"],
            correct_answer="left + (right - left) / 2",
            explanation="left + (right - left) // 2 guarantees that intermediate sums never exceed the maximum value representable by standard 32-bit integers."
        ),
        Question(
            concept_id=c_bin_search.id,
            topic_id=m_search.id,
            question_text="Given a sorted array of 1,000,000 items, at most approximately how many comparisons will binary search require in the worst case?",
            question_type="MCQ",
            difficulty="HARD",
            options=["100", "20", "500,000", "1,000,000"],
            correct_answer="20",
            explanation="log2(1,000,000) is approximately 19.93, so at most 20 iterations are needed."
        ),

        # Sentinel Search
        Question(
            concept_id=c_sen_search.id,
            topic_id=m_search.id,
            question_text="What is the key advantage of Sentinel Search over standard Linear Search?",
            question_type="MCQ",
            difficulty="MEDIUM",
            options=["It achieves O(log n) time complexity", "It eliminates the index boundary check (i < n) in the inner loop", "It works only on trees", "It uses exponential auxiliary memory"],
            correct_answer="It eliminates the index boundary check (i < n) in the inner loop",
            explanation="By replacing the last element with the target, the loop is guaranteed to terminate without testing boundary bounds on every single step."
        ),

        # Bubble Sort
        Question(
            concept_id=c_bubble.id,
            topic_id=m_sort.id,
            question_text="What is the best-case time complexity of an optimized Bubble Sort when the input array is already sorted?",
            question_type="MCQ",
            difficulty="EASY",
            options=["O(n)", "O(n log n)", "O(n^2)", "O(1)"],
            correct_answer="O(n)",
            explanation="An optimized Bubble Sort uses a swapped flag; if no swaps occur in pass 1, it halts in O(n) time."
        ),

        # Merge Sort
        Question(
            concept_id=c_merge.id,
            topic_id=m_sort.id,
            question_text="Why is Merge Sort preferred over Quick Sort for sorting linked lists?",
            question_type="MCQ",
            difficulty="MEDIUM",
            options=["Merge sort requires no random access and achieves O(1) extra space on linked lists", "Linked lists cannot store numbers", "Merge sort executes in O(1) time", "Quick sort requires doubly linked lists only"],
            correct_answer="Merge sort requires no random access and achieves O(1) extra space on linked lists",
            explanation="Linked lists allow pointer reassignment without allocating extra contiguous array buffers, making merge sort highly efficient."
        ),

        # Stack Operations & Valid Parentheses
        Question(
            concept_id=c_stack_ops.id,
            topic_id=m_stack.id,
            question_text="Which algorithmic paradigm does a Stack adhere to?",
            question_type="MCQ",
            difficulty="EASY",
            options=["First In, First Out (FIFO)", "Last In, First Out (LIFO)", "Random In, Priority Out (RIPO)", "First In, Never Out (FINO)"],
            correct_answer="Last In, First Out (LIFO)",
            explanation="A Stack pops the most recently pushed element first (Last In, First Out)."
        ),
        Question(
            concept_id=c_parens.id,
            topic_id=m_stack.id,
            question_text="When evaluating the string '([)]', what condition causes the stack-based validator to correctly return False?",
            question_type="MCQ",
            difficulty="MEDIUM",
            options=["The stack becomes empty too early", "Encountering ']' while top of stack is '(' instead of '['", "String length is an odd number", "Parentheses cannot be nested"],
            correct_answer="Encountering ']' while top of stack is '(' instead of '['",
            explanation="A closing bracket must match the opening bracket at the top of the stack. Here ']' encounters '(' so the delimiters are mismatched."
        )
    ]
    db.add_all(questions)
    db.commit()

    # 6. Coding Problems with Multi-language support (Python, C, C++, Java, JavaScript)
    p_bin_search = CodingProblem(
        title="Binary Search in Sorted Array",
        description=(
            "Given a sorted integer array and a target integer, write a function to search target in array. "
            "Input Format:\nLine 1: integer n (size of array)\nLine 2: n space-separated sorted integers\nLine 3: target integer\n"
            "Output Format:\nPrint the 0-indexed position of target if found, otherwise print -1."
        ),
        difficulty="MEDIUM",
        allowed_languages=["python", "cpp", "c", "java", "javascript"],
        time_limit=2.0,
        memory_limit=128
    )
    p_parens = CodingProblem(
        title="Valid Parentheses Delimiter Checker",
        description=(
            "Given a string containing only '(', ')', '{', '}', '[' and ']', determine if the brackets are balanced. "
            "Input: Single line string s.\n"
            "Output: Print 'true' if string is valid, or 'false' otherwise."
        ),
        difficulty="MEDIUM",
        allowed_languages=["python", "cpp", "c", "java", "javascript"],
        time_limit=2.0,
        memory_limit=128
    )
    db.add_all([p_bin_search, p_parens])
    db.commit()
    db.refresh(p_bin_search)
    db.refresh(p_parens)

    # Test cases for Binary Search
    tc_bs = [
        TestCase(problem_id=p_bin_search.id, input="5\n1 3 5 7 9\n5", expected_output="2", is_hidden=False),
        TestCase(problem_id=p_bin_search.id, input="4\n2 4 6 8\n7", expected_output="-1", is_hidden=False),
        TestCase(problem_id=p_bin_search.id, input="1\n10\n10", expected_output="0", is_hidden=True),
        TestCase(problem_id=p_bin_search.id, input="6\n-5 -2 0 3 9 12\n-2", expected_output="1", is_hidden=True),
    ]
    # Test cases for Valid Parentheses
    tc_vp = [
        TestCase(problem_id=p_parens.id, input="()[]{}", expected_output="true", is_hidden=False),
        TestCase(problem_id=p_parens.id, input="(]", expected_output="false", is_hidden=False),
        TestCase(problem_id=p_parens.id, input="{[]}", expected_output="true", is_hidden=True),
        TestCase(problem_id=p_parens.id, input="([)]", expected_output="false", is_hidden=True),
    ]
    db.add_all(tc_bs + tc_vp)
    db.commit()

    # 7. Seed Student A Mastery Data (demonstrates weak in Binary Search, strong in Linear Search and Stack)
    if student_a:
        now = datetime.now(timezone.utc)
        # Linear Search: Mastered (88%)
        m_lin = StudentMastery(student_id=student_a.id, concept_id=c_lin_search.id, mastery_score=88.0, attempts=5, correct_attempts=5, last_attempt_at=now - timedelta(days=2))
        # Binary Search: Weak (38%)
        m_bin = StudentMastery(student_id=student_a.id, concept_id=c_bin_search.id, mastery_score=38.0, attempts=3, correct_attempts=1, last_attempt_at=now - timedelta(hours=2))
        # Stack Operations: Strong (90%)
        m_stk = StudentMastery(student_id=student_a.id, concept_id=c_stack_ops.id, mastery_score=90.0, attempts=4, correct_attempts=4, last_attempt_at=now - timedelta(days=1))
        # Bubble Sort: Developing (62%)
        m_bub = StudentMastery(student_id=student_a.id, concept_id=c_bubble.id, mastery_score=62.0, attempts=3, correct_attempts=2, last_attempt_at=now - timedelta(hours=18))

        db.add_all([m_lin, m_bin, m_stk, m_bub])
        db.commit()

        # Add history records
        db.add_all([
            MasteryHistory(student_id=student_a.id, concept_id=c_lin_search.id, mastery_score=88.0, change_amount=15.0, reason="Fast correct attempts on Linear Search", timestamp=now - timedelta(days=2)),
            MasteryHistory(student_id=student_a.id, concept_id=c_bin_search.id, mastery_score=38.0, change_amount=-12.0, reason="Repeated boundary errors on Binary Search", timestamp=now - timedelta(hours=2)),
            MasteryHistory(student_id=student_a.id, concept_id=c_stack_ops.id, mastery_score=90.0, change_amount=20.0, reason="High precision stack operations practice", timestamp=now - timedelta(days=1))
        ])
        db.commit()

        # Seed Coding Submission & AI Evaluation for Student A
        sub_sample = CodingSubmission(
            student_id=student_a.id,
            problem_id=p_bin_search.id,
            language="python",
            source_code=(
                "import sys\n"
                "lines = sys.stdin.read().split()\n"
                "if lines:\n"
                "    n = int(lines[0])\n"
                "    arr = [int(x) for x in lines[1:n+1]]\n"
                "    target = int(lines[n+1])\n"
                "    left, right = 0, n - 1\n"
                "    ans = -1\n"
                "    while left <= right:\n"
                "        mid = left + (right - left) // 2\n"
                "        if arr[mid] == target:\n"
                "            ans = mid\n"
                "            break\n"
                "        elif arr[mid] < target:\n"
                "            left = mid + 1\n"
                "        else:\n"
                "            right = mid - 1\n"
                "    print(ans)\n"
            ),
            status="PASSED",
            score=100.0,
            execution_time=0.045,
            memory_used=18.4,
            viva_verdict="Correct code + understood",
            ai_feedback="Student demonstrates solid grasp of binary search boundary conditions and integer overflow prevention."
        )
        db.add(sub_sample)
        db.commit()
        db.refresh(sub_sample)

        # Add viva questions
        vq1 = ExplanationQuestion(
            submission_id=sub_sample.id,
            question_text="Why did you use left + (right - left) // 2 instead of (left + right) // 2?",
            question="Why did you use left + (right - left) // 2 instead of (left + right) // 2?",
            expected_concept="Integer Overflow Prevention"
        )
        vq2 = ExplanationQuestion(
            submission_id=sub_sample.id,
            question_text="What is the space complexity of your iterative binary search implementation?",
            question="What is the space complexity of your iterative binary search implementation?",
            expected_concept="Auxiliary Space Analysis"
        )
        db.add_all([vq1, vq2])
        db.commit()
        db.refresh(vq1)
        db.refresh(vq2)

        ans1 = ExplanationAnswer(explanation_question_id=vq1.id, student_answer="In languages like C++ or Java, left + right can overflow MAX_INT. Writing left + (right - left) // 2 keeps the arithmetic safe.", evaluation="Accurately identifies 32-bit signed integer overflow boundaries.", score=9.5)
        ans2 = ExplanationAnswer(explanation_question_id=vq2.id, student_answer="The space complexity is O(1) auxiliary memory because we only declare pointers left, right, and mid without recursion.", evaluation="Correctly distinguishes iterative O(1) space from recursive O(log n) call frames.", score=9.0)
        db.add_all([ans1, ans2])
        db.commit()

        # Add AIEvaluation record
        ai_eval = AIEvaluation(
            student_id=student_a.id,
            question_id=None,
            concept_id=c_bin_search.id,
            submission_id=sub_sample.id,
            score=9.25,
            understanding_verdict="Correct code + understood",
            feedback="Exceptional understanding of binary search invariants, edge conditions, and complexity analysis.",
            detected_weaknesses=[],
            detected_strengths=["Integer overflow prevention", "Iterative space efficiency", "Binary bounds reasoning"],
            difficulty_recommendation="ADVANCED",
            next_question_recommendation="Binary Search on Rotated Array"
        )
        db.add(ai_eval)
        db.commit()

    print("[Seed] Data Structures curriculum, concepts, questions, multi-language coding problems, and student history created successfully!")
