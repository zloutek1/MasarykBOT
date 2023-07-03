import abc
import uuid
from typing import Hashable

from sqlalchemy import Column, String

__all__ = ["DomainMixin"]

from sqlalchemy.orm import Mapped


class DomainMixin(Hashable, abc.ABC):
    """
    An addition to the Entity class
    provides the database entity an id field
    """

    id: Mapped[uuid.UUID | None] = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
