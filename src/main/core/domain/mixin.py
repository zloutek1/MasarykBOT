from sqlalchemy import Column, UUID

__all__ = ["DomainMixin"]


class DomainMixin:
    id = Column(UUID, primary_key=True)
