from sqlalchemy import Column, String

from core.database import Entity
from core.dated.mixin import DatedMixin


class Guild(Entity, DatedMixin):
    __tablename__ = "guild"

    name = Column(String, nullable=False)
