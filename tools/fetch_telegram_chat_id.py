import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

ENV_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(ENV_FILE, override=True)

bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

if not bot_token:
    print("[ERROR] TELEGRAM_BOT_TOKEN is empty in your .env file.")
    print("Please paste your Telegram Bot Token into .env e.g. TELEGRAM_BOT_TOKEN=123456789:ABC...")
    sys.exit(1)

print(f"[SEARCHING] Querying Telegram API for Bot Token: {bot_token[:10]}...")
url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if not data.get("ok"):
        print(f"[ERROR] Telegram API Error: {data.get('description')}")
        sys.exit(1)

    result = data.get("result", [])
    if not result:
        print("\n[NOTICE] No messages or /start updates found yet.")
        print("INSTRUCTIONS TO DISCOVER YOUR TELEGRAM CHAT ID:")
        print("1. Open Telegram app on your phone or PC.")
        print("2. Search for your bot name.")
        print("3. Click 'START' or send any message e.g. '/start' or 'hello'.")
        print("4. Run this script again: python tools/fetch_telegram_chat_id.py")
        sys.exit(0)

    # Extract chat_id from latest update
    latest_update = result[-1]
    msg = latest_update.get("message") or latest_update.get("edited_message") or latest_update.get("callback_query", {}).get("message")
    
    if not msg:
        print("[ERROR] Could not parse message from update payload.")
        sys.exit(1)

    chat = msg.get("chat", {})
    chat_id = str(chat.get("id"))
    first_name = chat.get("first_name", "User")
    username = chat.get("username", "")

    print("\n[SUCCESS] TELEGRAM CHAT ID FOUND!")
    print(f"• User: {first_name} (@{username})")
    print(f"• Chat ID: {chat_id}")

    # Auto update .env
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if "TELEGRAM_CHAT_ID=" in content:
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("TELEGRAM_CHAT_ID="):
                new_lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
            else:
                new_lines.append(line)
        new_content = "\n".join(new_lines) + "\n"
    else:
        new_content = content + f"\nTELEGRAM_CHAT_ID={chat_id}\n"

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[SUCCESS] Updated .env with TELEGRAM_CHAT_ID={chat_id}!")

except Exception as e:
    print(f"[ERROR] Error fetching Telegram chat ID: {e}")
