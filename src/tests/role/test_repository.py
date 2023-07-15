from assertpy import assert_that

import helpers
from helpers import MockRole
from role.model import Role
from role.repository import RoleRepository


class Test(helpers.TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = RoleRepository(session_factory=cls.database.session)

    async def test_create(self):
        # Call the method being tested
        role = MockRole(name='role name')
        model = Role.from_discord(role)

        result = await self.repository.create(model)

        # Assert the expected result
        self.assertIsInstance(result, Role)
        assert_that(result.name).is_equal_to('role name')

        results = await self.repository.find_all()
        assert_that(results).contains_only(result)
