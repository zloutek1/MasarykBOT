from typing import Self

import discord
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import Mapped

from core.database import Entity
from core.discord_mixin import DiscordMixin

__all__ = ["Role"]


class Role(Entity, DiscordMixin[discord.Role]):
    __tablename__ = "role"

    name: Mapped[str] = Column(String)
    color: Mapped[int] = Column(Integer, default=0xdeadbf)

    @classmethod
    def from_discord(cls, dto: discord.Role) -> Self:
        entity = Role()
        entity.discord_id = dto.id
        entity.name = dto.name
        entity.color = dto.color.value
        return entity

    def __repr__(self) -> str:
        attrs = (
            ('id', self.id),
            ('discord_id', self.discord_id),
            ('created', self.created),
            ('updated', self.updated),
            ('deleted', self.deleted),
            ('name', self.name),
            ('color', self.color),
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{type(self).__name__} {inner}>'
