from assertpy import assert_that

import helpers
from core.database import Entity
from guild.model import Guild
from guild.repository import GuildRepository


class Test(helpers.TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = GuildRepository(session_factory=cls.database.session)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)

    async def test_create(self):
        # Call the method being tested
        guild = helpers.create_discord_guild(name='guild name')
        model = Guild.from_discord(guild)

        result = await self.repository.create(model)

        # Assert the expected result
        self.assertIsInstance(result, Guild)
        assert_that(result.name).is_equal_to('guild name')

        results = await self.repository.find_all()
        assert_that(results).contains_only(result)
