import abc
from typing import TypeVar, Union, Sequence, cast

from sqlalchemy import select, func, BinaryExpression

from core.database import Entity
from core.dated.mixin import DatedMixin

__all__ = ['DatedRepository']

from core.domain.repository import DomainRepository

T = TypeVar('T', bound=Union[Entity, DatedMixin])


class DatedRepository(DomainRepository[T], abc.ABC):
    """
    A CRUD repository for DatedMixin entities
    delete is implemented as a soft-delete
    """

    async def find_all(self) -> Sequence[T]:
        async with self.session_factory() as session:
            statement = select(self.model).where(self.not_deleted())
            result = await session.execute(statement)
            session.expunge_all()
            return cast(Sequence[T], result.scalars().all())

    async def find(self, id: str) -> T | None:
        async with self.session_factory() as session:
            statement = select(self.model) \
                .where(self.model.id == id) \
                .where(self.not_deleted())
            result = await session.execute(statement)
            session.expunge_all()
            return result.scalars().first()

    async def create(self, entity: T) -> T:
        return await super().create(entity)

    async def update(self, entity: T) -> T:
        return await super().update(entity)

    async def delete(self, id: str) -> None:
        async with self.session_factory() as session:
            if not (entity := await self.find(id)):
                return
            entity.deleted = func.now()
            await session.merge(entity)
            await session.commit()
            session.expunge_all()

    async def hard_delete(self, id: str) -> None:
        await super().delete(id)

    def not_deleted(self) -> BinaryExpression:
        return self.model.deleted.is_(None)
