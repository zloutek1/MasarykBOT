from assertpy import assert_that

import helpers
from guild.model import Guild


class Test(helpers.TestBase):

    async def test_from_discord(self):
        guild = helpers.create_discord_guild(name='guild name')

        model = Guild.from_discord(guild)

        assert_that(model.name).is_equal_to('guild name')

    async def test_hash_by_discord_id(self):
        model1 = Guild()
        model1.id = 'AAA'
        model1.discord_id = '123'
        model1.name = 'Name A'

        model2 = Guild()
        model2.id = 'BBB'
        model2.discord_id = '123'
        model2.name = 'Name B'

        assert_that(hash(model1)).is_equal_to(hash(model2))
        assert_that(model1).is_equal_to(model2)
        assert_that({model1, model2}).is_length(1)

    async def test_equals_by_fields(self):
        model1 = Guild()
        model1.id = 'AAA'
        model1.discord_id = '123'
        model1.name = 'Name A'

        model2 = Guild()
        model2.id = None
        model2.discord_id = '123'
        model2.name = 'Name B'

        assert_that(model1.equals(model2)).is_false()

        model2.name = 'Name A'

        assert_that(model1.equals(model2)).is_true()
