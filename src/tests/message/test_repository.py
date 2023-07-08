from assertpy import assert_that

import helpers
from core.database import Entity
from message.model import Message
from message.repository import MessageRepository


class Test(helpers.TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = MessageRepository(session_factory=cls.database.session)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)

    async def test_create(self):
        # Call the method being tested
        message = helpers.create_discord_message(content='Hi')
        model = Message.from_discord(message)

        result = await self.repository.create(model)

        # Assert the expected result
        self.assertIsInstance(result, Message)
        assert_that(result.content).is_equal_to('Hi')

        results = await self.repository.find_all()
        assert_that(results).contains_only(result)
