from dataclasses import dataclass
from typing import Self

import discord
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

from core.database import Entity
from core.dated.mixin import DatedMixin
from core.discord_mixin import DiscordMixin


@dataclass
class Guild(Entity, DatedMixin, DiscordMixin):
    __tablename__ = "guild"

    name: Mapped[str] = Column(String, nullable=False)

    @classmethod
    def from_discord(cls, guild: discord.Guild) -> Self:
        entity = cls()
        entity.discord_id = guild.id
        entity.name = guild.name
        return entity
