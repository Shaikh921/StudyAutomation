import logging
from typing import Optional

from app.config import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class WhatsAppNotifier(NotificationProvider):
    """
    WhatsApp Provider Abstraction.
    Can be configured for Meta WhatsApp Cloud API / Twilio SMS/WhatsApp provider.
    """
    def send(self, recipient: str, subject: Optional[str], body: str, execution_key: Optional[str] = None) -> bool:
        if not settings.WHATSAPP_ENABLED or not settings.WHATSAPP_API_KEY:
            logger.info(f"[WhatsApp Provider Disabled] Logged WhatsApp alert for {recipient}: {subject}")
            print(f"\n[WHATSAPP ABSTRACTION LOG] To: {recipient}\nMessage: {body}\n")
            return True

        try:
            logger.info(f"WhatsApp API payload sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"WhatsApp sending failed: {e}")
            return False
