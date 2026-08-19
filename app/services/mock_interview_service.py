from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

from app.services.gemini_service import GeminiService


class MockInterviewService:
    ROUNDS = [
        {"round_num": 1, "name": "Introduction & Career Goals", "category": "HR/Intro", "question_count": 1},
        {"round_num": 2, "name": "DSA & Problem Solving", "category": "DSA", "question_count": 1},
        {"round_num": 3, "name": "Core CSE Fundamentals (OS/DBMS/CN/OOP)", "category": "Core CSE", "question_count": 1},
        {"round_num": 4, "name": "Python Technical Mastery & SQL Queries", "category": "Python & SQL", "question_count": 1},
        {"round_num": 5, "name": "Machine Learning Fundamentals", "category": "Machine Learning", "question_count": 1},
        {"round_num": 6, "name": "Portfolio Project Deep-Dive (SentinelShield / ApadaMitra)", "category": "Project", "question_count": 1},
        {"round_num": 7, "name": "HR & Behavioral Scenarios", "category": "HR/Behavioral", "question_count": 1},
    ]

    def __init__(self):
        self.gemini = GeminiService()

    def get_round_question(self, round_num: int, project_name: str = "SentinelShield") -> Dict[str, Any]:
        round_num = max(1, min(7, round_num))
        round_info = self.ROUNDS[round_num - 1]

        questions_db = {
            1: "Walk me through your background as a CSE student, your technical domain, and why you are targeting software/ML engineering roles.",
            2: "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`. Explain your approach, time complexity, and edge cases.",
            3: "Explain the difference between a Process and a Thread in Operating Systems. How does the CPU handle context switching and shared memory?",
            4: "Write a SQL query using Window Functions to find the 2nd highest salary per department from an `employees` table (`id`, `dept_id`, `salary`). Also explain Python decorator mechanics under the hood.",
            5: "How do you handle an imbalanced classification dataset in Machine Learning? Compare Precision, Recall, and F1-Score in this scenario.",
            6: f"Walk me through the architecture of your portfolio project '{project_name}'. What were the main technical challenges, database trade-offs, and security considerations?",
            7: "Describe a situation where you encountered a critical technical bug or project conflict under a tight deadline. How did you resolve it?"
        }

        q_text = questions_db.get(round_num, f"Explain a core technical concept in {round_info['category']}.")

        return {
            "round_num": round_num,
            "round_name": round_info["name"],
            "category": round_info["category"],
            "question": q_text,
            "total_rounds": 7
        }

    def evaluate_round_answer(self, round_num: int, question: str, candidate_answer: str) -> Dict[str, Any]:
        round_num = max(1, min(7, round_num))
        round_info = self.ROUNDS[round_num - 1]

        eval_res = self.gemini.evaluate_interview_answer(
            question_text=question,
            user_answer=candidate_answer,
            category=round_info["category"]
        )

        eval_res["round_num"] = round_num
        eval_res["round_name"] = round_info["name"]
        return eval_res

    def generate_final_interview_report(self, round_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        scores = [e.get("score", 7.0) for e in round_evaluations]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 7.0

        # Sub-scores mapping
        dsa_score = round(scores[1], 1) if len(scores) > 1 else avg_score
        core_score = round(scores[2], 1) if len(scores) > 2 else avg_score
        py_sql_score = round(scores[3], 1) if len(scores) > 3 else avg_score
        ml_score = round(scores[4], 1) if len(scores) > 4 else avg_score
        project_score = round(scores[5], 1) if len(scores) > 5 else avg_score
        hr_score = round(scores[0] + scores[6], 1) / 2.0 if len(scores) > 6 else avg_score

        tech_score = round((dsa_score + core_score + py_sql_score + ml_score + project_score) / 5.0, 1)
        comm_score = round((hr_score + avg_score) / 2.0, 1)

        weak_areas = []
        if dsa_score < 7.0: weak_areas.append("DSA & Algorithmic Optimization")
        if core_score < 7.0: weak_areas.append("Core CSE Systems (OS/DBMS/CN)")
        if py_sql_score < 7.0: weak_areas.append("SQL Window Functions & Python Mechanics")
        if ml_score < 7.0: weak_areas.append("Machine Learning Metrics & Evaluation")
        if project_score < 7.0: weak_areas.append("Project Architecture & Trade-Off Pitch")

        recommendation = "HIRE / PLACEMENT READY" if avg_score >= 7.5 else "NEEDS REVISION BEFORE PLACEMENT"

        return {
            "overall_score": avg_score,
            "technical_score": tech_score,
            "communication_score": comm_score,
            "scores_breakdown": {
                "dsa": dsa_score,
                "core_cse": core_score,
                "python_sql": py_sql_score,
                "ml": ml_score,
                "project": project_score,
                "hr": hr_score
            },
            "weak_areas": weak_areas if weak_areas else ["None! Excellent performance across all 7 rounds."],
            "recommendation": recommendation,
            "revision_roadmap": [
                f"1. Focus next 3 days on: {weak_areas[0]}" if weak_areas else "1. Maintain daily speed practice.",
                "2. Practice 60-second concise answer delivery without pauses.",
                "3. Re-verify time/space complexity statements."
            ]
        }
