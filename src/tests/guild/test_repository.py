import unittest
from unittest.mock import MagicMock

import discord
from assertpy import assert_that

from core.database import Entity, Database
from guild.model import Guild
from guild.repository import GuildRepository


class Test(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        database = Database('sqlite+aiosqlite:///:memory:')
        cls.database = database
        cls.repository = GuildRepository(session_factory=database.session)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)

    async def test_create(self):
        # Call the method being tested
        guild = MagicMock(spec=discord.Guild)
        guild.id = "770041446911123456"
        guild.name = "Mock Guild"

        model = Guild.from_discord(guild)

        result = await self.repository.create(model)

        # Assert the expected result
        self.assertIsInstance(result, Guild)
        assert_that(result.name).is_equal_to('Mock Guild')

        results = await self.repository.find_all()
        assert_that(results).contains_only(result)
