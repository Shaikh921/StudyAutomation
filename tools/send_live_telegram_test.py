import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.notifications.telegram import TelegramNotifier, TelegramCommandHandler

notifier = TelegramNotifier()
print(f"Is Configured: {notifier.is_configured()}")
print(f"Bot Token: {notifier.bot_token[:10]}...")
print(f"Chat ID: {notifier.default_chat_id}")

success = notifier.send(
    message="🚀 <b>60-Day CSE Placement Coach Initialized!</b>\n\n"
            "Your Telegram integration is 100% active!\n"
            "You will now receive daily study missions, DSA spaced repetition alerts, and CSE job digests directly here.\n\n"
            "Try sending commands like /today, /dsa, /jobs, /progress, /mock, or ask any question!",
    title="🤖 TELEGRAM NOTIFICATION SYSTEM VERIFIED",
    inline_buttons=[
        [{"text": "🎯 TODAY'S MISSION", "callback_data": "cmd_today"}, {"text": "💻 DSA QUESTION", "callback_data": "cmd_dsa"}],
        [{"text": "💼 LIVE JOBS", "callback_data": "cmd_jobs"}, {"text": "🗣️ MOCK INTERVIEW", "callback_data": "cmd_mock"}]
    ]
)

if success:
    print("[SUCCESS] Live Telegram notification sent successfully!")
else:
    print("[ERROR] Failed to send live Telegram message.")
