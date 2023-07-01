from sqlalchemy import Column, DateTime, func

from core.domain.mixin import DomainMixin

__all__ = ["DatedMixin"]


class DatedMixin(DomainMixin):
    created = Column(DateTime, default=func.now(), nullable=False)
    updated = Column(DateTime, default=None)
    deleted = Column(DateTime, default=None)
