from typing import List, TypeVar, Type

from asyncpg import Record

TEntity = TypeVar('TEntity', bound='Entity')


class Entity:
    __table_name__: str

    @classmethod
    def convert(cls: Type[TEntity], record: Record) -> TEntity:
        # noinspection PyArgumentList
        return cls(**{k: v for (k, v) in record.items()})


    @classmethod
    def convert_many(cls: Type[TEntity], records: List[Record]) -> List[TEntity]:
        return [cls.convert(record) for record in records]
