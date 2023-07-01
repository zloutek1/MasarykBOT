from dataclasses import dataclass

from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

from core.database import Entity
from core.dated.mixin import DatedMixin
from core.discord_mixin import DiscordMixin


@dataclass
class Guild(Entity, DatedMixin, DiscordMixin):
    __tablename__ = "guild"

    name: Mapped[str] = Column(String, nullable=False)
