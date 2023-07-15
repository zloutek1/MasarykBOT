from assertpy import assert_that

import helpers
from channel.category.model import CategoryChannel
from channel.category.repository import CategoryChannelRepository
from channel.category.syncer import CategoryChannelSyncer
from helpers import MockGuild, MockCategoryChannel
from sync.syncer import Diff


class Test(helpers.TestBase):
    repository: CategoryChannelRepository
    syncer: CategoryChannelSyncer

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = CategoryChannelRepository(session_factory=cls.database.session)
        cls.syncer = CategoryChannelSyncer(repository=cls.repository)

    async def test__get_diff_no_change(self):
        await self.repository.create(CategoryChannel(discord_id=123456, name='category'))
        discord_category_channels = [MockCategoryChannel(id=123456, name='category')]
        guild = MockGuild(categories=discord_category_channels)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).contains_only(CategoryChannel(discord_id=123456, name='category'))
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_created(self):
        discord_categories = [MockCategoryChannel(id=123456, name='Admin')]
        guild = MockGuild(categories=discord_categories)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).contains_only(
            CategoryChannel(id=None, discord_id=123456, name='Admin'))
        assert_that(diff.updated).is_empty()
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_updated(self):
        await self.repository.create(CategoryChannel(discord_id=123456, name='Admin'))
        discord_categories = [MockCategoryChannel(id=123456, name='User')]
        guild = MockGuild(categories=discord_categories)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).contains_only(CategoryChannel(discord_id=123456, name='User'))
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_deleted(self):
        await self.repository.create(CategoryChannel(discord_id=123456, name='Admin'))
        discord_categories = []
        guild = MockGuild(categories=discord_categories)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).is_empty()
        assert_that(diff.deleted).contains_only(CategoryChannel(discord_id=123456, name='User'))

    async def test__sync_created(self):
        category = CategoryChannel(discord_id=123456, name='Admin')
        diff = Diff(created={category}, updated=set(), deleted=set())

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).contains_only(category)

    async def test__sync_updated(self):
        await self.repository.create(CategoryChannel(discord_id=123456, name='Admin'))
        category = CategoryChannel(discord_id=123456, name='User')
        diff = Diff(created=set(), updated={category}, deleted=set())

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).contains_only(category)

    async def test__sync_deleted(self):
        category = await self.repository.create(CategoryChannel(discord_id=123456, name='Admin'))
        diff = Diff(created=set(), updated=set(), deleted={category})

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).is_empty()
