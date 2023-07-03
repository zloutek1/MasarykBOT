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
    color: Mapped[int] = Column(Integer)

    @classmethod
    def from_discord(cls, dto: discord.Role) -> Self:
        entity = Role()
        entity.discord_id = dto.id
        entity.name = dto.name
        entity.color = dto.color.value
        return entity

    def equals(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if self.id and other.id and self.id != other.id:
            return False
        return self.name == other.name and self.color == other.color
