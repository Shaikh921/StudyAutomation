# Telegram Bot Integration & Automation Guide

The **60-Day AI-Powered CSE Job Preparation Automation Platform** is fully integrated with **Telegram Bot API** as its primary interactive notification channel.

---

## 📌 1. Configuration Overview

| Configuration Parameter | Environment Variable | Current Value | Status |
|---|---|---|---|
| **Telegram Status** | `TELEGRAM_ENABLED` | `true` | **ACTIVE** |
| **Bot Token** | `TELEGRAM_BOT_TOKEN` | `<YOUR_TELEGRAM_BOT_TOKEN>` | **CONFIGURED** |
| **Chat ID** | `TELEGRAM_CHAT_ID` | `<YOUR_TELEGRAM_CHAT_ID>` | **VERIFIED & CONNECTED** |
| **Email SMTP** | `EMAIL_SENDER` | `<YOUR_EMAIL_ADDRESS>` | **CONFIGURED** |
| **AI Engine** | `GEMINI_API_KEY` | `<YOUR_GEMINI_API_KEY>` | **CONFIGURED (Gemini 2.5)** |

---

## 🤖 2. Interactive Telegram Bot Commands

You can send any of the following commands directly to your Telegram bot:

| Command | Action / Response | Inline Interactive Buttons |
|---|---|---|
| **`/start`** | Displays welcome banner, user setup info, and main dashboard navigation buttons. | `[START TODAY'S PLAN]`, `[START DSA]`, `[VIEW JOBS]`, `[ASK GEMINI]`, `[START MOCK INTERVIEW]`, `[PROGRESS]` |
| **`/today`** | Fetches Day X curriculum objectives across DSA, Aptitude, Core CSE, Python, SQL, and ML. | `[SOLVE DSA NOW]`, `[APPLY TO JOBS]`, `[MARK TODAY COMPLETE]` |
| **`/dsa`** | Fetches today's recommended DSA question with difficulty, topic, and pattern. | `[Hint 1 (Clue)]`, `[Hint 2 (Pattern)]`, `[Full Solution]`, `[Explain with Gemini]` |
| **`/jobs`** | Generates real-time top matching CSE & Software engineer job listings. | `[Apply #1 ↗]`, `[Apply #2 ↗]`, `[VIEW ALL JOBS]` |
| **`/progress`** | Displays 60-day completion %, solved DSA problems count, accuracy %, and due spaced revisions. | N/A |
| **`/mock`** | Starts the 7-Round Mock Interview simulation with Gemini evaluation. | N/A |
| **`/help`** | Displays command reference guide. | N/A |
| **`<natural language>`** | Send any technical prompt or question e.g. *"Explain TCP 3-way handshake"* to get an instant answer from Gemini 2.5! | N/A |

---

## 🚀 3. Daily Automated Notifications

Every morning, the background scheduler automatically triggers:

1. **07:00 AM — Daily CSE Job Digest**:
   - Searches live remote & software job feeds.
   - Filters out senior roles (5+ yrs) and incomplete listings.
   - Formats top matches with relevance scores and direct application links sent to Telegram & Email.

2. **08:00 AM — Today's Placement Mission**:
   - Calculates current **DAY X / 60**.
   - Formats today's study plan with clickable action buttons delivered straight to your Telegram chat.

3. **Spaced Repetition Reminders**:
   - Sends due DSA revision problems based on the SM-2 algorithm intervals (1d → 3d → 7d → 14d → 30d).

---

## 🧪 4. Live Test Verification Results

### A. Telegram Test Dispatch
- **Script**: `python tools/send_live_telegram_test.py`
- **Result**: `[SUCCESS] Live Telegram notification sent successfully!`

### B. System Health API (`GET /health`)
```json
{
  "status": "healthy",
  "database": "healthy",
  "scheduler": "running_manual_mode",
  "gemini": "configured",
  "telegram": "configured",
  "email": "configured",
  "timestamp": "2026-08-19T03:38:58.944816+00:00",
  "platform": "60-Day CSE Job Preparation Automation Platform"
}
```

### C. Automated Unit Test Suite (`python tools/run_tests.py`)
```text
Ran 10 tests in 32.341s
OK
```

### D. Endpoint Verification Suite (`python tools/test_app_endpoints.py`)
```text
GET /health status: 200, status: healthy
GET /system/status status: 200, status: operational
GET /study/today status: 200, day: 1
GET /dsa/progress status: 200
GET /jobs/digest status: 200
GET /applications/stats status: 200
GET /dashboard status: 200, HTML length: 50179 bytes
All API endpoints tested and functioning 100% successfully!
```

---

## 🛠️ 5. Helpful Commands & Maintenance

```bash
# Test Live Telegram Message
python tools/send_live_telegram_test.py

# Re-discover or Update Telegram Chat ID
python tools/fetch_telegram_chat_id.py

# Run Test Suite
python tools/run_tests.py
python tools/test_app_endpoints.py

# Run Web Platform Server
python run.py
```
