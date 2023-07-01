from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import Mapped

from core.domain.mixin import DomainMixin

__all__ = ["DatedMixin"]


@dataclass
class DatedMixin(DomainMixin):
    created: Mapped[datetime] = Column(DateTime, default=func.now(), nullable=False)
    updated: Mapped[datetime | None] = Column(DateTime, default=None)
    deleted: Mapped[datetime | None] = Column(DateTime, default=None)
