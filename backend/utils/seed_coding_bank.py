import logging
from sqlalchemy.orm import Session
from backend.models.coding import CodingProblem, TestCase

logger = logging.getLogger("seed_coding_bank")

EXPANDED_CODING_PROBLEMS = [
    {
        "title": "Two Sum — Target Pair Discovery",
        "difficulty": "EASY",
        "topic": "arrays",
        "expected_solution_concept": "Hashing / Two Pointers",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Find indices of two numbers in an array that sum to a target value.",
        "problem_statement": "Given an array of integers `nums` and an integer `target`, return the 0-based indices of the two numbers such that they add up to `target`. You may assume that each input would have exactly one solution, and you may not use the same element twice.",
        "input_format": "Line 1: Space-separated integers representing nums.\nLine 2: Single integer representing target.",
        "output_format": "Two space-separated indices in ascending order.",
        "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9\nOnly one valid answer exists.",
        "examples": [
            {
                "input": "2 7 11 15\n9",
                "output": "0 1",
                "explanation": "Because nums[0] + nums[1] == 2 + 7 == 9, we return 0 1."
            },
            {
                "input": "3 2 4\n6",
                "output": "1 2",
                "explanation": "Because nums[1] + nums[2] == 2 + 4 == 6, we return 1 2."
            }
        ],
        "test_cases": [
            {"input": "2 7 11 15\n9\n", "expected_output": "0 1\n", "is_hidden": False},
            {"input": "3 2 4\n6\n", "expected_output": "1 2\n", "is_hidden": False},
            {"input": "3 3\n6\n", "expected_output": "0 1\n", "is_hidden": True},
            {"input": "-1 -2 -3 -4 -5\n-8\n", "expected_output": "2 4\n", "is_hidden": True},
            {"input": "100 200 500 1000\n700\n", "expected_output": "1 2\n", "is_hidden": True}
        ]
    },
    {
        "title": "Valid Palindrome and Sanitization",
        "difficulty": "EASY",
        "topic": "strings",
        "expected_solution_concept": "Two Pointers / String Manipulation",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Determine if a string is a palindrome after sanitizing non-alphanumeric characters.",
        "problem_statement": "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Alphanumeric characters include letters and numbers. Given a string `s`, print `true` if it is a palindrome, or `false` otherwise.",
        "input_format": "A single line containing string s.",
        "output_format": "A single line printing 'true' or 'false'.",
        "constraints": "1 <= s.length <= 2 * 10^5\ns consists only of printable ASCII characters.",
        "examples": [
            {
                "input": "A man, a plan, a canal: Panama",
                "output": "true",
                "explanation": "'amanaplanacanalpanama' is a palindrome."
            },
            {
                "input": "race a car",
                "output": "false",
                "explanation": "'raceacar' is not a palindrome."
            }
        ],
        "test_cases": [
            {"input": "A man, a plan, a canal: Panama\n", "expected_output": "true\n", "is_hidden": False},
            {"input": "race a car\n", "expected_output": "false\n", "is_hidden": False},
            {"input": " \n", "expected_output": "true\n", "is_hidden": True},
            {"input": "0P\n", "expected_output": "false\n", "is_hidden": True},
            {"input": "Was it a car or a cat I saw?\n", "expected_output": "true\n", "is_hidden": True}
        ]
    },
    {
        "title": "Search in Rotated Sorted Array",
        "difficulty": "MEDIUM",
        "topic": "searching",
        "expected_solution_concept": "Modified Binary Search (O(log n))",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Search for a target value in an ascending array rotated at an unknown pivot.",
        "problem_statement": "There is an integer array `nums` sorted in ascending order with distinct values. Given the array `nums` after an unknown rotation pivot and an integer `target`, return the index of `target` if it is in `nums`, or `-1` if it is not in `nums`.",
        "input_format": "Line 1: Space-separated integers representing nums.\nLine 2: Single integer representing target.",
        "output_format": "The 0-based index of target, or -1 if not found.",
        "constraints": "1 <= nums.length <= 5000\n-10^4 <= nums[i] <= 10^4\nAll values of nums are unique.",
        "examples": [
            {
                "input": "4 5 6 7 0 1 2\n0",
                "output": "4",
                "explanation": "Target 0 is located at index 4."
            },
            {
                "input": "4 5 6 7 0 1 2\n3",
                "output": "-1",
                "explanation": "Target 3 does not exist in nums, returning -1."
            }
        ],
        "test_cases": [
            {"input": "4 5 6 7 0 1 2\n0\n", "expected_output": "4\n", "is_hidden": False},
            {"input": "4 5 6 7 0 1 2\n3\n", "expected_output": "-1\n", "is_hidden": False},
            {"input": "1\n0\n", "expected_output": "-1\n", "is_hidden": True},
            {"input": "1 3\n3\n", "expected_output": "1\n", "is_hidden": True},
            {"input": "5 1 3\n5\n", "expected_output": "0\n", "is_hidden": True}
        ]
    },
    {
        "title": "Merge Overlapping Intervals",
        "difficulty": "MEDIUM",
        "topic": "sorting",
        "expected_solution_concept": "Greedy Interval Merging with Sorting",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Merge all overlapping intervals into mutually disjoint intervals.",
        "problem_statement": "Given a collection of intervals where each interval is represented by two space-separated integers `start end`, merge all overlapping intervals, and return an array of the non-overlapping intervals sorted by start time.",
        "input_format": "Line 1: Integer n (number of intervals).\nNext n lines: Two space-separated integers 'start end'.",
        "output_format": "Merged intervals, one per line as 'start end'.",
        "constraints": "1 <= n <= 10^4\n0 <= start <= end <= 10^4",
        "examples": [
            {
                "input": "4\n1 3\n2 6\n8 10\n15 18",
                "output": "1 6\n8 10\n15 18",
                "explanation": "Intervals [1,3] and [2,6] overlap, merging into [1,6]."
            }
        ],
        "test_cases": [
            {"input": "4\n1 3\n2 6\n8 10\n15 18\n", "expected_output": "1 6\n8 10\n15 18\n", "is_hidden": False},
            {"input": "2\n1 4\n4 5\n", "expected_output": "1 5\n", "is_hidden": False},
            {"input": "3\n1 4\n0 2\n3 5\n", "expected_output": "0 5\n", "is_hidden": True},
            {"input": "1\n10 20\n", "expected_output": "10 20\n", "is_hidden": True}
        ]
    },
    {
        "title": "Generate Well-Formed Parentheses",
        "difficulty": "MEDIUM",
        "topic": "recursion",
        "expected_solution_concept": "Backtracking / State Space Tree Recursion",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Generate all valid combinations of n pairs of balanced parentheses.",
        "problem_statement": "Given an integer `n`, generate all combinations of well-formed parentheses containing `n` pairs of open and closed brackets. Print each combination on a new line in lexicographical order.",
        "input_format": "A single integer n.",
        "output_format": "Each valid combination on a separate line.",
        "constraints": "1 <= n <= 8",
        "examples": [
            {
                "input": "3",
                "output": "((()))\n(()())\n(())()\n()(())\n()()()",
                "explanation": "All 5 well-formed parentheses for n = 3."
            }
        ],
        "test_cases": [
            {"input": "1\n", "expected_output": "()\n", "is_hidden": False},
            {"input": "2\n", "expected_output": "(())\n()()\n", "is_hidden": False},
            {"input": "3\n", "expected_output": "((()))\n(()())\n(())()\n()(())\n()()()\n", "is_hidden": True}
        ]
    },
    {
        "title": "Reverse Linked List Sequence",
        "difficulty": "EASY",
        "topic": "linked lists",
        "expected_solution_concept": "Iterative Pointer Inversion (prev, curr, next)",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Reverse a sequence representing a singly linked list.",
        "problem_statement": "Given a sequence of values representing a singly linked list from head to tail, reverse the sequence and print the values from the new head to tail.",
        "input_format": "A single line with space-separated integers representing node values.",
        "output_format": "Space-separated integers representing the reversed list values.",
        "constraints": "0 <= number of nodes <= 5000\n-5000 <= Node.val <= 5000",
        "examples": [
            {
                "input": "1 2 3 4 5",
                "output": "5 4 3 2 1",
                "explanation": "Reversing 1->2->3->4->5 yields 5->4->3->2->1."
            }
        ],
        "test_cases": [
            {"input": "1 2 3 4 5\n", "expected_output": "5 4 3 2 1\n", "is_hidden": False},
            {"input": "1 2\n", "expected_output": "2 1\n", "is_hidden": False},
            {"input": "42\n", "expected_output": "42\n", "is_hidden": True},
            {"input": "10 20 30 40\n", "expected_output": "40 30 20 10\n", "is_hidden": True}
        ]
    },
    {
        "title": "Min Stack Invariant Tracker",
        "difficulty": "MEDIUM",
        "topic": "stacks",
        "expected_solution_concept": "Dual Stack / Invariant Minimum Tracking",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Design a stack that retrieves the minimum element in O(1) time.",
        "problem_statement": "Process a series of stack commands: 'push x', 'pop', 'top', and 'getMin'. Print results for 'top' and 'getMin'.",
        "input_format": "Line 1: Integer q (number of operations).\nNext q lines: Commands 'push x', 'pop', 'top', or 'getMin'.",
        "output_format": "For each 'top' and 'getMin' command, print the corresponding integer on a new line.",
        "constraints": "1 <= q <= 3 * 10^4\n-2^31 <= x <= 2^31 - 1",
        "examples": [
            {
                "input": "6\npush -2\npush 0\npush -3\ngetMin\npop\ntop",
                "output": "-3\n0",
                "explanation": "Min is -3. After popping -3, top element is 0."
            }
        ],
        "test_cases": [
            {"input": "6\npush -2\npush 0\npush -3\ngetMin\npop\ntop\n", "expected_output": "-3\n0\n", "is_hidden": False},
            {"input": "5\npush 5\ngetMin\npush 3\ngetMin\ntop\n", "expected_output": "5\n3\n3\n", "is_hidden": False},
            {"input": "4\npush 1\npush 2\ntop\ngetMin\n", "expected_output": "2\n1\n", "is_hidden": True}
        ]
    },
    {
        "title": "Implement Queue using Stacks",
        "difficulty": "EASY",
        "topic": "queues",
        "expected_solution_concept": "Amortized O(1) Two-Stack Transfer",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Implement FIFO queue operations using two LIFO stacks.",
        "problem_statement": "Process queue operations: 'push x', 'pop', 'peek', 'empty'. Output the result for 'pop', 'peek', and 'empty' commands.",
        "input_format": "Line 1: Integer q.\nNext q lines: Commands 'push x', 'pop', 'peek', 'empty'.",
        "output_format": "Print each popped/peeked value or 'true'/'false' for empty.",
        "constraints": "1 <= q <= 100\n1 <= x <= 9",
        "examples": [
            {
                "input": "5\npush 1\npush 2\npeek\npop\nempty",
                "output": "1\n1\nfalse",
                "explanation": "Queue has [1, 2]. Peek returns 1. Pop returns 1. Empty is false."
            }
        ],
        "test_cases": [
            {"input": "5\npush 1\npush 2\npeek\npop\nempty\n", "expected_output": "1\n1\nfalse\n", "is_hidden": False},
            {"input": "3\npush 10\npop\nempty\n", "expected_output": "10\ntrue\n", "is_hidden": False},
            {"input": "4\npush 7\npush 8\npop\npop\n", "expected_output": "7\n8\n", "is_hidden": True}
        ]
    },
    {
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "MEDIUM",
        "topic": "sliding window",
        "expected_solution_concept": "Sliding Window with Hash Set / Index Map",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Find the length of the longest substring with all unique characters.",
        "problem_statement": "Given a string `s`, find the length of the longest substring without repeating characters.",
        "input_format": "A single line containing string s.",
        "output_format": "A single integer denoting max length.",
        "constraints": "0 <= s.length <= 5 * 10^4\ns consists of English letters, digits, symbols and spaces.",
        "examples": [
            {
                "input": "abcabcbb",
                "output": "3",
                "explanation": "The answer is 'abc', with the length of 3."
            },
            {
                "input": "bbbbb",
                "output": "1",
                "explanation": "The answer is 'b', with the length of 1."
            }
        ],
        "test_cases": [
            {"input": "abcabcbb\n", "expected_output": "3\n", "is_hidden": False},
            {"input": "bbbbb\n", "expected_output": "1\n", "is_hidden": False},
            {"input": "pwwkew\n", "expected_output": "3\n", "is_hidden": False},
            {"input": " \n", "expected_output": "1\n", "is_hidden": True},
            {"input": "dvdf\n", "expected_output": "3\n", "is_hidden": True}
        ]
    },
    {
        "title": "Climbing Stairs — Dynamic Steps",
        "difficulty": "EASY",
        "topic": "dynamic programming",
        "expected_solution_concept": "Dynamic Programming / Fibonacci Transition (dp[i] = dp[i-1] + dp[i-2])",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Calculate distinct ways to climb a staircase of n steps taking 1 or 2 steps at a time.",
        "problem_statement": "You are climbing a staircase. It takes `n` steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
        "input_format": "A single integer n.",
        "output_format": "A single integer representing total distinct ways.",
        "constraints": "1 <= n <= 45",
        "examples": [
            {
                "input": "2",
                "output": "2",
                "explanation": "There are two ways: 1 step + 1 step, or 2 steps."
            },
            {
                "input": "3",
                "output": "3",
                "explanation": "Three ways: 1+1+1, 1+2, 2+1."
            }
        ],
        "test_cases": [
            {"input": "2\n", "expected_output": "2\n", "is_hidden": False},
            {"input": "3\n", "expected_output": "3\n", "is_hidden": False},
            {"input": "4\n", "expected_output": "5\n", "is_hidden": True},
            {"input": "5\n", "expected_output": "8\n", "is_hidden": True},
            {"input": "10\n", "expected_output": "89\n", "is_hidden": True}
        ]
    },
    {
        "title": "Container With Most Water",
        "difficulty": "MEDIUM",
        "topic": "two pointers",
        "expected_solution_concept": "Two Pointers Greedy Inward Shrink",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Find two vertical lines that form a container storing the maximum amount of water.",
        "problem_statement": "You are given an integer array `height` of length `n`. There are `n` vertical lines drawn such that the two endpoints of the ith line are `(i, 0)` and `(i, height[i])`. Find two lines that together with the x-axis form a container, such that the container contains the most water. Return the maximum amount of water a container can store.",
        "input_format": "A single line with space-separated integers representing heights.",
        "output_format": "A single integer representing the maximum water volume.",
        "constraints": "n == height.length\n2 <= n <= 10^5\n0 <= height[i] <= 10^4",
        "examples": [
            {
                "input": "1 8 6 2 5 4 8 3 7",
                "output": "49",
                "explanation": "Max area is between index 1 (height 8) and index 8 (height 7): min(8, 7) * (8 - 1) = 7 * 7 = 49."
            }
        ],
        "test_cases": [
            {"input": "1 8 6 2 5 4 8 3 7\n", "expected_output": "49\n", "is_hidden": False},
            {"input": "1 1\n", "expected_output": "1\n", "is_hidden": False},
            {"input": "4 3 2 1 4\n", "expected_output": "16\n", "is_hidden": True},
            {"input": "1 2 1\n", "expected_output": "2\n", "is_hidden": True}
        ]
    },
    {
        "title": "Longest Increasing Subsequence",
        "difficulty": "HARD",
        "topic": "dynamic programming",
        "expected_solution_concept": "Patience Sorting / Binary Search (O(n log n))",
        "time_limit": 2.0,
        "memory_limit": 128,
        "description": "Find the length of the longest strictly increasing subsequence in an array.",
        "problem_statement": "Given an integer array `nums`, return the length of the longest strictly increasing subsequence. A subsequence is a sequence that can be derived from an array by deleting some or no elements without changing the order of the remaining elements.",
        "input_format": "A single line with space-separated integers.",
        "output_format": "A single integer representing max subsequence length.",
        "constraints": "1 <= nums.length <= 2500\n-10^4 <= nums[i] <= 10^4",
        "examples": [
            {
                "input": "10 9 2 5 3 7 101 18",
                "output": "4",
                "explanation": "The longest increasing subsequence is [2, 3, 7, 101], therefore length is 4."
            },
            {
                "input": "0 1 0 3 2 3",
                "output": "4",
                "explanation": "The longest increasing subsequence is [0, 1, 2, 3], length 4."
            }
        ],
        "test_cases": [
            {"input": "10 9 2 5 3 7 101 18\n", "expected_output": "4\n", "is_hidden": False},
            {"input": "0 1 0 3 2 3\n", "expected_output": "4\n", "is_hidden": False},
            {"input": "7 7 7 7 7 7 7\n", "expected_output": "1\n", "is_hidden": True},
            {"input": "1 3 6 7 9 4 10 5 6\n", "expected_output": "6\n", "is_hidden": True}
        ]
    }
]

