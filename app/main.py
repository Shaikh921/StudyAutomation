from fastapi import FastAPI, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import date

from app.config import settings
from app.database.database import get_db
from app.database.migrations import init_db
from app.scheduler.scheduler import init_scheduler

from app.api import (
    users, study, dsa, interview, ai, jobs, applications, progress, notifications, system, reminders, mock_interview, focus, backup, telegram_router, program
)
from app.models.user import User
from app.services.roadmap_service import RoadmapService
from app.services.planner_service import PlannerService
from app.services.dsa_service import DSAService
from app.services.job_service import JobApplicationService
from app.services.job_search_service import JobSearchService
from app.models.job import JobListing

app = FastAPI(
    title=settings.APP_NAME,
    version="3.0.0",
    description="60-Day AI-Powered CSE Job Preparation Automation Platform & Career Coach"
)

# Register API Routers
app.include_router(system.router)
app.include_router(program.router)
app.include_router(users.router)
app.include_router(study.router)
app.include_router(dsa.router)
app.include_router(interview.router)
app.include_router(mock_interview.router)
app.include_router(ai.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(progress.router)
app.include_router(notifications.router)
app.include_router(reminders.router)
app.include_router(focus.router)
app.include_router(backup.router)
app.include_router(telegram_router.router)


@app.on_event("startup")
def startup_event():
    init_db()
    # Auto-seed database if empty (e.g. fresh cloud deployment)
    try:
        from app.database.database import SessionLocal
        from app.models.user import User
        from app.models.dsa import DSAQuestion
        from tools.import_dsa_bank import import_questions
        from tools.seed_program import seed_program

        db = SessionLocal()
        user_count = db.query(User).count()
        dsa_count = db.query(DSAQuestion).count()
        db.close()

        if dsa_count == 0:
            print("Auto-importing 250+ DSA question bank...")
            import_questions()
        if user_count == 0:
            print("Auto-seeding default student profile...")
            seed_program()
    except Exception as e:
        print(f"Auto-seed notice: {e}")

    try:
        init_scheduler()
    except Exception as e:
        print(f"Scheduler startup notice: {e}")



@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
def get_dashboard(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>60-Day CSE Job Prep Setup</title>
            <style>
                body { font-family: 'Plus Jakarta Sans', sans-serif; background: #041312; color: #f0fdf4; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
                .card { background: rgba(13, 31, 28, 0.75); border: 1px solid rgba(16, 185, 129, 0.2); padding: 40px; border-radius: 16px; text-align: center; max-width: 500px; }
                code { background: #0a211e; color: #34d399; padding: 6px 12px; border-radius: 6px; font-size: 0.9rem; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2 style="color: #34d399;">🚀 60-Day CSE Job Prep Platform</h2>
                <p style="color: #94a3b8;">System initialized! Please run the seed script to set up your 60-day profile and DSA question bank.</p>
                <p><code>python tools/import_dsa_bank.py && python tools/seed_program.py</code></p>
            </div>
        </body>
        </html>
        """

    prog_status = getattr(user, "program_status", "NOT_STARTED") or "NOT_STARTED"
    day_calc = RoadmapService.calculate_current_day(user=user)
    is_started = day_calc["is_started"]

    summary = PlannerService.get_today_mission_summary(db, user)
    dsa_progress = DSAService.get_progress(db, user.id)
    weak_topics = DSAService.get_weak_topics(db, user.id)
    app_stats = JobApplicationService.get_application_stats(db, user.id)
    
    # Discover fresh live jobs
    job_search = JobSearchService()
    try:
        job_search.discover_and_ingest_jobs(db, user)
    except Exception:
        pass
    top_jobs = db.query(JobListing).order_by(JobListing.relevance_score.desc()).limit(6).all()

    start_date_str = user.program_start_date.strftime("%d %b %Y") if user.program_start_date else "Not Started"
    end_date_str = user.program_end_date.strftime("%d %b %Y") if user.program_end_date else "Not Set"
    progress_pct = day_calc['completion_percentage']

    # NOT_STARTED HERO CARD
    not_started_hero = f"""
    <div class="glass-card" style="text-align: center; padding: 54px 24px; border: 2px dashed var(--accent-emerald); margin-bottom: 28px;">
        <h1 style="color: var(--accent-mint); font-size: 2.2rem; margin-top: 0;">🚀 60-DAY CSE CAREER COACH</h1>
        <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.35); padding: 10px 24px; border-radius: 12px; display: inline-block; margin: 14px 0 24px 0;">
            <span style="color: var(--accent-amber); font-weight: 800; font-size: 1.05rem;">PROGRAM STATUS: NOT STARTED</span>
        </div>
        <p style="color: var(--text-muted); font-size: 1.05rem; max-width: 580px; margin: 0 auto 28px auto; line-height: 1.6;">
            Your strict 60-day placement preparation countdown will start <strong>ONLY</strong> when you explicitly click the button below. Day 1 will lock to the date you click start.
        </p>
        <button onclick="startProgram()" style="background: linear-gradient(135deg, #059669, #10b981); color: white; border: none; font-size: 1.25rem; font-weight: 800; padding: 16px 42px; border-radius: 16px; cursor: pointer; box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4); transition: transform 0.2s;">
            ▶ START 60-DAY PROGRAM NOW
        </button>
    </div>
    """

    active_header_banner = f"""
    <div class="header-banner">
        <div class="header-top">
            <div class="title-area">
                <h1>60-Day CSE Job Preparation Automation Platform</h1>
                <p>Student: <strong>{user.name}</strong> ({user.email}) | Target: <strong>Software & Machine Learning Engineer</strong></p>
            </div>
            <div class="date-controls">
                <span style="font-size: 0.85rem; color: var(--text-muted);">Started: <strong style="color: var(--accent-mint);">{start_date_str}</strong> | Ends: <strong style="color: var(--accent-amber);">{end_date_str}</strong></span>
            </div>
        </div>

        <!-- 60-Day Progress Bar -->
        <div class="progress-container">
            <div class="progress-label">
                <span>DAY {day_calc['current_day']} OF 60 — {day_calc['phase_name']} ({day_calc['mode_name']})</span>
                <span style="color: var(--accent-amber); font-weight: 700;">{progress_pct}% COMPLETED ({day_calc['days_completed']} Days Done, {day_calc['days_remaining']} Left)</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {progress_pct}%;"></div>
            </div>
        </div>
    </div>
    """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>60-Day CSE Job Preparation Platform & AI Career Coach</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-primary: #041312;
                --bg-card: rgba(13, 31, 28, 0.75);
                --border-color: rgba(16, 185, 129, 0.18);
                --border-glow: rgba(16, 185, 129, 0.4);
                --accent-mint: #34d399;
                --accent-emerald: #10b981;
                --accent-amber: #fbbf24;
                --accent-gold: #f59e0b;
                --accent-rose: #f43f5e;
                --text-main: #f0fdf4;
                --text-muted: #94a3b8;
            }}
            * {{ box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }}
            body {{ background-color: var(--bg-primary); color: var(--text-main); margin: 0; padding: 24px; min-height: 100vh; background-image: radial-gradient(circle at 10% 20%, rgba(16, 185, 129, 0.05) 0%, transparent 40%), radial-gradient(circle at 90% 80%, rgba(245, 158, 11, 0.04) 0%, transparent 40%); }}
            .container {{ max-width: 1340px; margin: 0 auto; }}

            /* Navbar Header */
            .header-banner {{
                background: linear-gradient(135deg, rgba(13, 31, 28, 0.95), rgba(6, 20, 18, 0.98));
                backdrop-filter: blur(24px);
                border: 1px solid var(--border-color);
                border-radius: 20px;
                padding: 28px;
                margin-bottom: 28px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            }}
            .header-top {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }}
            .title-area h1 {{ margin: 0; font-size: 1.85rem; font-weight: 800; background: linear-gradient(to right, var(--accent-mint), var(--accent-amber)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .title-area p {{ margin: 6px 0 0 0; color: var(--text-muted); font-size: 0.95rem; }}

            /* 60-Day Progress Bar */
            .progress-container {{ margin-top: 22px; }}
            .progress-label {{ display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px; color: #cbd5e1; }}
            .progress-track {{ background: rgba(0, 0, 0, 0.4); border-radius: 999px; height: 14px; overflow: hidden; position: relative; border: 1px solid rgba(255, 255, 255, 0.05); }}
            .progress-fill {{ background: linear-gradient(90deg, #10b981, #34d399, #f59e0b, #fbbf24); height: 100%; border-radius: 999px; transition: width 0.5s ease; box-shadow: 0 0 12px rgba(52, 211, 153, 0.4); }}

            /* Quick Actions Bar */
            .quick-actions {{ display: flex; gap: 10px; overflow-x: auto; margin-bottom: 24px; padding-bottom: 6px; }}
            .qa-btn {{ background: rgba(13, 31, 28, 0.7); border: 1px solid var(--border-color); color: var(--text-main); padding: 10px 18px; border-radius: 12px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease; white-space: nowrap; display: flex; align-items: center; gap: 6px; }}
            .qa-btn:hover {{ background: rgba(16, 185, 129, 0.2); border-color: var(--accent-mint); color: var(--accent-mint); transform: translateY(-2px); }}

            /* Start Date Controls */
            .date-controls {{ display: flex; align-items: center; gap: 10px; background: rgba(6, 20, 18, 0.8); padding: 8px 16px; border-radius: 12px; border: 1px solid var(--border-color); }}

            /* Navigation Tabs */
            .tabs-nav {{ display: flex; gap: 12px; margin-bottom: 24px; border-bottom: 1px solid var(--border-color); padding-bottom: 14px; overflow-x: auto; }}
            .tab-btn {{ background: rgba(13, 31, 28, 0.5); border: 1px solid var(--border-color); color: var(--text-muted); padding: 11px 22px; border-radius: 12px; font-weight: 600; font-size: 0.9rem; cursor: pointer; transition: all 0.25s ease; }}
            .tab-btn.active, .tab-btn:hover {{ background: rgba(16, 185, 129, 0.15); color: var(--accent-mint); border-color: var(--accent-emerald); box-shadow: 0 4px 14px rgba(16, 185, 129, 0.2); }}

            /* Grid Layout */
            .grid-2 {{ display: grid; grid-template-columns: 2fr 1fr; gap: 24px; }}
            .grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 24px; }}

            /* Cards */
            .glass-card {{
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-color);
                border-radius: 18px;
                padding: 24px;
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
                transition: transform 0.2s, border-color 0.2s;
            }}
            .glass-card:hover {{ border-color: var(--border-glow); }}
            .card-title {{ font-size: 1.1rem; font-weight: 700; color: var(--accent-mint); margin-top: 0; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; }}

            /* Clickable Task Items */
            .task-item {{ background: rgba(6, 20, 18, 0.6); border: 1px solid var(--border-color); padding: 16px 20px; border-radius: 14px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; transition: all 0.25s ease; cursor: pointer; }}
            .task-item:hover {{ background: rgba(13, 31, 28, 0.95); border-color: var(--accent-mint); transform: translateX(4px); box-shadow: 0 4px 20px rgba(16, 185, 129, 0.15); }}
            .task-info font {{ font-weight: 700; color: #f0fdf4; font-size: 1.02rem; display: flex; align-items: center; gap: 8px; }}
            .task-info font::after {{ content: "🔍 Study Guide"; font-size: 0.72rem; color: var(--accent-amber); font-weight: 600; opacity: 0.85; margin-left: 8px; background: rgba(245, 158, 11, 0.12); padding: 2px 8px; border-radius: 6px; }}
            .task-info p {{ margin: 6px 0 0 0; font-size: 0.88rem; color: var(--text-muted); }}
            .check-btn {{ background: rgba(16, 185, 129, 0.18); color: var(--accent-mint); border: 1px solid rgba(16, 185, 129, 0.35); padding: 8px 18px; border-radius: 10px; font-size: 0.82rem; font-weight: 700; cursor: pointer; transition: all 0.2s; }}
            .check-btn:hover {{ background: var(--accent-emerald); color: #041312; box-shadow: 0 0 12px rgba(16, 185, 129, 0.5); }}

            /* AI Chatbox */
            .chat-box {{ display: flex; flex-direction: column; height: 390px; background: rgba(6, 20, 18, 0.85); border-radius: 14px; border: 1px solid var(--border-color); padding: 16px; }}
            .chat-messages {{ flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; margin-bottom: 12px; padding-right: 6px; }}
            .msg {{ padding: 12px 16px; border-radius: 12px; font-size: 0.88rem; max-width: 85%; line-height: 1.5; }}
            .msg.bot {{ background: rgba(13, 31, 28, 0.9); border: 1px solid rgba(16, 185, 129, 0.2); align-self: flex-start; color: #f0fdf4; }}
            .msg.user {{ background: linear-gradient(135deg, #059669, #10b981); align-self: flex-end; color: white; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }}
            .chat-input-area {{ display: flex; gap: 10px; }}
            .chat-input-area input {{ flex: 1; background: #0d2320; border: 1px solid #10b981; color: white; padding: 10px 16px; border-radius: 10px; font-size: 0.88rem; }}
            .chat-input-area button {{ background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #041312; border: none; font-weight: 800; padding: 10px 20px; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3); }}

            /* Modals */
            .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(12px); z-index: 9999; justify-content: center; align-items: center; padding: 20px; }}
            .modal-overlay.active {{ display: flex; }}
            .modal-card {{ background: rgba(13, 31, 28, 0.95); border: 1px solid var(--border-glow); width: 100%; max-width: 680px; max-height: 85vh; border-radius: 20px; padding: 28px; overflow-y: auto; box-shadow: 0 25px 50px rgba(0, 0, 0, 0.6); position: relative; }}
            .modal-header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid var(--border-color); padding-bottom: 16px; margin-bottom: 20px; }}
            .modal-title {{ margin: 0; font-size: 1.35rem; font-weight: 800; color: var(--accent-mint); }}
            .modal-subtitle {{ margin: 4px 0 0 0; font-size: 0.85rem; color: var(--accent-amber); font-weight: 600; }}
            .close-modal {{ background: rgba(255, 255, 255, 0.1); color: var(--text-muted); border: none; font-size: 1.2rem; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
            .close-modal:hover {{ background: var(--accent-rose); color: white; }}

            /* Job Card Items */
            .job-card {{ background: rgba(6, 20, 18, 0.7); border: 1px solid var(--border-color); padding: 18px; border-radius: 14px; transition: border-color 0.2s; }}
            .job-card:hover {{ border-color: var(--accent-amber); }}
            .job-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }}
            .job-title {{ font-weight: 700; color: #f0fdf4; font-size: 0.98rem; margin: 0; }}
            .job-company {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 2px; }}
            .score-pill {{ background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); border: 1px solid rgba(245, 158, 11, 0.35); padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 800; }}
            .job-actions {{ display: flex; justify-content: space-between; align-items: center; margin-top: 14px; pt-2; border-top: 1px solid rgba(255,255,255,0.05); }}
            .apply-link {{ background: linear-gradient(135deg, #059669, #10b981); color: white; text-decoration: none; padding: 7px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 700; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3); }}
            
            /* Stats Pill */
            .stat-pill {{ display: flex; justify-content: space-between; background: rgba(6, 20, 18, 0.6); padding: 12px 18px; border-radius: 12px; border: 1px solid var(--border-color); margin-bottom: 12px; }}
            .stat-pill span {{ color: var(--text-muted); font-size: 0.88rem; }}
            .stat-pill strong {{ font-weight: 700; color: var(--text-main); }}

            @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            {active_header_banner if is_started else not_started_hero}

            <!-- Quick Actions Bar -->
            <div class="quick-actions">
                {f'<button class="qa-btn" style="background: linear-gradient(135deg, #059669, #10b981); color: white;" onclick="startProgram()">🚀 Start 60-Day Program</button>' if not is_started else '<button class="qa-btn" onclick="showTab(\'mission\')">🎯 Today\'s Plan</button>'}
                <button class="qa-btn" onclick="showTab('dsa')">💻 DSA Focus</button>
                <button class="qa-btn" onclick="showTab('ai-tutor')">🤖 Ask Gemini AI</button>
                <button class="qa-btn" onclick="openMockInterviewModal()">🗣️ 7-Round Mock Interview</button>
                <button class="qa-btn" onclick="showTab('jobs')">💼 Live Jobs</button>
                <button class="qa-btn" onclick="openFocusModal()">⏱️ Focus Timer</button>
                <button class="qa-btn" onclick="triggerDatabaseBackup()">💾 Backup Database</button>
            </div>

            <!-- Navigation Tabs -->
            <div class="tabs-nav">
                <button class="tab-btn active" onclick="showTab('mission')">🎯 Today's Mission</button>
                <button class="tab-btn" onclick="showTab('ai-tutor')">🤖 Gemini AI Tutor & Coach</button>
                <button class="tab-btn" onclick="showTab('dsa')">💻 DSA Question Bank ({dsa_progress['total_questions_in_bank']})</button>
                <button class="tab-btn" onclick="showTab('jobs')">💼 Live CSE Job Digest ({len(top_jobs)})</button>
                <button class="tab-btn" onclick="showTab('applications')">📊 Applications Tracker</button>
            </div>

            <!-- Tab 1: Today's Mission -->
            <div id="tab-mission" class="tab-content">
                <div class="grid-2">
                    <div class="glass-card">
                        <div class="card-title">
                            <span>{f"DAY {summary['day_number']} CURRICULUM OBJECTIVES" if is_started else "PROGRAM OBJECTIVES (STANDBY)"}</span>
                            <span style="font-size: 0.8rem; background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); border: 1px solid rgba(245, 158, 11, 0.3); padding: 4px 12px; border-radius: 8px;">Target: {summary['estimated_hours']} Hours</span>
                        </div>
                        <p style="color: #cbd5e1; font-size: 0.95rem; margin-bottom: 20px; line-height: 1.6;">{summary['objectives']}</p>

                        <!-- Clickable Task Items -->
                        <div class="task-item" onclick="openTopicModal('dsa', '{summary['dsa']['topic']}')">
                            <div class="task-info">
                                <font>💻 DSA Focus Pattern</font>
                                <p>{summary['dsa']['topic']} ({summary['dsa']['question_count']} Recommended Problems)</p>
                            </div>
                            <button class="check-btn" onclick="event.stopPropagation(); completeTask('dsa')">Mark Complete</button>
                        </div>

                        <div class="task-item" onclick="openTopicModal('aptitude', '{summary['aptitude']['topic']}')">
                            <div class="task-info">
                                <font>📐 Aptitude Timed Practice</font>
                                <p>{summary['aptitude']['topic']} ({summary['aptitude']['question_count']} Questions)</p>
                            </div>
                            <button class="check-btn" onclick="event.stopPropagation(); completeTask('aptitude')">Mark Complete</button>
                        </div>

                        <div class="task-item" onclick="openTopicModal('core', '{summary['core']['topics']}')">
                            <div class="task-info">
                                <font>⚙️ Core CSE Subject</font>
                                <p>{summary['core']['subject']}: {summary['core']['topics']}</p>
                            </div>
                            <button class="check-btn" onclick="event.stopPropagation(); completeTask('core')">Mark Complete</button>
                        </div>

                        <div class="task-item" onclick="openTopicModal('python', '{summary['python']['topic']}')">
                            <div class="task-info">
                                <font>🐍 Python Technical Mastery</font>
                                <p>{summary['python']['topic']}</p>
                            </div>
                            <button class="check-btn" onclick="event.stopPropagation(); completeTask('python')">Mark Complete</button>
                        </div>

                        <div class="task-item" onclick="openTopicModal('sql', '{summary['sql']['topic']}')">
                            <div class="task-info">
                                <font>🗄️ SQL & Relational Databases</font>
                                <p>{summary['sql']['topic']}</p>
                            </div>
                            <button class="check-btn" onclick="event.stopPropagation(); completeTask('sql')">Mark Complete</button>
                        </div>

                        <div class="task-item" onclick="openTopicModal('ml', '{summary['ml']['topic']}')">
                            <div class="task-info">
                                <font>🤖 Machine Learning Fundamentals</font>
                                <p>{summary['ml']['topic']}</p>
                            </div>
                            <button class="check-btn" onclick="event.stopPropagation(); completeTask('ml')">Mark Complete</button>
                        </div>

                        <div class="task-item" onclick="openTopicModal('interview', '{summary['interview']['task']}')">
                            <div class="task-info">
                                <font>🗣️ Communication & HR Practice</font>
                                <p>{summary['communication']} | {summary['interview']['task']}</p>
                            </div>
                            <button class="check-btn" onclick="event.stopPropagation(); completeTask('interview')">Mark Complete</button>
                        </div>
                    </div>

                    <!-- Side Stats & Recovery -->
                    <div style="display: flex; flex-direction: column; gap: 20px;">
                        <div class="glass-card">
                            <div class="card-title">📈 REVISION & WEAK TOPICS</div>
                            <div class="stat-pill">
                                <span>Spaced Revisions Due Today:</span>
                                <strong style="color: var(--accent-rose);">{dsa_progress['due_for_revision']} Qs</strong>
                            </div>
                            <div class="stat-pill">
                                <span>DSA Accuracy Rate:</span>
                                <strong style="color: var(--accent-mint);">{dsa_progress['accuracy_percentage']}%</strong>
                            </div>
                            <div style="margin-top: 14px;">
                                <strong style="font-size: 0.85rem; color: var(--accent-amber);">TOP WEAK TOPICS (&lt; 70% Accuracy):</strong>
                                <ul style="padding-left: 18px; margin-top: 6px; font-size: 0.88rem; color: #cbd5e1;">
                                    {"".join([f"<li>{w['topic']} ({w['accuracy']}% Accuracy) — {w['priority']} Priority</li>" for w in weak_topics]) if weak_topics else "<li>No weak topics detected! Keep solving.</li>"}
                                </ul>
                            </div>
                        </div>

                        <div class="glass-card">
                            <div class="card-title">🚀 DAILY APPLICATION TARGET</div>
                            <div class="stat-pill">
                                <span>Daily Application Target:</span>
                                <strong>5 Quality Applications</strong>
                            </div>
                            <div class="stat-pill">
                                <span>Jobs Saved / Applied:</span>
                                <strong style="color: var(--accent-mint);">{app_stats['jobs_applied']} Applied</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 2: Gemini AI Tutor & Plan Modifier -->
            <div id="tab-ai-tutor" class="tab-content" style="display: none;">
                <div class="grid-2">
                    <div class="glass-card">
                        <div class="card-title">
                            <span>🤖 GEMINI AI TUTOR CHAT</span>
                            <span style="font-size: 0.8rem; color: var(--accent-mint);">● Online (Gemini 2.5)</span>
                        </div>
                        <div class="chat-box">
                            <div class="chat-messages" id="chatMessages">
                                <div class="msg bot">Hello {user.name}! I am your Gemini AI Tutor & Placement Coach. Ask me any technical question, DSA hint, or ask me to modify today's plan!</div>
                            </div>
                            <div class="chat-input-area">
                                <input type="text" id="chatInput" placeholder="Ask a question or type 'I only have 3 hours today'..." onkeydown="if(event.key==='Enter') sendChatMessage()">
                                <button onclick="sendChatMessage()">Send</button>
                            </div>
                        </div>
                    </div>

                    <div class="glass-card">
                        <div class="card-title">✨ DYNAMIC AI PLAN MODIFIER</div>
                        <p style="font-size: 0.88rem; color: var(--text-muted);">Type custom instructions for Gemini to update today's plan in SQLite real-time:</p>
                        <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 14px;">
                            <button class="tab-btn" onclick="quickModifyPlan('I only have 3 hours today, streamline my objectives.')">⏱️ "I only have 3 hours today"</button>
                            <button class="tab-btn" onclick="quickModifyPlan('I am weak in Graphs, replace today\'s DSA topic with Graph BFS.')">🌳 "Focus extra on Graph BFS today"</button>
                            <button class="tab-btn" onclick="quickModifyPlan('Swap ML topic with SQL Window functions practice.')">🗄️ "Swap ML with SQL Window Functions"</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 3: DSA Question Bank -->
            <div id="tab-dsa" class="tab-content" style="display: none;">
                <div class="glass-card">
                    <div class="card-title">
                        <span>💻 250+ CURATED DSA QUESTION BANK ({dsa_progress['total_questions_in_bank']} Loaded)</span>
                        <span style="font-size: 0.85rem; color: var(--accent-amber);">{dsa_progress['total_solved_correctly']} Solved ({dsa_progress['accuracy_percentage']}%)</span>
                    </div>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">Authoritative bank parsed from <code>DSA_Placement_Ready_Top_250.md</code>.</p>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; margin-top: 16px;">
                        {"".join([
                            f"<div class='task-item'>"
                            f"<div class='task-info'>"
                            f"<font>[{q['difficulty']}] {q['title']}</font>"
                            f"<p>Topic: {q['topic']} | Pattern: {q['pattern']}</p>"
                            f"</div>"
                            f"<button class='check-btn' onclick='attemptDSA(" + str(q['id']) + ")'>Solve</button>"
                            f"</div>" for q in summary['dsa']['questions']
                        ])}
                    </div>
                </div>
            </div>

            <!-- Tab 4: Live CSE Job Digest -->
            <div id="tab-jobs" class="tab-content" style="display: none;">
                <div class="glass-card">
                    <div class="card-title">
                        <span>💼 LIVE CSE & SOFTWARE JOB DIGEST</span>
                        <span style="font-size: 0.85rem; color: var(--accent-mint);">Real-Time Verified Jobs</span>
                    </div>
                    <div class="grid-3" style="margin-top: 16px;">
                        {"".join([
                            f"<div class='job-card'>"
                            f"<div class='job-header'>"
                            f"<div>"
                            f"<h4 class='job-title'>{j.title}</h4>"
                            f"<div class='job-company'>{j.company} • {j.location}</div>"
                            f"</div>"
                            f"<span class='score-pill'>{j.relevance_score}/100 Match</span>"
                            f"</div>"
                            f"<p style='font-size: 0.82rem; color: var(--text-muted); margin: 8px 0;'>Skills: {j.skills}</p>"
                            f"<div class='job-actions'>"
                            f"<a href='{j.source_url}' target='_blank' class='apply-link'>Apply Live URL ↗</a>"
                            f"<button class='check-btn' onclick='markApplied({j.id})'>Mark Applied</button>"
                            f"</div>"
                            f"</div>" for j in top_jobs
                        ])}
                    </div>
                </div>
            </div>

            <!-- Tab 5: Applications Tracker & Notification Channels -->
            <div id="tab-applications" class="tab-content" style="display: none;">
                <div class="glass-card">
                    <div class="card-title">📊 APPLICATION TRACKER & STATS</div>
                    <div class="grid-3">
                        <div class="stat-pill"><span>Total Discovered:</span><strong>{app_stats['total_jobs_discovered']}</strong></div>
                        <div class="stat-pill"><span>Jobs Saved:</span><strong>{app_stats['jobs_saved']}</strong></div>
                        <div class="stat-pill"><span>Jobs Applied:</span><strong style="color: var(--accent-mint);">{app_stats['jobs_applied']}</strong></div>
                    </div>
                </div>

                <div class="glass-card" style="margin-top: 24px;">
                    <div class="card-title">
                        <span>🔔 NOTIFICATION CHANNELS ARCHITECTURE</span>
                        <span style="font-size: 0.8rem; color: var(--accent-mint);">Telegram + Email + Gemini 2.5</span>
                    </div>
                    <div class="grid-3" style="margin-top: 16px;">
                        <div class="stat-pill">
                            <span>✈️ Telegram Bot API:</span>
                            <strong style="color: var(--accent-mint);">{"CONFIGURED" if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID else "UNCONFIGURED (.env)"}</strong>
                        </div>
                        <div class="stat-pill">
                            <span>📧 Gmail SMTP Email:</span>
                            <strong>{"CONFIGURED" if settings.EMAIL_SENDER and settings.EMAIL_APP_PASSWORD else "CONSOLE FALLBACK (.env)"}</strong>
                        </div>
                        <div class="stat-pill">
                            <span>🖥️ Console Notifier:</span>
                            <strong style="color: var(--accent-mint);">ENABLED (Terminal Logs)</strong>
                        </div>
                    </div>

                    <div style="margin-top: 20px; display: flex; gap: 12px; align-items: center;">
                        <button class="check-btn" style="padding: 10px 20px; font-size: 0.88rem;" onclick="sendTestNotification('telegram')">✈️ Test Telegram Alert</button>
                        <button class="check-btn" style="padding: 10px 20px; font-size: 0.88rem;" onclick="sendTestNotification('email')">📧 Test Email Alert</button>
                        <span style="font-size: 0.82rem; color: var(--text-muted);">Triggers instant test alert across selected channel.</span>
                    </div>
                </div>
            </div>

        </div>

        <!-- Topic Detail Modal -->
        <div id="topicModal" class="modal-overlay">
            <div class="modal-card">
                <div class="modal-header">
                    <div>
                        <h3 id="modalTopicTitle" class="modal-title">Topic Study Guide</h3>
                        <p id="modalTopicSubtitle" class="modal-subtitle">Estimated Allocation: 1.5 Hours</p>
                    </div>
                    <button class="close-modal" onclick="closeTopicModal()">&times;</button>
                </div>
                <div id="modalBody">
                    <h4 style="color: var(--accent-mint); margin-top: 0;">📚 Key Concepts to Study Today:</h4>
                    <ul id="modalKeyConcepts" style="padding-left: 20px; font-size: 0.92rem; line-height: 1.6; color: #cbd5e1;"></ul>

                    <h4 style="color: var(--accent-amber); margin-top: 20px;">❓ Targeted Interview Questions:</h4>
                    <ul id="modalQuestions" style="padding-left: 20px; font-size: 0.92rem; line-height: 1.6; color: #cbd5e1;"></ul>

                    <h4 style="color: var(--accent-emerald); margin-top: 20px;">🎯 Action Items for Today:</h4>
                    <ul id="modalActions" style="padding-left: 20px; font-size: 0.92rem; line-height: 1.6; color: #cbd5e1;"></ul>

                    <div id="aiExplanationBox" style="margin-top: 20px; padding: 16px; background: rgba(6, 20, 18, 0.9); border: 1px solid var(--accent-emerald); border-radius: 12px; display: none;">
                        <strong style="color: var(--accent-mint); font-size: 0.9rem;">🤖 Gemini AI Deep Dive Explanation:</strong>
                        <div id="aiExplanationText" style="margin-top: 8px; font-size: 0.88rem; color: #f0fdf4; white-space: pre-wrap; line-height: 1.5;"></div>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 24px; pt-2; border-top: 1px solid var(--border-color);">
                    <button class="tab-btn" onclick="askAiToExplainModalTopic()">🤖 Explain Topic with Gemini AI</button>
                    <button class="check-btn" style="padding: 10px 20px; font-size: 0.9rem;" onclick="completeTaskFromModal()">Mark Topic Completed</button>
                </div>
            </div>
        </div>

        <!-- Focus Mode Modal -->
        <div id="focusModal" class="modal-overlay">
            <div class="modal-card">
                <div class="modal-header">
                    <div>
                        <h3 class="modal-title">⏱️ Distraction-Free Focus Mode</h3>
                        <p class="modal-subtitle">Select Timer & Study Topic</p>
                    </div>
                    <button class="close-modal" onclick="closeFocusModal()">&times;</button>
                </div>
                <div style="display: flex; flex-direction: column; gap: 16px;">
                    <div>
                        <label style="font-size: 0.88rem; color: var(--text-muted);">Study Category:</label>
                        <select id="focusCategory" style="width: 100%; background: #0d2320; color: white; border: 1px solid #10b981; padding: 10px; border-radius: 8px; margin-top: 6px;">
                            <option value="DSA">DSA Focus Pattern</option>
                            <option value="Aptitude">Aptitude Practice</option>
                            <option value="Core">Core CSE Subject</option>
                            <option value="Python">Python Technical Mastery</option>
                            <option value="SQL">SQL & Databases</option>
                            <option value="ML">Machine Learning</option>
                            <option value="Interview">Mock Interview Prep</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size: 0.88rem; color: var(--text-muted);">Focus Duration:</label>
                        <select id="focusDuration" style="width: 100%; background: #0d2320; color: white; border: 1px solid #10b981; padding: 10px; border-radius: 8px; margin-top: 6px;">
                            <option value="25">25 Minutes (Pomodoro)</option>
                            <option value="45">45 Minutes (Standard Study)</option>
                            <option value="60">60 Minutes (Deep Dive)</option>
                            <option value="90">90 Minutes (Mastery Session)</option>
                        </select>
                    </div>
                    <div style="text-align: center; margin-top: 16px;">
                        <h2 id="focusTimerDisplay" style="font-size: 3rem; color: var(--accent-mint); margin: 0;">25:00</h2>
                        <p id="focusStatusText" style="color: var(--text-muted); font-size: 0.9rem;">Ready to focus</p>
                    </div>
                    <div style="display: flex; justify-content: center; gap: 12px; margin-top: 10px;">
                        <button class="check-btn" style="padding: 12px 24px; font-size: 1rem;" onclick="startFocusTimer()">▶ Start Session</button>
                        <button class="tab-btn" onclick="stopFocusTimer()">⏹ Reset</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 7-Round Mock Interview Modal -->
        <div id="mockInterviewModal" class="modal-overlay">
            <div class="modal-card" style="max-width: 760px;">
                <div class="modal-header">
                    <div>
                        <h3 class="modal-title">🗣️ Full 7-Round Mock Interview Mode</h3>
                        <p id="mockRoundSubtitle" class="modal-subtitle">Round 1 of 7 — Introduction & Career Goals</p>
                    </div>
                    <button class="close-modal" onclick="closeMockInterviewModal()">&times;</button>
                </div>
                <div id="mockInterviewBody">
                    <div style="background: rgba(6, 20, 18, 0.9); border: 1px solid var(--border-glow); padding: 18px; border-radius: 12px; margin-bottom: 16px;">
                        <strong style="color: var(--accent-mint); font-size: 0.9rem;">Interviewer Question:</strong>
                        <p id="mockQuestionText" style="margin: 8px 0 0 0; color: #f0fdf4; font-size: 1rem; line-height: 1.5;">Loading question...</p>
                    </div>
                    <div>
                        <label style="font-size: 0.88rem; color: var(--text-muted);">Your Answer / Code Response:</label>
                        <textarea id="mockAnswerInput" rows="5" style="width: 100%; background: #0d2320; color: white; border: 1px solid #10b981; padding: 12px; border-radius: 10px; margin-top: 6px; font-size: 0.9rem;" placeholder="Type your structured technical answer or code..."></textarea>
                    </div>
                    <div id="mockEvaluationResult" style="margin-top: 16px; padding: 14px; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--accent-emerald); border-radius: 10px; display: none;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; pt-2; border-top: 1px solid var(--border-color);">
                    <button class="tab-btn" onclick="submitMockRoundAnswer()">Submit Answer & Score</button>
                    <button class="check-btn" onclick="nextMockRound()">Next Round ➔</button>
                </div>
            </div>
        </div>

        <script>
            let currentModalCategory = '';
            let currentModalTopic = '';
            let currentMockRound = 1;
            let mockEvaluations = [];
            let focusInterval = null;

            function showTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
                document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('tab-' + tabName).style.display = 'block';
                event.target.classList.add('active');
            }}

            async function startProgram() {{
                const res = await fetch('/program/start', {{ method: 'POST' }});
                const data = await res.json();
                alert(data.message);
                window.location.reload();
            }}

            async function openTopicModal(category, topicName) {{
                currentModalCategory = category;
                currentModalTopic = topicName;
                document.getElementById('aiExplanationBox').style.display = 'none';

                const res = await fetch(`/study/topic-detail?category=${{category}}&topic=${{encodeURIComponent(topicName)}}`);
                const data = await res.json();

                document.getElementById('modalTopicTitle').innerText = data.title;
                document.getElementById('modalTopicSubtitle').innerText = `Category: ${{category.toUpperCase()}} | Allocation: ${{data.estimated_time}}`;

                document.getElementById('modalKeyConcepts').innerHTML = data.key_concepts.map(c => `<li>${{c}}</li>`).join('');
                document.getElementById('modalQuestions').innerHTML = data.interview_questions.map(q => `<li>${{q}}</li>`).join('');
                document.getElementById('modalActions').innerHTML = data.action_items.map(a => `<li>${{a}}</li>`).join('');

                document.getElementById('topicModal').classList.add('active');
            }}

            function closeTopicModal() {{ document.getElementById('topicModal').classList.remove('active'); }}
            function openFocusModal() {{ document.getElementById('focusModal').classList.add('active'); }}
            function closeFocusModal() {{ stopFocusTimer(); document.getElementById('focusModal').classList.remove('active'); }}
            function openMockInterviewModal() {{ currentMockRound = 1; mockEvaluations = []; loadMockRoundQuestion(1); document.getElementById('mockInterviewModal').classList.add('active'); }}
            function closeMockInterviewModal() {{ document.getElementById('mockInterviewModal').classList.remove('active'); }}

            async function loadMockRoundQuestion(roundNum) {{
                document.getElementById('mockRoundSubtitle').innerText = `Round ${{roundNum}} of 7`;
                document.getElementById('mockEvaluationResult').style.display = 'none';
                document.getElementById('mockAnswerInput').value = '';
                const res = await fetch(`/interview/mock/round/${{roundNum}}`);
                const data = await res.json();
                document.getElementById('mockQuestionText').innerText = data.question;
            }}

            async function submitMockRoundAnswer() {{
                const answerText = document.getElementById('mockAnswerInput').value.trim();
                if(!answerText) {{ alert("Please type your answer."); return; }}

                const questionText = document.getElementById('mockQuestionText').innerText;
                const res = await fetch('/interview/mock/evaluate-round', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ round_num: currentMockRound, question: questionText, candidate_answer: answerText }})
                }});
                const data = await res.json();
                mockEvaluations.push(data);

                const evalBox = document.getElementById('mockEvaluationResult');
                evalBox.style.display = 'block';
                evalBox.innerHTML = `<strong>Score: ${{data.score}}/10</strong><br><em>Tip:</em> ${{data.interview_tip}}<br><em>Follow-up:</em> ${{data.follow_up_question}}`;
            }}

            async function nextMockRound() {{
                if (currentMockRound < 7) {{
                    currentMockRound++;
                    loadMockRoundQuestion(currentMockRound);
                }} else {{
                    const res = await fetch('/interview/mock/generate-report', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ round_evaluations: mockEvaluations }})
                    }});
                    const report = await res.json();
                    alert(`Interview Complete!\nOverall Score: ${{report.overall_score}}/10\nTechnical: ${{report.technical_score}}\nRecommendation: ${{report.recommendation}}`);
                    closeMockInterviewModal();
                }}
            }}

            function startFocusTimer() {{
                const mins = parseInt(document.getElementById('focusDuration').value);
                let seconds = mins * 60;
                stopFocusTimer();
                document.getElementById('focusStatusText').innerText = "Focusing...";

                focusInterval = setInterval(() => {{
                    seconds--;
                    const m = Math.floor(seconds / 60);
                    const s = seconds % 60;
                    document.getElementById('focusTimerDisplay').innerText = `${{m.toString().padStart(2, '0')}}:${{s.toString().padStart(2, '0')}}`;
                    if (seconds <= 0) {{
                        stopFocusTimer();
                        alert("Focus Session Complete!");
                    }}
                }}, 1000);
            }}

            function stopFocusTimer() {{
                if(focusInterval) clearInterval(focusInterval);
                document.getElementById('focusTimerDisplay').innerText = "25:00";
                document.getElementById('focusStatusText').innerText = "Session Reset";
            }}

            async function askAiToExplainModalTopic() {{
                const box = document.getElementById('aiExplanationBox');
                const text = document.getElementById('aiExplanationText');
                box.style.display = 'block';
                text.innerText = "Querying Gemini AI Tutor for an interview cheat-sheet...";

                const prompt = `Provide a concise 3-bullet interview cheat-sheet for: '${{currentModalTopic}}' under category '${{currentModalCategory}}'.`;
                const res = await fetch('/ai/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: prompt }})
                }});
                const data = await res.json();
                text.innerText = data.reply;
            }}

            async function completeTaskFromModal() {{
                await completeTask(currentModalCategory);
                closeTopicModal();
            }}

            async function triggerDatabaseBackup() {{
                const res = await fetch('/system/backup', {{ method: 'POST' }});
                const data = await res.json();
                alert(data.message);
            }}

            async function completeTask(category) {{
                const res = await fetch('/study/complete-task', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ category: category }})
                }});
                alert('Task marked complete!');
            }}

            async function sendChatMessage() {{
                const input = document.getElementById('chatInput');
                const msgText = input.value.trim();
                if(!msgText) return;

                const messagesDiv = document.getElementById('chatMessages');
                messagesDiv.innerHTML += `<div class="msg user">${{msgText}}</div>`;
                input.value = '';
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                const res = await fetch('/ai/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: msgText }})
                }});
                const data = await res.json();
                messagesDiv.innerHTML += `<div class="msg bot">${{data.reply}}</div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }}

            async function quickModifyPlan(promptText) {{
                const res = await fetch('/ai/modify-plan', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ user_prompt: promptText }})
                }});
                const data = await res.json();
                alert(data.message);
                window.location.reload();
            }}

            async function markApplied(jobId) {{
                await fetch(`/jobs/${{jobId}}/apply`, {{ method: 'POST' }});
                alert('Marked as Applied!');
            }}

            async function sendTestNotification(channel) {{
                const res = await fetch('/notifications/test', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ channel: channel, subject: 'Test Alert', body: 'Test notification from platform!' }})
                }});
                const data = await res.json();
                alert(`Notification status for ${{channel}}: ${{data.status}}`);
            }}

            async function attemptDSA(questionId) {{
                const result = prompt("Enter result ('correct', 'incorrect', 'partial'):", "correct");
                if (result) {{
                    await fetch(`/dsa/${{questionId}}/attempt`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ result: result, confidence: 5 }})
                    }});
                    alert('DSA attempt recorded!');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content