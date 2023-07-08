from typing import Type

from core.dated.repository import DatedRepository
from message.model import Message

__all__ = ["MessageRepository"]


class MessageRepository(DatedRepository[Message]):
    @property
    def model(self) -> Type:
        return Message
