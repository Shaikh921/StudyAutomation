from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.dsa import DSAQuestion, DSAAttempt, DSARevisionSchedule
from app.models.user import User


class DSAService:
    @staticmethod
    def record_attempt(
        db: Session,
        user_id: int,
        question_id: int,
        result: str,  # correct, incorrect, partial, skipped
        answer_text: Optional[str] = None,
        time_taken_seconds: Optional[int] = None,
        confidence: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a DSA attempt and updates the SM-2 spaced-repetition revision schedule.
        Intervals: 1d -> 3d -> 7d -> 14d -> 30d.
        """
        attempt = DSAAttempt(
            question_id=question_id,
            user_id=user_id,
            attempted_at=datetime.now(timezone.utc),
            answer_text=answer_text,
            result=result.lower(),
            time_taken_seconds=time_taken_seconds,
            confidence=confidence,
            notes=notes
        )
        db.add(attempt)

        # Update or create revision schedule
        rev = db.query(DSARevisionSchedule).filter(
            DSARevisionSchedule.user_id == user_id,
            DSARevisionSchedule.question_id == question_id
        ).first()

        now = datetime.now(timezone.utc)

        if not rev:
            rev = DSARevisionSchedule(
                user_id=user_id,
                question_id=question_id,
                last_attempted=now,
                next_revision=now + timedelta(days=1),
                interval_days=1.0,
                ease_score=2.5,
                consecutive_correct=0,
                priority=1
            )
            db.add(rev)

        rev.last_attempted = now

        # SM-2 Spaced repetition logic
        res_clean = result.lower().strip()
        if res_clean == "correct":
            rev.consecutive_correct += 1
            if rev.consecutive_correct == 1:
                rev.interval_days = 1.0
            elif rev.consecutive_correct == 2:
                rev.interval_days = 3.0
            elif rev.consecutive_correct == 3:
                rev.interval_days = 7.0
            elif rev.consecutive_correct == 4:
                rev.interval_days = 14.0
            else:
                rev.interval_days = 30.0
            
            if confidence and confidence >= 4:
                rev.ease_score = min(3.5, rev.ease_score + 0.1)
        elif res_clean == "partial":
            rev.interval_days = 1.5
            rev.priority = 2
        else:  # incorrect or skipped
            rev.consecutive_correct = 0
            rev.interval_days = 1.0
            rev.ease_score = max(1.3, rev.ease_score - 0.2)
            rev.priority = 3  # High priority revision

        rev.next_revision = now + timedelta(days=rev.interval_days)
        db.commit()
        db.refresh(attempt)

        return {
            "attempt_id": attempt.id,
            "result": attempt.result,
            "next_revision": rev.next_revision.isoformat(),
            "interval_days": rev.interval_days,
            "consecutive_correct": rev.consecutive_correct
        }

    @staticmethod
    def get_progress(db: Session, user_id: int) -> Dict[str, Any]:
        total_questions = db.query(DSAQuestion).count()
        attempts = db.query(DSAAttempt).filter(DSAAttempt.user_id == user_id).all()
        
        attempted_q_ids = set(a.question_id for a in attempts)
        correct_q_ids = set(a.question_id for a in attempts if a.result == "correct")

        accuracy = (len(correct_q_ids) / len(attempted_q_ids) * 100) if attempted_q_ids else 0.0

        return {
            "total_questions_in_bank": total_questions,
            "total_attempted": len(attempted_q_ids),
            "total_solved_correctly": len(correct_q_ids),
            "accuracy_percentage": round(accuracy, 1),
            "due_for_revision": DSAService.get_due_revisions_count(db, user_id)
        }

    @staticmethod
    def get_due_revisions_count(db: Session, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        return db.query(DSARevisionSchedule).filter(
            DSARevisionSchedule.user_id == user_id,
            DSARevisionSchedule.next_revision <= now
        ).count()

    @staticmethod
    def get_weak_topics(db: Session, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        results = db.query(
            DSAQuestion.topic,
            func.count(DSAAttempt.id).label("total_attempts"),
            func.sum(case((DSAAttempt.result == 'correct', 1), else_=0)).label("correct_attempts")
        ).join(DSAAttempt, DSAQuestion.id == DSAAttempt.question_id)\
         .filter(DSAAttempt.user_id == user_id)\
         .group_by(DSAQuestion.topic).all()

        weak = []
        for r in results:
            topic, total, correct = r[0], r[1], r[2] or 0
            acc = (correct / total) * 100 if total > 0 else 0
            if acc < 70:
                weak.append({
                    "topic": topic,
                    "attempts": total,
                    "accuracy": round(acc, 1),
                    "priority": "High" if acc < 50 else "Medium"
                })

        weak.sort(key=lambda x: x["accuracy"])
        return weak[:limit]

    @staticmethod
    def get_daily_dsa_questions(db: Session, user_id: int, topic_hint: str = "Arrays", count: int = 4) -> List[Dict[str, Any]]:
        """
        Selects daily questions according to priority:
        1. Due for revision
        2. Weak topics
        3. Current roadmap topic
        4. New unattempted questions
        """
        now = datetime.now(timezone.utc)
        selected_questions = []
        selected_ids = set()

        # 1. Due Revisions
        revisions = db.query(DSAQuestion).join(DSARevisionSchedule)\
            .filter(DSARevisionSchedule.user_id == user_id, DSARevisionSchedule.next_revision <= now)\
            .limit(count).all()
        for q in revisions:
            selected_questions.append(q)
            selected_ids.add(q.id)

        # 2. Weak Topics
        if len(selected_questions) < count:
            weak_topics = DSAService.get_weak_topics(db, user_id)
            for wt in weak_topics:
                if len(selected_questions) >= count:
                    break
                w_qs = db.query(DSAQuestion).filter(
                    DSAQuestion.topic.ilike(f"%{wt['topic']}%"),
                    ~DSAQuestion.id.in_(selected_ids)
                ).limit(count - len(selected_questions)).all()
                for q in w_qs:
                    selected_questions.append(q)
                    selected_ids.add(q.id)

        # 3. Current Roadmap Topic
        if len(selected_questions) < count:
            topic_qs = db.query(DSAQuestion).filter(
                DSAQuestion.topic.ilike(f"%{topic_hint}%"),
                ~DSAQuestion.id.in_(selected_ids)
            ).limit(count - len(selected_questions)).all()
            for q in topic_qs:
                selected_questions.append(q)
                selected_ids.add(q.id)

        # 4. Fallback: Any new questions
        if len(selected_questions) < count:
            all_qs = db.query(DSAQuestion).filter(~DSAQuestion.id.in_(selected_ids)).limit(count - len(selected_questions)).all()
            for q in all_qs:
                selected_questions.append(q)
                selected_ids.add(q.id)

        return [
            {
                "id": q.id,
                "title": q.question_text,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "pattern": q.pattern or q.topic
            }
            for q in selected_questions[:count]
        ]
