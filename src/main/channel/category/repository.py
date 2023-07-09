from typing import Type

from channel.category.model import CategoryChannel
from core.dated.repository import DatedRepository

__all__ = ["CategoryChannelRepository"]


class CategoryChannelRepository(DatedRepository[CategoryChannel]):
    @property
    def model(self) -> Type:
        return CategoryChannel
