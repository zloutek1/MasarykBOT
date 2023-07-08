from typing import Type

from channel.model import Channel
from core.dated.repository import DatedRepository

__all__ = ["ChannelRepository"]


class ChannelRepository(DatedRepository[Channel]):
    @property
    def model(self) -> Type:
        return Channel
