from typing import Self

import discord
from sqlalchemy import Column, String, Integer

from core.database import Entity
from core.dated.mixin import DatedMixin
from core.discord_mixin import DiscordMixin

__all__ = ["Role"]


class Role(Entity, DatedMixin, DiscordMixin[discord.Role]):
    __tablename__ = "role"

    name: str = Column(String)
    color: int = Column(Integer)

    @classmethod
    def from_discord(cls, dto: discord.Role) -> Self:
        entity = Role()
        entity.discord_id = dto.id
        entity.name = dto.name
        entity.color = dto.color.value
        return entity
