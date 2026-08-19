# 🚀 60-Day CSE Career Coach — Deployment & 24/7 Execution Guide

This guide explains how to deploy your **60-Day AI-Powered CSE Career Coach** so that it runs **continuously 24/7** in the background, automatically sending daily Telegram alerts, Gmail study missions, and job digests every day without requiring your computer to stay on.

---

## 📌 DEPLOYMENT OPTIONS AT A GLANCE

| Deployment Option | Ideal For | Cost | Laptop Can Be Off? | Setup Difficulty |
|---|---|---|---|---|
| **Option 1: Cloud VPS (Docker / systemd)** | 24/7 Autonomous Daily Coach | $0 - $5 / mo | ✅ YES | ⚡ Recommended (Easy) |
| **Option 2: Render.com / Railway.app** | Free Cloud Hosting | Free tier | ✅ YES | ⚡ Easiest Cloud |
| **Option 3: Local Windows Service (NSSM)** | Local PC Running 24/7 | Free | ❌ NO | 🔧 Easy Local |

---

## 🌐 OPTION 1: DEPLOY ON CLOUD SERVER (VPS - Docker / Docker Compose)

Deploying on a Cloud VPS (such as DigitalOcean, Hetzner, AWS EC2, or Vultr) using Docker ensures your platform **never sleeps**, sending your Telegram study plan every morning at 08:00 AM Kolkata time.

### Step 1: Upload Project Files to your Server
Upload or git clone your `automation_engine/` directory to your cloud server:
```bash
git clone <your-private-repo-url> /opt/automation_engine
cd /opt/automation_engine
```

### Step 2: Configure Environment Variables
Create your `.env` file on the server:
```bash
cp .env.example .env
nano .env
```
Ensure your credentials are set:
```env
GEMINI_API_KEY=your_gemini_api_key_here

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

EMAIL_ENABLED=true
EMAIL_SENDER=your_email@gmail.com
EMAIL_APP_PASSWORD=your_gmail_app_password_here
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

TIMEZONE=Asia/Kolkata
```

### Step 3: Run with 1-Command Docker Compose
Run the container in background daemon mode:
```bash
docker compose up -d --build
```

### Step 4: Verify Container Status
Check that your server is running:
```bash
docker compose ps
docker compose logs -f
```

---

## ☁️ OPTION 2: DEPLOY ON RENDER.COM / RAILWAY.APP (Free Cloud Hosting)

If you don't own a Linux server, you can deploy for free on Render or Railway.

### Deploying on Render.com:
1. Push your `automation_engine/` code to a private GitHub repository.
2. Sign up on [Render.com](https://render.com).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository.
5. Set build and start settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`
6. Under **Environment Variables**, add:
   - `GEMINI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `EMAIL_SENDER`
   - `EMAIL_APP_PASSWORD`
   - `TIMEZONE` = `Asia/Kolkata`
7. Click **Create Web Service**.

---

## 💻 OPTION 3: RUN 24/7 ON LOCAL WINDOWS PC (NSSM Windows Service)

If you keep your Windows PC on during the day and want the platform to start automatically whenever Windows boots up, install it as a Windows Background Service.

### Method A: Using Windows Task Scheduler (Simple)
1. Press `Win + R`, type `taskschd.msc`, and press Enter.
2. Click **Create Basic Task...** in the right sidebar.
3. Name: `CSE Career Coach 60-Day Platform`.
4. Trigger: Select **When the computer starts**.
5. Action: Select **Start a program**.
6. Program/script: Browse to your Python executable:
   `c:\Automation\automation_engine\.venv\Scripts\python.exe`
7. Add arguments: `run.py`
8. Start in: `c:\Automation\automation_engine`
9. Click **Finish**.

### Method B: Using NSSM (Non-Sucking Service Manager)
1. Download NSSM from `https://nssm.cc/download`.
2. Open PowerShell as Administrator and run:
   ```powershell
   nssm install CseCareerCoach "c:\Automation\automation_engine\.venv\Scripts\python.exe" "c:\Automation\automation_engine\run.py"
   nssm set CseCareerCoach AppDirectory "c:\Automation\automation_engine"
   nssm start CseCareerCoach
   ```

---

## ⏰ AUTOMATED DAILY SCHEDULE VERIFICATION

Once deployed, the background scheduler automatically triggers the following events every single day in `Asia/Kolkata` timezone:

| Time (Kolkata) | Event Name | Action Taken |
|---|---|---|
| **08:00 AM** | ☀️ Morning Mission Alert | Generates Day X study plan & sends Telegram + Email summary. |
| **09:30 AM** | 💼 Job Openings Digest | Discovers & sends daily curated CSE job list. |
| **01:00 PM** | ⏰ Quick Revision Reminder | Sends alert if SM-2 spaced revisions are due. |
| **06:00 PM** | 💻 Evening DSA Focus | Sends notification to open DSA question bank. |
| **10:30 PM** | 📊 Nightly Progress Review | Calculates daily completed tasks and accuracy %. |

---

## 🔍 MONITORING & TROUBLESHOOTING

- **Check Health Status**: Visit `http://your-server-ip:8000/health`
- **View Dashboard**: Visit `http://your-server-ip:8000/dashboard`
- **Trigger Instant Telegram Test**:
  Run on your server:
  ```bash
  python tools/send_live_telegram_test.py
  ```
