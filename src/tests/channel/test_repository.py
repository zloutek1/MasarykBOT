from assertpy import assert_that

import helpers
from channel.category.model import CategoryChannel
from channel.repository import ChannelRepository
from channel.text.model import TextChannel
from core.database import Entity
from helpers import MockTextChannel


class Test(helpers.TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = ChannelRepository(session_factory=cls.database.session)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)

    async def test_create(self):
        # Call the method being tested
        channel = MockTextChannel(name='channel name')
        model = TextChannel.from_discord(channel)

        result = await self.repository.create(model)

        # Assert the expected result
        self.assertIsInstance(result, TextChannel)
        assert_that(result.name).is_equal_to('channel name')

        results = await self.repository.find_all()
        assert_that(results).contains_only(result)

    async def test_find_all(self):
        model = TextChannel(discord_id=1, name='channel name')
        result1 = await self.repository.create(model)

        model = CategoryChannel(discord_id=2, name='category name')
        result2 = await self.repository.create(model)

        results = await self.repository.find_all()
        assert_that(results).contains_only(result1, result2)
