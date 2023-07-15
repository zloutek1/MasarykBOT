from assertpy import assert_that

import helpers
from channel.text.model import TextChannel
from helpers import MockTextChannel


class Test(helpers.TestBase):

    async def test_from_discord(self):
        text_channel = MockTextChannel(name='text channel name')

        model = TextChannel.from_discord(text_channel)

        assert_that(model.name).is_equal_to('text channel name')

    async def test_hash_by_discord_id(self):
        model1 = TextChannel()
        model1.id = 'AAA'
        model1.discord_id = '123'
        model1.name = 'Name A'

        model2 = TextChannel()
        model2.id = 'BBB'
        model2.discord_id = '123'
        model2.name = 'Name B'

        assert_that(hash(model1)).is_equal_to(hash(model2))
        assert_that(model1).is_equal_to(model2)
        assert_that({model1, model2}).is_length(1)
