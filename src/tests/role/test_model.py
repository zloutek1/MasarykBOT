from assertpy import assert_that

import helpers
from helpers import MockRole
from role.model import Role


class Test(helpers.TestBase):

    async def test_from_discord(self):
        role = MockRole(name='role name')

        model = Role.from_discord(role)

        assert_that(model.name).is_equal_to('role name')

    async def test_hash_by_discord_id(self):
        model1 = Role()
        model1.id = 'AAA'
        model1.discord_id = '123'
        model1.name = 'Name A'

        model2 = Role()
        model2.id = 'BBB'
        model2.discord_id = '123'
        model2.name = 'Name B'

        assert_that(hash(model1)).is_equal_to(hash(model2))
        assert_that(model1).is_equal_to(model2)
        assert_that({model1, model2}).is_length(1)
