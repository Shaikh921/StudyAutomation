from datetime import date, datetime, timezone
import zoneinfo
from typing import Dict, Any, List, Optional

KOLKATA_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")


class RoadmapService:
    @staticmethod
    def get_today_kolkata() -> date:
        """
        Returns today's date in Asia/Kolkata timezone.
        """
        return datetime.now(KOLKATA_TZ).date()

    @staticmethod
    def calculate_current_day(user=None, start_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculate current day number and phase based on program start date and program status.
        If user has not started the program (program_status == "NOT_STARTED"), returns 0/Not Started.
        """
        today = RoadmapService.get_today_kolkata()

        # Handle user object if passed
        status = "NOT_STARTED"
        start_date_obj = None

        if user:
            status = getattr(user, "program_status", "NOT_STARTED") or "NOT_STARTED"
            if user.program_start_date:
                if isinstance(user.program_start_date, datetime):
                    start_date_obj = user.program_start_date.date()
                else:
                    start_date_obj = user.program_start_date
        elif start_date:
            status = "ACTIVE"
            start_date_obj = start_date

        if status == "NOT_STARTED" or not start_date_obj:
            return {
                "status": "NOT_STARTED",
                "is_started": False,
                "program_start_date": None,
                "current_day": 0,
                "current_phase": 0,
                "phase_name": "Program Not Started",
                "mode_name": "Standby Mode",
                "days_completed": 0,
                "days_remaining": 60,
                "completion_percentage": 0.0,
                "is_sprint_mode": False,
                "is_final_mode": False,
            }

        delta = (today - start_date_obj).days
        current_day = delta + 1

        if current_day > 60:
            status = "COMPLETED"
            current_day = 60
            days_completed = 60
            days_remaining = 0
            completion_percentage = 100.0
        elif current_day < 1:
            current_day = 1
            days_completed = 0
            days_remaining = 59
            completion_percentage = 1.7
        else:
            days_completed = current_day - 1
            days_remaining = 60 - current_day
            completion_percentage = round((days_completed / 60.0) * 100, 1)

        if current_day <= 15:
            phase = 1
            phase_name = "Phase 1 — Foundation (Days 1–15)"
            mode_name = "Foundation Learning Mode"
        elif current_day <= 30:
            phase = 2
            phase_name = "Phase 2 — Core Data Structures & Systems (Days 16–30)"
            mode_name = "Core Systems Practice Mode"
        elif current_day <= 45:
            phase = 3
            phase_name = "Phase 3 — Advanced Topics & Mastery (Days 31–45)"
            mode_name = "Advanced Mastery & Revision Mode"
        elif current_day <= 53:
            phase = 4
            phase_name = "Phase 4 — Interview Sprint (Days 46–60)"
            mode_name = "🚀 INTERVIEW SPRINT MODE (Days 46–53)"
        else:
            phase = 4
            phase_name = "Phase 4 — Final Interview Sprint (Days 54–60)"
            mode_name = "🔥 FINAL INTERVIEW MODE (Days 54–60)"

        return {
            "status": status,
            "is_started": True,
            "program_start_date": start_date_obj.isoformat(),
            "current_day": current_day,
            "current_phase": phase,
            "phase_name": phase_name,
            "mode_name": mode_name,
            "days_completed": days_completed,
            "days_remaining": days_remaining,
            "completion_percentage": completion_percentage,
            "is_sprint_mode": current_day >= 46,
            "is_final_mode": current_day >= 54,
        }

    @staticmethod
    def get_day_curriculum(day_number: int) -> Dict[str, Any]:
        day_number = max(1, min(60, day_number))
        
        # Phase 1: Days 1-15 Foundation
        if day_number <= 15:
            dsa_topics = ["Arrays", "Strings", "Hashing", "Two Pointers", "Sliding Window", "Basic Recursion"]
            aptitude_topics = ["Percentages", "Ratio & Proportion", "Average", "Profit & Loss", "Simple Interest & CI", "Time & Work", "Speed, Distance & Time"]
            core_topics = ["OOP Fundamentals", "DBMS Fundamentals", "OS Fundamentals", "Computer Networks Fundamentals"]
            python_topics = ["Functions & Arguments", "Lists & Tuples", "Dictionaries & Sets", "OOP in Python", "Exception Handling"]
            ml_topics = ["ML Basics & Pipelines", "Supervised vs Unsupervised", "Regression vs Classification", "Train/Test Split & Features", "Overfitting vs Underfitting"]

            idx = (day_number - 1) % len(dsa_topics)
            apt_idx = (day_number - 1) % len(aptitude_topics)
            core_idx = (day_number - 1) % len(core_topics)
            py_idx = (day_number - 1) % len(python_topics)
            ml_idx = (day_number - 1) % len(ml_topics)

            return {
                "day_number": day_number,
                "phase": 1,
                "mode": "Foundation Mode",
                "dsa_topic": dsa_topics[idx],
                "dsa_target_count": 4,
                "aptitude_topic": aptitude_topics[apt_idx],
                "aptitude_question_count": 15,
                "core_subject": core_topics[core_idx].split()[0],
                "core_topics": core_topics[core_idx],
                "core_question_count": 5,
                "python_topic": python_topics[py_idx],
                "python_question_count": 3,
                "sql_topic": "Basic SELECT, WHERE, ORDER BY, Operators",
                "sql_question_count": 3,
                "ml_topic": ml_topics[ml_idx],
                "ml_question_count": 3,
                "communication_task": "Practice 60-second self-introduction clear voice recording",
                "project_task": "Prepare architecture diagram and technical pitch for SentinelShield / portfolio project",
                "interview_task": "Review basic HR question: 'Tell me about yourself'",
                "job_application_target": 5,
                "mock_interview_today": False,
                "objectives": f"Phase 1 Foundation Day {day_number}: Master {dsa_topics[idx]} and core fundamentals.",
            }

        # Phase 2: Days 16-30 Core Systems
        elif day_number <= 30:
            dsa_topics = ["Linked List", "Stack", "Queue", "Binary Search", "Sorting Algorithms", "Recursion", "Backtracking"]
            dbms_topics = ["Keys & Constraints", "Normalization (1NF-3NF, BCNF)", "SQL Joins", "Transactions & ACID", "Indexing & B-Trees"]
            os_topics = ["Process vs Thread", "CPU Scheduling Algorithms", "Deadlock & Prevention", "Memory Management", "Virtual Memory & Paging"]
            cn_topics = ["OSI 7-Layer Model", "TCP/IP Protocol Suite", "TCP vs UDP Handshake", "HTTP vs HTTPS & SSL", "DNS & Subnetting Basics"]
            ml_topics = ["Linear Regression", "Logistic Regression", "Decision Trees", "Random Forest", "KNN & SVM Basics", "Evaluation Metrics (Precision, Recall, F1)"]

            sub_day = day_number - 15
            idx = (sub_day - 1) % len(dsa_topics)
            dbms_idx = (sub_day - 1) % len(dbms_topics)
            os_idx = (sub_day - 1) % len(os_topics)
            cn_idx = (sub_day - 1) % len(cn_topics)
            ml_idx = (sub_day - 1) % len(ml_topics)

            return {
                "day_number": day_number,
                "phase": 2,
                "mode": "Core Systems Practice Mode",
                "dsa_topic": dsa_topics[idx],
                "dsa_target_count": 4,
                "aptitude_topic": "Permutation & Combination / Probability",
                "aptitude_question_count": 20,
                "core_subject": "Systems & Database",
                "core_topics": f"DBMS: {dbms_topics[dbms_idx]} | OS: {os_topics[os_idx]} | CN: {cn_topics[cn_idx]}",
                "core_question_count": 5,
                "python_topic": "Generators, Iterators, & Decorators",
                "python_question_count": 3,
                "sql_topic": f"SQL: {dbms_topics[dbms_idx]}",
                "sql_question_count": 4,
                "ml_topic": ml_topics[ml_idx],
                "ml_question_count": 3,
                "communication_task": "Explain a complex algorithm out loud in simple terms without reading notes",
                "project_task": "Document database design and API flow for ApadaMitra / portfolio project",
                "interview_task": "Practice scenario question: 'Describe a challenging bug you solved'",
                "job_application_target": 5,
                "mock_interview_today": (day_number % 3 == 0),
                "objectives": f"Phase 2 Systems Day {day_number}: Deep dive into {dsa_topics[idx]} and system concepts.",
            }

        # Phase 3: Days 31-45 Advanced Topics & Mastery
        elif day_number <= 45:
            dsa_topics = ["Trees & Traversals", "Binary Search Tree (BST)", "Heap & Priority Queue", "Graphs & BFS/DFS", "Greedy Algorithms", "Dynamic Programming Fundamentals"]
            ml_topics = ["Feature Engineering", "Data Preprocessing & Scaling", "Model Evaluation & Metrics", "Cross-Validation Techniques", "Bias vs Variance Tradeoff", "Hyperparameter Tuning"]
            python_topics = ["Advanced OOP & Magic Methods", "REST API Consumption & Requests", "File I/O & JSON Processing", "Concurrency & Threading Basics"]
            sql_topics = ["Complex JOINs & Self Joins", "GROUP BY & HAVING Clause", "Subqueries & Correlated Subqueries", "Window Functions (ROW_NUMBER, RANK, DENSE_RANK)"]

            sub_day = day_number - 30
            idx = (sub_day - 1) % len(dsa_topics)
            ml_idx = (sub_day - 1) % len(ml_topics)
            py_idx = (sub_day - 1) % len(python_topics)
            sql_idx = (sub_day - 1) % len(sql_topics)

            return {
                "day_number": day_number,
                "phase": 3,
                "mode": "Advanced Mastery Mode",
                "dsa_topic": dsa_topics[idx],
                "dsa_target_count": 3,
                "aptitude_topic": "Timed Mixed Aptitude Practice Set",
                "aptitude_question_count": 20,
                "core_subject": "Advanced Core & Systems Design",
                "core_topics": "System Architecture, Design Patterns, Scalability Scenarios",
                "core_question_count": 5,
                "python_topic": python_topics[py_idx],
                "python_question_count": 4,
                "sql_topic": sql_topics[sql_idx],
                "sql_question_count": 4,
                "ml_topic": ml_topics[ml_idx],
                "ml_question_count": 4,
                "communication_task": "Practice 2-minute concise technical pitch of EnviroScan / portfolio project",
                "project_task": "Prepare trade-off & challenge response for your primary project",
                "interview_task": "Practice HR question: 'Where do you see yourself in 3 years?'",
                "job_application_target": 5,
                "mock_interview_today": (day_number % 2 == 0),
                "objectives": f"Phase 3 Mastery Day {day_number}: Advanced {dsa_topics[idx]} & SQL Window Functions.",
            }

        # Phase 4 Sprint (Days 46-53) & Final Mode (Days 54-60)
        else:
            is_final_sprint = (day_number >= 54)
            sub_day = day_number - 45
            
            return {
                "day_number": day_number,
                "phase": 4,
                "mode": "🔥 FINAL INTERVIEW MODE" if is_final_sprint else "🚀 INTERVIEW SPRINT MODE",
                "dsa_topic": "Mixed Placement-Ready Timed DSA Problems",
                "dsa_target_count": 2 if is_final_sprint else 3,
                "aptitude_topic": "Comprehensive Timed Aptitude Speed Test",
                "aptitude_question_count": 20 if is_final_sprint else 25,
                "core_subject": "Full CSE Interview Simulation",
                "core_topics": "Mixed Core CSE Rapid-fire (OS, DBMS, CN, OOP)",
                "core_question_count": 10 if is_final_sprint else 8,
                "python_topic": "Python Interview Edge-Cases & Code Tricks",
                "python_question_count": 5,
                "sql_topic": "Complex SQL Query Building & Optimization",
                "sql_question_count": 5,
                "ml_topic": "End-to-End ML Pipeline & Model Selection Interview Scenarios",
                "ml_question_count": 5,
                "communication_task": "Full Mock Technical & Behavioral Interview Practice",
                "project_task": "End-to-End Project Walkthrough (SentinelShield / ApadaMitra / EnviroScan)",
                "interview_task": "Live Mock Interview Simulation Day",
                "job_application_target": 5,
                "mock_interview_today": True if is_final_sprint and (day_number % 2 == 0) else True,
                "objectives": f"Phase 4 Interview Sprint Day {day_number}: High-intensity mock interview, timed DSA & placement applications.",
            }

    @staticmethod
    def get_topic_detail(category: str, topic_name: str) -> Dict[str, Any]:
        category_clean = category.lower().strip()

        details_db = {
            "dsa": {
                "title": f"💻 DSA Deep Dive: {topic_name}",
                "estimated_time": "2.0 - 2.5 Hours",
                "key_concepts": [
                    "Pattern Recognition: Identify when to apply this technique within 5 minutes.",
                    "Core Algorithm Steps & Invariants: State time and space complexity upfront.",
                    "Edge Cases: Empty inputs, single elements, negative numbers, overflow, duplicate values.",
                    "Optimized vs Brute Force: Walk through how to reduce O(N^2) to O(N) or O(N log N)."
                ],
                "interview_questions": [
                    "How do you optimize time complexity using hash maps / two pointers?",
                    "What are the boundary conditions and array index traps?",
                    "Can you write clean, syntax-error-free code without looking at references?"
                ],
                "action_items": [
                    "1. Solve the recommended problems on LeetCode/GfG.",
                    "2. Explain your solution out loud before typing code.",
                    "3. Record time & space complexity in your notes."
                ]
            },
            "aptitude": {
                "title": f"📐 Aptitude Practice: {topic_name}",
                "estimated_time": "1.0 Hour",
                "key_concepts": [
                    "Formula Mastery: Memorize shortcut formulas for speed.",
                    "Ratio & Fractional Conversions: Convert percentages to fractions (e.g. 16.66% = 1/6).",
                    "Time vs Rate Inverses: Work done = Rate × Time.",
                    "Speed Units: Multiply km/h by 5/18 to get m/s."
                ],
                "interview_questions": [
                    "How fast can you solve a compound interest vs simple interest problem?",
                    "Solve a relative speed problem (two trains moving in opposite directions)."
                ],
                "action_items": [
                    "1. Complete 15-20 timed aptitude practice questions.",
                    "2. Target < 1.5 minutes per question.",
                    "3. Review wrong answers immediately."
                ]
            },
            "core": {
                "title": f"⚙️ Core CSE Subject: {topic_name}",
                "estimated_time": "1.5 Hours",
                "key_concepts": [
                    "Fundamental Definitions & Real-World Analogy.",
                    "Architecture Diagram & Internal Workflow.",
                    "Comparison Questions: (e.g., Process vs Thread, 3NF vs BCNF, TCP vs UDP).",
                    "System Trade-offs & Scaling Bottlenecks."
                ],
                "interview_questions": [
                    "Explain the exact step-by-step workflow (e.g., Page Fault handling or TCP Handshake).",
                    "Why would you choose BCNF over 3NF in a high-concurrency database?",
                    "How does virtual memory protect process address spaces?"
                ],
                "action_items": [
                    "1. Draw the architecture diagram on paper.",
                    "2. Answer 5 core CSE scenario-based interview questions.",
                    "3. Explain concept in 90 seconds without filler words."
                ]
            },
            "python": {
                "title": f"🐍 Python Mastery: {topic_name}",
                "estimated_time": "1.0 Hour",
                "key_concepts": [
                    "Language Mechanics & Memory Model: Reference counting, garbage collection, GIL.",
                    "Mutable vs Immutable Types: Tricky tuple modifications & default parameter traps (`def fn(lst=[])`).",
                    "OOP & Magic Methods: `__init__`, `__str__`, `__repr__`, `__call__`, inheritance & MRO.",
                    "Generators & Iterators: Memory efficiency of `yield` over lists."
                ],
                "interview_questions": [
                    "What is the difference between deepcopy and shallow copy in Python?",
                    "How do decorators work under the hood using first-class functions?",
                    "Explain how `*args` and `**kwargs` are unpacked."
                ],
                "action_items": [
                    "1. Code 3 Python edge-case code snippets in REPL.",
                    "2. Understand time complexity of list/dict operations in Python.",
                    "3. Practice writing custom decorators & generator functions."
                ]
            },
            "sql": {
                "title": f"🗄️ SQL & Databases: {topic_name}",
                "estimated_time": "1.0 Hour",
                "key_concepts": [
                    "Query Execution Order: FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY.",
                    "JOIN Types: INNER, LEFT, RIGHT, FULL OUTER, CROSS, SELF JOIN.",
                    "Aggregation & Grouping: WHERE vs HAVING filter rules.",
                    "Window Functions: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `PARTITION BY`."
                ],
                "interview_questions": [
                    "Write a query to find the N-th highest salary using Window Functions.",
                    "What is the difference between `WHERE` and `HAVING`?",
                    "How do indexes speed up `SELECT` but slow down `INSERT`/`UPDATE`?"
                ],
                "action_items": [
                    "1. Write and execute SQL queries on DB fiddle or local SQLite.",
                    "2. Practice 3 window function query problems.",
                    "3. Check execution plan and indexing strategies."
                ]
            },
            "ml": {
                "title": f"🤖 Machine Learning: {topic_name}",
                "estimated_time": "1.0 Hour",
                "key_concepts": [
                    "Mathematical Intuition: Loss functions, cost optimization, gradient descent.",
                    "Supervised vs Unsupervised: Classification, Regression, Clustering.",
                    "Evaluation Metrics: Accuracy, Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix.",
                    "Overfitting vs Underfitting: Bias-Variance Tradeoff, L1 (Lasso) vs L2 (Ridge) Regularization."
                ],
                "interview_questions": [
                    "When would you choose F1-score over Accuracy in imbalanced datasets?",
                    "How does Decision Tree handle missing values and overfitting?",
                    "Explain the difference between L1 and L2 regularization."
                ],
                "action_items": [
                    "1. Implement a baseline model in Scikit-Learn.",
                    "2. Plot train vs validation loss curves.",
                    "3. State pros and cons of the algorithm in interviews."
                ]
            },
            "interview": {
                "title": f"🗣️ Project & HR Practice: {topic_name}",
                "estimated_time": "0.75 Hour",
                "key_concepts": [
                    "STAR Method: Situation, Task, Action, Result.",
                    "Project Pitch Structure: Problem statement -> Architecture -> Your exact role -> Technical trade-offs -> Result.",
                    "Behavioral Questions: Conflict resolution, tight deadlines, handling failure.",
                    "Communication Clarity: Structure answers logically without stuttering or long pauses."
                ],
                "interview_questions": [
                    "Tell me about a time you faced a difficult technical bug and how you resolved it.",
                    "Walk me through the architecture of your primary project (e.g. SentinelShield / ApadaMitra).",
                    "Why do you want to join our engineering team?"
                ],
                "action_items": [
                    "1. Record yourself delivering a 2-minute project elevator pitch.",
                    "2. Practice answering 2 HR questions using the STAR framework.",
                    "3. Listen to your recording and refine technical vocabulary."
                ]
            }
        }

        guide = details_db.get(category_clean, details_db["core"])
        return {
            "category": category,
            "topic_name": topic_name,
            "title": guide["title"],
            "estimated_time": guide["estimated_time"],
            "key_concepts": guide["key_concepts"],
            "interview_questions": guide["interview_questions"],
            "action_items": guide["action_items"]
        }
