from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import json

from app.models.user import User
from app.models.study import StudyPlan, StudySession
from app.models.dsa import DSAQuestion, DSAAttempt, DSARevisionSchedule
from app.models.job import JobApplication
from app.services.roadmap_service import RoadmapService
from app.services.dsa_service import DSAService


class PlannerService:
    @staticmethod
    def generate_daily_plan(db: Session, user: User, target_date: Optional[date] = None) -> Optional[StudyPlan]:
        """
        Generates a personalized daily study plan if program_status is ACTIVE.
        """
        status = getattr(user, "program_status", "NOT_STARTED") or "NOT_STARTED"
        if status == "NOT_STARTED" or not user.program_start_date:
            return None

        target_date = target_date or RoadmapService.get_today_kolkata()
        
        # Check if plan already exists for today
        existing = db.query(StudyPlan).filter(
            StudyPlan.user_id == user.id,
            StudyPlan.plan_date == target_date
        ).first()

        day_calc = RoadmapService.calculate_current_day(user=user)
        day_number = day_calc["current_day"]
        phase = day_calc["current_phase"]
        curriculum = RoadmapService.get_day_curriculum(day_number)

        # 1. Fetch Weak Topics
        weak_topics = DSAService.get_weak_topics(db, user.id)
        weak_topic_names = [w["topic"] for w in weak_topics]

        # 2. Fetch Due DSA Revisions
        now = datetime.now(timezone.utc)
        due_revisions = db.query(DSARevisionSchedule).filter(
            DSARevisionSchedule.user_id == user.id,
            DSARevisionSchedule.next_revision <= now
        ).all()
        due_q_ids = [r.question_id for r in due_revisions[:3]]

        # 3. Fetch Select DSA Questions for Today
        target_q_count = curriculum.get("dsa_target_count", 4)
        selected_dsa = DSAService.get_daily_dsa_questions(db, user.id, curriculum["dsa_topic"], count=target_q_count)
        selected_q_ids = [q["id"] for q in selected_dsa]
        
        all_dsa_ids = list(set(selected_q_ids + due_q_ids))[:5]

        # 4. Check Upcoming Interviews
        upcoming_interviews = db.query(JobApplication).filter(
            JobApplication.user_id == user.id,
            JobApplication.interview_date.isnot(None),
            JobApplication.status.in_(["interview", "assessment"])
        ).all()
        
        interview_task = curriculum["interview_task"]
        if upcoming_interviews:
            closest = min(upcoming_interviews, key=lambda x: x.interview_date)
            days_to_int = (closest.interview_date.date() - target_date).days
            if 0 <= days_to_int <= 7:
                company = closest.job.company if closest.job else "Target Company"
                if days_to_int == 0:
                    interview_task = f"🚨 INTERVIEW DAY: Checklist & final review for {company}!"
                elif days_to_int == 1:
                    interview_task = f"⚡ D-1 INTERVIEW REVISION: Review weak topics & {company} prep pack."
                elif days_to_int == 3:
                    interview_task = f"🎯 D-3 MOCK INTERVIEW: Complete full technical mock for {company}."
                else:
                    interview_task = f"📅 D-{days_to_int} INTERVIEW PREP: Focus on {company} requirements."

        # 5. Missed Task Recovery
        recovery_tasks = []
        if day_number > 1:
            yesterday_date = target_date - timedelta(days=1)
            yesterday_plan = db.query(StudyPlan).filter(
                StudyPlan.user_id == user.id,
                StudyPlan.plan_date == yesterday_date
            ).first()

            if yesterday_plan and yesterday_plan.completed_tasks:
                completed = json.loads(yesterday_plan.completed_tasks)
                all_cats = ["dsa", "aptitude", "core", "python", "sql", "ml", "interview"]
                missed = [c for c in all_cats if c not in completed]
                
                for m_cat in missed[:2]:
                    recovery_tasks.append({
                        "category": m_cat,
                        "title": f"Recovery Slot (30m): Review missed {m_cat.upper()} topic",
                        "duration_hours": 0.5
                    })

        recovery_time = len(recovery_tasks) * 0.5
        total_time = min(10.0, curriculum.get("estimated_total_time", 6.5) + recovery_time)

        if existing:
            existing.day_number = day_number
            existing.phase = phase
            existing.objectives = curriculum["objectives"]
            existing.dsa_topic = curriculum["dsa_topic"]
            existing.dsa_question_ids = json.dumps(all_dsa_ids)
            existing.aptitude_topic = curriculum["aptitude_topic"]
            existing.aptitude_question_count = curriculum["aptitude_question_count"]
            existing.core_subject = curriculum["core_subject"]
            existing.core_topics = curriculum["core_topics"]
            existing.python_topic = curriculum["python_topic"]
            existing.sql_topic = curriculum["sql_topic"]
            existing.ml_topic = curriculum["ml_topic"]
            existing.communication_task = curriculum["communication_task"]
            existing.project_task = curriculum["project_task"]
            existing.interview_task = interview_task
            existing.estimated_total_time = total_time
            existing.recovery_tasks = json.dumps(recovery_tasks)
            db.commit()
            db.refresh(existing)
            return existing

        new_plan = StudyPlan(
            user_id=user.id,
            plan_date=target_date,
            day_number=day_number,
            phase=phase,
            objectives=curriculum["objectives"],
            dsa_topic=curriculum["dsa_topic"],
            dsa_question_ids=json.dumps(all_dsa_ids),
            aptitude_topic=curriculum["aptitude_topic"],
            aptitude_question_count=curriculum["aptitude_question_count"],
            core_subject=curriculum["core_subject"],
            core_topics=curriculum["core_topics"],
            python_topic=curriculum["python_topic"],
            sql_topic=curriculum["sql_topic"],
            ml_topic=curriculum["ml_topic"],
            communication_task=curriculum["communication_task"],
            project_task=curriculum["project_task"],
            interview_task=interview_task,
            estimated_total_time=total_time,
            completed_tasks="[]",
            recovery_tasks=json.dumps(recovery_tasks),
            is_completed=False
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        return new_plan

    @staticmethod
    def get_today_mission_summary(db: Session, user: User) -> Dict[str, Any]:
        day_calc = RoadmapService.calculate_current_day(user=user)

        if not day_calc["is_started"] or day_calc["status"] == "NOT_STARTED":
            return {
                "program_status": "NOT_STARTED",
                "is_started": False,
                "day_number": 0,
                "phase": 0,
                "phase_name": "Program Not Started",
                "mode_name": "Standby Mode",
                "days_completed": 0,
                "days_remaining": 60,
                "completion_percentage": 0.0,
                "objectives": "Program Not Started. Click [START 60-DAY PROGRAM] on dashboard when ready.",
                "estimated_hours": 0,
                "dsa": {"topic": "Not Started", "question_count": 0, "questions": [], "is_completed": False},
                "aptitude": {"topic": "Not Started", "question_count": 0, "is_completed": False},
                "core": {"subject": "Not Started", "topics": "Not Started", "is_completed": False},
                "python": {"topic": "Not Started", "is_completed": False},
                "sql": {"topic": "Not Started", "is_completed": False},
                "ml": {"topic": "Not Started", "is_completed": False},
                "communication": "Not Started",
                "project": "Not Started",
                "interview": {"task": "Not Started", "is_completed": False},
                "recovery_slots": [],
                "completed_tasks": [],
                "is_plan_completed": False
            }

        plan = PlannerService.generate_daily_plan(db, user)
        if not plan:
            return {
                "program_status": user.program_status,
                "is_started": False,
                "day_number": day_calc["current_day"],
                "phase": day_calc["current_phase"],
                "phase_name": day_calc["phase_name"],
                "mode_name": day_calc["mode_name"],
                "days_completed": day_calc["days_completed"],
                "days_remaining": day_calc["days_remaining"],
                "completion_percentage": day_calc["completion_percentage"],
                "objectives": "Program paused or completed.",
                "estimated_hours": 0,
                "dsa": {"topic": "N/A", "question_count": 0, "questions": [], "is_completed": False},
                "aptitude": {"topic": "N/A", "question_count": 0, "is_completed": False},
                "core": {"subject": "N/A", "topics": "N/A", "is_completed": False},
                "python": {"topic": "N/A", "is_completed": False},
                "sql": {"topic": "N/A", "is_completed": False},
                "ml": {"topic": "N/A", "is_completed": False},
                "communication": "N/A",
                "project": "N/A",
                "interview": {"task": "N/A", "is_completed": False},
                "recovery_slots": [],
                "completed_tasks": [],
                "is_plan_completed": False
            }

        q_ids = json.loads(plan.dsa_question_ids or "[]")
        dsa_questions = []
        if q_ids:
            questions = db.query(DSAQuestion).filter(DSAQuestion.id.in_(q_ids)).all()
            dsa_questions = [
                {
                    "id": q.id,
                    "title": q.question_text,
                    "difficulty": q.difficulty,
                    "pattern": q.pattern or q.topic,
                    "topic": q.topic
                }
                for q in questions
            ]

        completed_list = json.loads(plan.completed_tasks or "[]")
        recovery_list = json.loads(plan.recovery_tasks or "[]")

        return {
            "program_status": "ACTIVE",
            "is_started": True,
            "plan_id": plan.id,
            "day_number": plan.day_number,
            "phase": plan.phase,
            "phase_name": day_calc["phase_name"],
            "mode_name": day_calc["mode_name"],
            "days_completed": day_calc["days_completed"],
            "days_remaining": day_calc["days_remaining"],
            "completion_percentage": day_calc["completion_percentage"],
            "objectives": plan.objectives,
            "estimated_hours": plan.estimated_total_time,
            "dsa": {
                "topic": plan.dsa_topic,
                "question_count": len(dsa_questions),
                "questions": dsa_questions,
                "is_completed": "dsa" in completed_list
            },
            "aptitude": {
                "topic": plan.aptitude_topic,
                "question_count": plan.aptitude_question_count,
                "is_completed": "aptitude" in completed_list
            },
            "core": {
                "subject": plan.core_subject,
                "topics": plan.core_topics,
                "is_completed": "core" in completed_list
            },
            "python": {
                "topic": plan.python_topic,
                "is_completed": "python" in completed_list
            },
            "sql": {
                "topic": plan.sql_topic,
                "is_completed": "sql" in completed_list
            },
            "ml": {
                "topic": plan.ml_topic,
                "is_completed": "ml" in completed_list
            },
            "communication": plan.communication_task,
            "project": plan.project_task,
            "interview": {
                "task": plan.interview_task,
                "is_completed": "interview" in completed_list
            },
            "recovery_slots": recovery_list,
            "completed_tasks": completed_list,
            "is_plan_completed": len(completed_list) >= 7
        }
