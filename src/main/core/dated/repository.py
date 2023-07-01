import abc
from typing import TypeVar, Union

from core.database import Entity
from core.dated.mixin import DatedMixin

__all__ = ['DatedRepository']

from core.domain.repository import DomainRepository

T = TypeVar('T', bound=Union[Entity, DatedMixin])


class DatedRepository(DomainRepository[T], abc.ABC):
    pass
