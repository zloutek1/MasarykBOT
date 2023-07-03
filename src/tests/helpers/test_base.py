import unittest

from core.database import Database, Entity

__all__ = ['TestBase']


class TestBase(unittest.IsolatedAsyncioTestCase):
    database: Database

    @classmethod
    def setUpClass(cls):
        cls.database = Database(url='sqlite+aiosqlite:///:memory:', echo=True)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)
