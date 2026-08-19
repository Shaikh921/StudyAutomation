from abc import ABC, abstractmethod
from typing import Optional


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, recipient: str, subject: Optional[str], body: str, execution_key: Optional[str] = None) -> bool:
        pass
