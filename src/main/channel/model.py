from typing import Self

import discord
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

from core.database import Entity
from core.discord_mixin import DiscordMixin

__all__ = ["Channel"]


class Channel(Entity, DiscordMixin[discord.abc.GuildChannel]):
    __tablename__ = "channel"

    name: Mapped[str] = Column(String, nullable=False)
    type: Mapped[str] = Column(String, nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "channel",
        "polymorphic_on": type,
        "with_polymorphic": "*"
    }

    @classmethod
    def from_discord(cls, dto: discord.abc.GuildChannel) -> Self:
        entity = Channel()
        entity.discord_id = dto.id
        entity.name = dto.name
        entity.type = str(dto.type)
        return entity
