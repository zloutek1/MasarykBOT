from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .entity import Entity

TObject = TypeVar('TObject')
TEntity = TypeVar('TEntity', bound=Entity)



class Mapper(ABC, Generic[TObject, TEntity]):
    @abstractmethod
    async def map(self, obj: TObject) -> TEntity:
        raise NotImplementedError
    
