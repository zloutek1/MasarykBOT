from typing import Type

from channel.text.model import TextChannel
from core.dated.repository import DatedRepository

__all__ = ["TextChannelRepository"]


class TextChannelRepository(DatedRepository[TextChannel]):
    @property
    def model(self) -> Type[TextChannel]:
        return TextChannel
