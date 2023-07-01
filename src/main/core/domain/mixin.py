import uuid
from dataclasses import dataclass

from sqlalchemy import Column, UUID

__all__ = ["DomainMixin"]

from sqlalchemy.orm import Mapped


@dataclass
class DomainMixin:
    id: Mapped[uuid.UUID] = Column(UUID, primary_key=True, default=uuid.uuid4)
