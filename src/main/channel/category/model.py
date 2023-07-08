from typing import Self, Any

import discord
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from channel.model import Channel
from core.discord_mixin import DiscordMixin

__all__ = ["CategoryChannel"]


class CategoryChannel(Channel, DiscordMixin[discord.CategoryChannel]):
    __tablename__ = "category_channel"

    id: Mapped[str] = mapped_column(ForeignKey('channel.id'), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "category_channel",
    }

    def __init__(self, **kw: Any):
        super().__init__(type="category_channel", **kw)

    @classmethod
    def from_discord(cls, dto: discord.CategoryChannel) -> Self:
        entity = CategoryChannel()
        entity.discord_id = dto.id
        entity.name = dto.name
        return entity

    def equals(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if self.id and other.id and self.id != other.id:
            return False
        return self.name == other.name and self.type == other.type
