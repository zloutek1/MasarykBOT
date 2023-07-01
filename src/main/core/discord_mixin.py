from dataclasses import dataclass

from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped


@dataclass
class DiscordMixin:
    discord_id: Mapped[str] = Column(String, nullable=False)
