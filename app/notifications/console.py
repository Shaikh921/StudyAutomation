import logging
from typing import Optional
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class ConsoleNotifier(NotificationProvider):
    def send(self, recipient: str, subject: Optional[str], body: str, execution_key: Optional[str] = None) -> bool:
        header = f"=== CONSOLE NOTIFICATION [{subject or 'Alert'}] to {recipient} ==="
        border = "=" * len(header)
        print(f"\n{border}\n{header}\n{border}\n{body}\n{border}\n")
        logger.info(f"Console notification sent to {recipient}: {subject}")
        return True
