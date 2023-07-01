import logging
from contextlib import contextmanager, AbstractContextManager
from typing import Callable

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

log = logging.getLogger(__name__)
Entity = declarative_base()


class Database:
    def __init__(self, url: str):
        assert url, "Database connection url must be set"
        self._engine = create_async_engine(url, echo=True)
        self._session_factory = async_sessionmaker(bind=self._engine, expire_on_commit=False)

    async def create_database(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.create_all)

    @contextmanager
    async def session(self) -> Callable[..., AbstractContextManager[AsyncSession]]:
        session: AsyncSession = self._session_factory()
        try:
            yield session
        except Exception:
            log.exception("Session rollback because of exception")
            await session.rollback()
            raise
        finally:
            await session.close()
