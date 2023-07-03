from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import Mapped

from core.domain.mixin import DomainMixin

__all__ = ["DatedMixin"]


class DatedMixin(DomainMixin):
    created: Mapped[datetime | None] = Column(DateTime, default=func.now())
    updated: Mapped[datetime | None] = Column(DateTime, default=None)
    deleted: Mapped[datetime | None] = Column(DateTime, default=None)
