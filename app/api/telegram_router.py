from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

from app.notifications.telegram import TelegramCommandHandler, TelegramNotifier

router = APIRouter(prefix="/telegram", tags=["Telegram Bot Webhook"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Receives incoming webhook updates from Telegram Bot API.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = str(message.get("chat", {}).get("id", ""))

    callback_query = data.get("callback_query", {})
    if callback_query:
        text = callback_query.get("data", "")
        chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))

    if text and chat_id:
        res = TelegramCommandHandler.process_message(text)
        notifier = TelegramNotifier()
        notifier.send(message=res["reply"], recipient=chat_id, inline_buttons=res.get("buttons"))

    return {"status": "ok"}


@router.post("/command")
def execute_telegram_command(payload: Dict[str, str]):
    """
    Allows executing a Telegram command directly via API or UI button.
    """
    command_text = payload.get("command", "/help")
    res = TelegramCommandHandler.process_message(command_text)
    return res
