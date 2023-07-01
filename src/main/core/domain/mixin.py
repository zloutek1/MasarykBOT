import uuid
from dataclasses import dataclass

from sqlalchemy import Column, String

__all__ = ["DomainMixin"]

from sqlalchemy.orm import Mapped


@dataclass
class DomainMixin:
    id: Mapped[uuid.UUID] = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
