from typing import Self, Any

import discord
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from channel.model import Channel
from core.discord_mixin import DiscordMixin

__all__ = ["TextChannel"]


class TextChannel(Channel, DiscordMixin[discord.TextChannel]):
    __tablename__ = "text_channel"

    id: Mapped[str] = mapped_column(ForeignKey('channel.id'), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "text_channel",
    }

    def __init__(self, **kw: Any):
        super().__init__(type="text_channel", **kw)

    @classmethod
    def from_discord(cls, dto: discord.TextChannel) -> Self:
        entity = TextChannel()
        entity.discord_id = dto.id
        entity.name = dto.name
        return entity
