import abc
import logging
from contextlib import asynccontextmanager
from typing import AsyncContextManager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept

log = logging.getLogger(__name__)


class CombinedMeta(DeclarativeAttributeIntercept, abc.ABCMeta):
    """
    The DelcarativeBase has a metaclass=DeclarativeAttributeIntercept
    In order to allow Entity subclasses to also inherit other abstract classes
    we need to add abc.ABCMeta to the Entity's metaclass
    """


class Entity(AsyncAttrs, DeclarativeBase, metaclass=CombinedMeta):
    """
    A base class for all database entities
    ex.
        class User(Entity):
            __tablename__ = "user"
    """


class Database:
    def __init__(self, url: str):
        assert url, "Database connection url must be set"
        self._engine = create_async_engine(url, echo=True)
        self._session_factory = async_sessionmaker(bind=self._engine, expire_on_commit=False)

    async def create_database(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncContextManager[AsyncSession]:
        session: AsyncSession = self._session_factory()
        try:
            yield session
        except Exception:
            log.exception("Session rollback because of exception")
            await session.rollback()
            raise
        finally:
            await session.close()
