# 60-Day AI-Powered CSE Job Preparation Automation Platform & Placement Coach

> **An intelligent, personal job-preparation automation system designed for CSE students to achieve technical interview readiness and maximize software job opportunities within a strict 60-day window.**

---

## 📖 TABLE OF CONTENTS
1. [What This Project Does](#-what-this-project-does)
2. [Explicit Program Start Logic & State Machine](#-explicit-program-start-logic--state-machine)
3. [Key System Features](#-key-system-features)
4. [System Architecture & Technology Stack](#-system-architecture--technology-stack)
5. [How It Works (Under the Hood)](#-how-it-works-under-the-hood)
6. [Database Schema & Models](#-database-schema--models)
7. [Interactive Channels (Telegram + Email + Gemini)](#-interactive-channels-telegram--email--gemini)
8. [Step-by-Step Installation & Setup Guide](#-step-by-step-installation--setup-guide)
9. [How to Use the System Day-to-Day](#-how-to-use-the-system-day-to-day)
10. [Testing & Verification Suite](#-testing--verification-suite)
11. [API Reference Summary](#-api-reference-summary)

---

## 🚀 WHAT THIS PROJECT DOES

The **60-Day AI-Powered CSE Career Coach** is an autonomous backend engine and web platform built to solve the core challenges faced by computer science job seekers: fragmented study schedules, poor revision retention, unguided interview preparation, and time-consuming job searches.

Rather than acting as a static todo app or generic reminder tool, this system **actively plans, teaches, reminds, evaluates, and adapts** to your progress every single day over a 60-day preparation timeline.

---

## 🔒 EXPLICIT PROGRAM START LOGIC & STATE MACHINE

The 60-day countdown begins **ONLY** when you explicitly click the **[ 🚀 START 60-DAY PROGRAM ]** button on the dashboard or invoke `POST /program/start`.

```text
                     +---------------------------+
                     |        NOT_STARTED        |  <-- Initial State (Server Startup)
                     +---------------------------+      No countdown, no daily study emails
                                   |
                       [ START 60-DAY PROGRAM ]  <-- Explicit User Action Only
                                   |
                                   v
                     +---------------------------+
                     |          ACTIVE           |  <-- Sets program_start_date = today (Kolkata)
                     +---------------------------+      current_day = ((today - start_date).days) + 1
                        /                     \
             [ PAUSE PROGRAM ]           Day 60 Reached
                      /                         \
                     v                           v
         +-----------------------+     +-----------------------+
         |        PAUSED         |     |       COMPLETED       |
         +-----------------------+     +-----------------------+
         (Notification Pause Only)      (Final Curriculum Done)
```

### Key Principles:
1. **Never Auto-Starts**: Server startup, database creation, browser refreshes, or first API requests **DO NOT** initialize Day 1.
2. **Asia/Kolkata Timezone Formula**:
   $$\text{current\_day} = (\text{today}_{\text{kolkata}} - \text{program\_start\_date}).\text{days} + 1$$
3. **Accidental Reset Protection**: Clicking `START` when already `ACTIVE` will **NOT** reset your progress to Day 1.
4. **Calendar Continuity**: Missed study days do not shift the calendar forward; missed tasks are handled via existing Missed-Task Recovery slots (max 2/day, 30m each).

---

## ✨ KEY SYSTEM FEATURES

### 1. 📅 60-Day Curriculum & Adaptive Roadmap Engine
- **Phase 1 (Days 1–15)**: Data Structures & Core CSE Foundations.
- **Phase 2 (Days 16–30)**: Advanced Algorithms & Machine Learning.
- **Phase 3 (Days 31–45)**: System Design, Projects & Mock Interviews.
- **Phase 4 — Interview Sprint Mode (Days 46–53)**: Auto-activates on Day 46 with timed DSA, core interview questions, and 3 applications/day.
- **Final Interview Mode (Days 54–60)**: Auto-activates on Day 54 with intensive mock interview simulation and 5 quality applications/day.

### 2. 💻 Curated 250+ DSA Question Bank & SM-2 Spaced Repetition
- Parsed directly from [`DSA_Placement_Ready_Top_250.md`](file:///c:/Automation/automation_engine/DSA_Placement_Ready_Top_250.md) (300+ entries across 22 categories).
- SHA-256 fingerprint deduplication prevents duplicate database entries.
- Weak topic tracking automatically highlights areas where accuracy falls below 70%.

### 3. 🤖 Gemini 2.5 Progressive Hint & Tutor System
- **Level 1 Hint**: Subtle clue without giving away the algorithm.
- **Level 2 Hint**: Core pattern and time/space complexity approach.
- **Level 3 (Solution)**: Complete Python code with explanation and follow-up question.

### 4. 🗣️ Full 7-Round Mock Interview Engine
- Conducts step-by-step 7-round interview simulations: Intro, DSA, Core CSE, Python/SQL, ML, System Design, HR.

### 5. 💼 Job Search Engine & Preparation Packs
- Ingests real-time remote and software engineering job listings.
- Filter rules: Rejects senior roles (5+ yrs) and incomplete URLs.
- Deterministic match score (0–100%).

### 6. ✈️ Telegram Bot & Gmail SMTP Integration
- **Two-Way Telegram Bot**: Interacts via commands (`/start`, `/today`, `/dsa`, `/jobs`, `/progress`, `/mock`, `/ask`).
- **Inline Action Buttons**: `[START TODAY'S PLAN]`, `[START DSA]`, `[VIEW JOBS]`, `[ASK GEMINI]`.
- **Gmail SMTP HTML Emails**: Formats rich daily mission emails and job digests.

---

## 🔌 API REFERENCE SUMMARY

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check (database, scheduler, Gemini, Telegram, Email). |
| `GET` | `/program/status` | Returns current program state, Day X, start/end dates, progress %. |
| `POST` | `/program/start` | Explicitly starts 60-day program & sets Day 1 to today. |
| `POST` | `/program/pause` | Pauses daily notifications. |
| `POST` | `/program/resume` | Resumes daily notifications. |
| `POST` | `/program/restart` | Requires `{"confirm_restart": true}` to reset Day 1. |
| `GET` | `/study/today` | Retrieves current Day X mission summary. |
| `POST` | `/study/complete-task` | Marks a daily task completed in SQLite. |
| `POST` | `/dsa/{id}/attempt` | Records DSA attempt and updates SM-2 revision interval. |
| `POST` | `/system/backup` | Saves timestamped SQLite database copy in `backups/`. |
| `POST` | `/telegram/webhook` | Telegram Bot API callback update handler. |