def seed_expanded_coding_bank(db: Session):
    """
    Seeds non-duplicate Easy, Medium, and Hard coding questions covering
    arrays, strings, searching, sorting, recursion, linked lists, stacks, queues,
    sliding window, two pointers, and dynamic programming with full test cases.
    """
    for prob_data in EXPANDED_CODING_PROBLEMS:
        existing = db.query(CodingProblem).filter(CodingProblem.title == prob_data["title"]).first()
        if existing:
            # Update fields if missing
            if not existing.problem_statement:
                existing.problem_statement = prob_data["problem_statement"]
                existing.input_format = prob_data["input_format"]
                existing.output_format = prob_data["output_format"]
                existing.constraints = prob_data["constraints"]
                existing.examples = prob_data["examples"]
                existing.expected_solution_concept = prob_data["expected_solution_concept"]
                existing.topic = prob_data["topic"]
                db.commit()
            continue

        problem = CodingProblem(
            title=prob_data["title"],
            description=prob_data["description"],
            difficulty=prob_data["difficulty"],
            problem_statement=prob_data["problem_statement"],
            input_format=prob_data["input_format"],
            output_format=prob_data["output_format"],
            constraints=prob_data["constraints"],
            examples=prob_data["examples"],
            expected_solution_concept=prob_data["expected_solution_concept"],
            topic=prob_data["topic"],
            allowed_languages=["python", "cpp", "c", "java", "javascript"],
            time_limit=prob_data["time_limit"],
            memory_limit=prob_data["memory_limit"]
        )
        db.add(problem)
        db.commit()
        db.refresh(problem)

        for tc_data in prob_data["test_cases"]:
            tc = TestCase(
                problem_id=problem.id,
                input=tc_data["input"],
                expected_output=tc_data["expected_output"],
                is_hidden=tc_data["is_hidden"]
            )
            db.add(tc)

        db.commit()
        logger.info(f"[Seed] Added coding problem '{problem.title}' with {len(prob_data['test_cases'])} test cases.")

    print(f"[Seed] Expanded coding question bank verified ({len(EXPANDED_CODING_PROBLEMS)} problems).")
