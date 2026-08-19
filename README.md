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
9. [24/7 Deployment Guide](#-247-deployment-guide)
10. [How to Use the System Day-to-Day](#-how-to-use-the-system-day-to-day)
11. [Testing & Verification Suite](#-testing--verification-suite)
12. [API Reference Summary](#-api-reference-summary)

---

## 🚀 WHAT THIS PROJECT DOES

The **60-Day AI-Powered CSE Career Coach** is an autonomous backend engine and web platform built to solve the core challenges faced by computer science job seekers: fragmented study schedules, poor revision retention, unguided interview preparation, and time-consuming job searches.

Rather than acting as a static todo app or generic reminder tool, this system **actively plans, teaches, reminds, evaluates, and adapts** to your progress every single day over a 60-day preparation timeline.

---

## 🔒 EXPLICIT PROGRAM START LOGIC & STATE MACHINE

The 60-day countdown begins **ONLY** when you explicitly click the **[ 🚀 START 60-DAY PROGRAM ]** button on the dashboard or invoke `POST /program/start`.

- **Initial State**: `NOT_STARTED`. Server startup, database creation, or browser visits **do not** start Day 1.
- **Start Action**: Sets `program_start_date = today` (Asia/Kolkata), generates Day 1 plan, and sends welcome notification via Telegram & Email.
- **Calculation Formula**:
  $$\text{current\_day} = (\text{today}_{\text{kolkata}} - \text{program\_start\_date}).\text{days} + 1$$
- **Accidental Reset Prevention**: Clicking `START` when active will **not** reset Day 1.

---

## ☁️ 24/7 DEPLOYMENT GUIDE

For complete 24/7 continuous operation without keeping your personal computer turned on, see the full guide in [`DEPLOYMENT_GUIDE.md`](file:///c:/Automation/automation_engine/DEPLOYMENT_GUIDE.md).

### 1-Command Docker Deployment:
```bash
docker compose up -d --build
```
This runs the platform container in the background with volume persistence for `automation_engine.db`.

---

## 📱 HOW TO USE THE SYSTEM DAY-to-DAY

### Option A: Via Telegram Bot (Mobile & Desktop)
Open Telegram and chat with your bot using these commands:
- `/today` — Get today's curriculum objectives and click `[START TODAY'S PLAN]`.
- `/dsa` — Get today's DSA question and use inline buttons `[Hint 1]`, `[Hint 2]`, `[Full Solution]`, or `[Explain with Gemini]`.
- `/jobs` — View fresh CSE job listings and click `[Apply ↗]`.
- `/progress` — Check your 60-day completion progress and accuracy.
- `/mock` — Start a 7-round mock interview session.

### Option B: Via Web Dashboard ([http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard))
1. Open the dashboard to see your 60-day progress bar.
2. Click on any daily task item to open the **Topic Study Guide Modal** with key concepts, interview questions, and Gemini AI deep dive explanations.
3. Use the **Quick Actions Bar** to launch Focus Mode timers, start mock interviews, or backup the database in 1 click.

---

## 🧪 TESTING & VERIFICATION SUITE

```bash
# 1. Run Core Unit Test Suite
python tools/run_tests.py

# 2. Run API Endpoint Test Suite
python tools/test_app_endpoints.py

# 3. Test Live Telegram Message Dispatch
python tools/send_live_telegram_test.py

# 4. Verify Syntax Compilation
python -m compileall app
```
