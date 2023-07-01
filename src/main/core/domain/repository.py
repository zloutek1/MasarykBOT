import abc
from contextlib import AbstractContextManager
from typing import Callable, TypeVar, Generic, Iterator

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Entity
from core.domain.mixin import DomainMixin

__all__ = ['DomainRepository']

T = TypeVar('T', bound=[Entity, DomainMixin])


class DomainRepository(abc.ABC, Generic[T]):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[AsyncSession]]) -> None:
        self.session_factory = session_factory

    @property
    @abc.abstractmethod
    def model(self):
        raise NotImplementedError

    async def find_all(self) -> Iterator[T]:
        async with self.session_factory() as session:
            return await session.query(self.model).all()

    async def find(self, id: str) -> T | None:
        async with self.session_factory() as session:
            return (
                await session
                .query(self.model)
                .filter(self.model.id == id)
                .first()
            )

    async def create(self, entity: T) -> T:
        async with self.session_factory() as session:
            await session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity: T) -> T:
        async with self.session_factory() as session:
            await session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def delete(self, id: str) -> None:
        async with self.session_factory() as session:
            entity = self.find(id)
            if entity:
                await session.delete(entity)
                await session.commit()
