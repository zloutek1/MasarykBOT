from assertpy import assert_that

import helpers
from helpers import MockRole, MockGuild
from role.model import Role
from role.repository import RoleRepository
from role.syncer import RoleSyncer
from sync.syncer import Diff


class Test(helpers.TestBase):
    repository: RoleRepository
    syncer: RoleSyncer

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = RoleRepository(session_factory=cls.database.session)
        cls.syncer = RoleSyncer(repository=cls.repository)

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.everyone_role = await self.repository.create(Role(discord_id=0, name='@everyone', color=0xdeadbf))

    async def test__get_diff_no_change(self):
        await self.repository.create(Role(discord_id=123456, name='Admin'))
        guild = MockGuild(roles=[
            MockRole(id=123456, name='Admin')
        ])

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).is_empty()
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_created(self):
        guild = MockGuild(roles=[
            MockRole(id=123456, name='Admin')
        ])

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).contains_only(Role(id=None, discord_id=123456, name='Admin'))
        assert_that(diff.updated).is_empty()
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_updated(self):
        await self.repository.create(Role(discord_id=123456, name='Admin'))
        guild = MockGuild(roles=[
            MockRole(id=123456, name='User')
        ])

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).contains_only(Role(discord_id=123456, name='User'))
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_deleted(self):
        await self.repository.create(Role(discord_id=123456, name='Admin'))
        discord_roles = []
        guild = MockGuild(roles=discord_roles)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).is_empty()
        assert_that(diff.deleted).contains_only(Role(discord_id=123456, name='User'))

    async def test__sync_created(self):
        role = Role(discord_id=123456, name='Admin')
        diff = Diff(created={role}, updated=set(), deleted=set())

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).contains_only(role, self.everyone_role)

    async def test__sync_updated(self):
        await self.repository.create(Role(discord_id=123456, name='Admin'))
        role = Role(discord_id=123456, name='User')
        diff = Diff(created=set(), updated={role}, deleted=set())

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).contains_only(role, self.everyone_role)

    async def test__sync_deleted(self):
        db_role = await self.repository.create(Role(discord_id=123456, name='Admin'))
        diff = Diff(created=set(), updated=set(), deleted={db_role})

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).contains_only(self.everyone_role)
