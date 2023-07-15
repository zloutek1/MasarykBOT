from typing import Self

import discord
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

from core.database import Entity
from core.discord_mixin import DiscordMixin

__all__ = ["Guild"]


class Guild(Entity, DiscordMixin[discord.Guild]):
    __tablename__ = "guild"

    name: Mapped[str] = Column(String, nullable=False)
    icon_url: Mapped[str] = Column(String)

    @classmethod
    def from_discord(cls, dto: discord.Guild) -> Self:
        entity = Guild()
        entity.discord_id = dto.id
        entity.name = dto.name
        entity.icon_url = dto.icon.url if dto.icon else None
        return entity

    def __repr__(self) -> str:
        attrs = (
            ('id', self.id),
            ('discord_id', self.discord_id),
            ('created', self.created),
            ('updated', self.updated),
            ('deleted', self.deleted),
            ('name', self.name),
            ('icon_url', self.icon_url),
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{type(self).__name__} {inner}>'
