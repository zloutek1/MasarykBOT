import unittest

from assertpy import assert_that

import helpers
from core.database import Entity, Database
from role.model import Role
from role.repository import RoleRepository


class Test(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        database = Database('sqlite+aiosqlite:///:memory:')
        cls.database = database
        cls.repository = RoleRepository(session_factory=database.session)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)

    async def test_create(self):
        # Call the method being tested
        role = helpers.create_role('role name')
        model = Role.from_discord(role)

        result = await self.repository.create(model)

        # Assert the expected result
        self.assertIsInstance(result, Role)
        assert_that(result.name).is_equal_to('role name')

        results = await self.repository.find_all()
        assert_that(results).contains_only(result)
