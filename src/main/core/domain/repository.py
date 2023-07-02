import abc
from typing import TypeVar, Generic, Union, AsyncContextManager, Callable, Sequence, cast, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Entity
from core.domain.mixin import DomainMixin

__all__ = ['DomainRepository']

T = TypeVar('T', bound=Union[Entity, DomainMixin])


class DomainRepository(abc.ABC, Generic[T]):
    def __init__(self, session_factory: Callable[..., AsyncContextManager[AsyncSession]]) -> None:
        self.session_factory = session_factory

    @property
    @abc.abstractmethod
    def model(self) -> Type:
        raise NotImplementedError

    async def find_all(self) -> Sequence[T]:
        async with self.session_factory() as session:
            statement = select(self.model)
            result = await session.execute(statement)
            session.expunge_all()
            return cast(Sequence[T], result.scalars().all())

    async def find(self, id: str) -> T | None:
        async with self.session_factory() as session:
            statement = select(self.model).where(self.model.id == id)
            result = await session.execute(statement)
            session.expunge_all()
            return result.scalars().first()

    async def create(self, entity: T) -> T:
        async with self.session_factory() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity: T) -> T:
        async with self.session_factory() as session:
            await session.merge(entity)
            await session.commit()
            session.expunge_all()
            return entity

    async def delete(self, id: str) -> None:
        async with self.session_factory() as session:
            if not (entity := await self.find(id)):
                return
            await session.delete(entity)
            await session.commit()
            session.expunge_all()
