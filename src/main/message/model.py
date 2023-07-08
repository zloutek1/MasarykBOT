from typing import Self

import discord
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

from core.database import Entity
from core.discord_mixin import DiscordMixin

__all__ = ["Message"]


class Message(Entity, DiscordMixin[discord.Message]):
    __tablename__ = "message"

    content: Mapped[str] = Column(String, nullable=False)

    @classmethod
    def from_discord(cls, dto: discord.Message) -> Self:
        entity = Message()
        entity.discord_id = dto.id
        entity.content = dto.content
        return entity

    def equals(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if self.id and other.id and self.id != other.id:
            return False
        return self.content == other.content
