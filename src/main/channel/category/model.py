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

    def __repr__(self) -> str:
        attrs = (
            ('id', self.id),
            ('discord_id', self.discord_id),
            ('created', self.created),
            ('updated', self.updated),
            ('deleted', self.deleted),
            ('name', self.name)
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{type(self).__name__} {inner}>'
