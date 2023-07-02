from dataclasses import dataclass
from typing import Self

import discord
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

from core.database import Entity
from core.dated.mixin import DatedMixin
from core.discord_mixin import DiscordMixin


@dataclass
class Guild(Entity, DatedMixin, DiscordMixin[discord.Guild]):
    __tablename__ = "guild"

    name: Mapped[str] = Column(String, nullable=False)

    @classmethod
    def from_discord(cls, dto: discord.Guild) -> Self:
        entity = Guild()
        entity.discord_id = dto.id
        entity.name = dto.name
        return entity
