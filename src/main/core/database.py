import logging
from contextlib import asynccontextmanager
from typing import AsyncContextManager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

log = logging.getLogger(__name__)


class Entity(AsyncAttrs, DeclarativeBase):
    pass


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
