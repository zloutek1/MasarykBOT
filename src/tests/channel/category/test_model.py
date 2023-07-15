from assertpy import assert_that

import helpers
from channel.category.model import CategoryChannel
from helpers import MockCategoryChannel


class Test(helpers.TestBase):

    async def test_from_discord(self):
        category = MockCategoryChannel(name='category name')

        model = CategoryChannel.from_discord(category)

        assert_that(model.name).is_equal_to('category name')

    async def test_hash_by_discord_id(self):
        model1 = CategoryChannel()
        model1.id = 'AAA'
        model1.discord_id = '123'
        model1.name = 'Name A'

        model2 = CategoryChannel()
        model2.id = 'BBB'
        model2.discord_id = '123'
        model2.name = 'Name B'

        assert_that(hash(model1)).is_equal_to(hash(model2))
        assert_that(model1).is_equal_to(model2)
        assert_that({model1, model2}).is_length(1)

    async def test_equals_by_fields(self):
        model1 = CategoryChannel()
        model1.id = 'AAA'
        model1.discord_id = '123'
        model1.name = 'Name A'

        model2 = CategoryChannel()
        model2.id = None
        model2.discord_id = '123'
        model2.name = 'Name B'

        assert_that(model1.equals(model2)).is_false()

        model2.name = 'Name A'

        assert_that(model1.equals(model2)).is_true()
