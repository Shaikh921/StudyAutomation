from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer
from app.services.gemini_service import GeminiService


class InterviewService:
    @staticmethod
    def start_interview_session(db: Session, user_id: int, category: str = "Mixed") -> InterviewSession:
        session = InterviewSession(
            user_id=user_id,
            category=category,
            status="in_progress"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_next_question(category: str, day_number: int = 1) -> Dict[str, Any]:
        """
        Retrieves targeted interview question based on category and roadmap day.
        """
        questions_pool = {
            "DBMS": "Explain the difference between 3NF and BCNF. Provide a real-world scenario where BCNF is required.",
            "OS": "Explain how virtual memory is implemented using paging. What causes a page fault and how is it resolved?",
            "CN": "Walk me through the full TCP three-way handshake process. Why is a 2-way handshake insufficient?",
            "OOP": "Compare abstract classes and interfaces in Python/Java. When would you choose one over the other?",
            "Python": "Explain the difference between deep copy and shallow copy in Python. How does Python manage memory?",
            "SQL": "How do Window functions like DENSE_RANK() differ from ROW_NUMBER()? Write a query concept to find the 2nd highest salary.",
            "ML": "Explain the Bias-Variance tradeoff. How do regularization techniques (L1 vs L2) mitigate overfitting?",
            "HR": "Tell me about a time when you had to debug a difficult technical issue under tight deadlines.",
            "Projects": "Explain the architecture of your primary project (e.g. SentinelShield / ApadaMitra / EnviroScan). What was the biggest trade-off you made?"
        }
        
        q_text = questions_pool.get(category, f"Explain key core concepts of {category} and state their practical applications.")
        return {
            "category": category,
            "question_text": q_text,
            "hints": "Structure your answer with: 1. Core definition, 2. Key components, 3. Real-world example/trade-off."
        }

    @staticmethod
    def submit_and_evaluate_answer(
        db: Session,
        session_id: int,
        question_text: str,
        category: str,
        user_answer: str
    ) -> Dict[str, Any]:
        gemini = GeminiService()
        eval_result = gemini.evaluate_interview_answer(question_text, user_answer, category)

        answer_record = InterviewAnswer(
            session_id=session_id,
            question_text=question_text,
            category=category,
            user_answer=user_answer,
            evaluation_score=eval_result.get("score", 7.0),
            correctness=eval_result.get("evaluation", ""),
            missing_points=eval_result.get("missing_points", ""),
            follow_up_question=eval_result.get("follow_up_question", "")
        )
        db.add(answer_record)
        db.commit()
        db.refresh(answer_record)

        return {
            "answer_id": answer_record.id,
            "score": answer_record.evaluation_score,
            "evaluation": answer_record.correctness,
            "missing_points": answer_record.missing_points,
            "follow_up_question": answer_record.follow_up_question
        }
