from sqlalchemy import Column, String

from core.database import Entity
from core.dated.mixin import DatedMixin
from core.discord_mixin import DiscordMixin


class Role(Entity, DatedMixin, DiscordMixin):
    __tablename__ = "role"

    name = Column(String)
