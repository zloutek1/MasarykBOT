from typing import TypeVar, Generic

import inject

from .entity import Entity
from .types import Pool

TEntity = TypeVar('TEntity', bound=Entity)


class Table(Generic[TEntity]):
    @inject.autoparams('pool')
    def __init__(self, entity: TEntity, pool: Pool) -> None:
        assert hasattr(entity, '__table_name__')
        self.entity = entity
        self.pool = pool

    @property
    def __table_name__(self):
        return self.entity.__table_name__
