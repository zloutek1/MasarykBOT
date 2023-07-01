from sqlalchemy import Column, String

from core.database import Entity
from core.dated.mixin import DatedMixin
from core.discord_mixin import DiscordMixin


class Guild(Entity, DatedMixin, DiscordMixin):
    __tablename__ = "guild"

    name = Column(String, nullable=False)
