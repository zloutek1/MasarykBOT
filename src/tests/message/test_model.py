from assertpy import assert_that

import helpers
from message.model import Message


class Test(helpers.TestBase):

    async def test_from_discord(self):
        message = helpers.create_discord_message(content='Hi')

        model = Message.from_discord(message)

        assert_that(model.content).is_equal_to('Hi')

    async def test_hash_by_discord_id(self):
        model1 = Message()
        model1.id = 'AAA'
        model1.discord_id = '123'
        model1.content = 'Name A'

        model2 = Message()
        model2.id = 'BBB'
        model2.discord_id = '123'
        model2.content = 'Name B'

        assert_that(hash(model1)).is_equal_to(hash(model2))
        assert_that(model1).is_equal_to(model2)
        assert_that({model1, model2}).is_length(1)

    async def test_equals_by_fields(self):
        model1 = Message()
        model1.id = 'AAA'
        model1.discord_id = '123'
        model1.content = 'Name A'

        model2 = Message()
        model2.id = None
        model2.discord_id = '123'
        model2.content = 'Name B'

        assert_that(model1.equals(model2)).is_false()

        model2.content = 'Name A'

        assert_that(model1.equals(model2)).is_true()
