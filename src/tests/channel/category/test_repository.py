from assertpy import assert_that

import helpers
from channel.category.model import CategoryChannel
from channel.category.repository import CategoryChannelRepository
from core.database import Entity


class Test(helpers.TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = CategoryChannelRepository(session_factory=cls.database.session)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)

    async def test_create(self):
        # Call the method being tested
        channel = helpers.create_discord_category_channel(name='channel name')
        model = CategoryChannel.from_discord(channel)

        result = await self.repository.create(model)

        # Assert the expected result
        self.assertIsInstance(result, CategoryChannel)
        assert_that(result.name).is_equal_to('channel name')

        results = await self.repository.find_all()
        assert_that(results).contains_only(result)
