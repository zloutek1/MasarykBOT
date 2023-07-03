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

    def equals(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if self.id and other.id and self.id != other.id:
            return False
        return self.name == other.name and self.icon_url == other.icon_url
