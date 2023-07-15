from assertpy import assert_that

import helpers
from channel.text.model import TextChannel
from channel.text.repository import TextChannelRepository
from channel.text.syncer import TextChannelSyncer
from helpers import MockTextChannel, MockGuild
from sync.syncer import Diff


class Test(helpers.TestBase):
    repository: TextChannelRepository
    syncer: TextChannelSyncer

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = TextChannelRepository(session_factory=cls.database.session)
        cls.syncer = TextChannelSyncer(repository=cls.repository)

    async def test__get_diff_no_change(self):
        await self.repository.create(TextChannel(discord_id=123456, name='Admin'))
        discord_text_channels = [MockTextChannel(id=123456, name='Admin')]
        guild = MockGuild(text_channels=discord_text_channels)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).is_empty()
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_created(self):
        discord_text_channels = [MockTextChannel(id=123456, name='Admin')]
        guild = MockGuild(text_channels=discord_text_channels)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).contains_only(
            TextChannel(id=None, discord_id=123456, name='Admin'))
        assert_that(diff.updated).is_empty()
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_updated(self):
        await self.repository.create(TextChannel(discord_id=123456, name='Admin'))
        discord_text_channels = [MockTextChannel(id=123456, name='User')]
        guild = MockGuild(text_channels=discord_text_channels)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).contains_only(TextChannel(discord_id=123456, name='User'))
        assert_that(diff.deleted).is_empty()

    async def test__get_diff_deleted(self):
        await self.repository.create(TextChannel(discord_id=123456, name='Admin'))
        discord_roles = []
        guild = MockGuild(roles=discord_roles)

        diff = await self.syncer._get_diff(guild)

        assert_that(diff).is_instance_of(Diff)
        assert_that(diff.created).is_empty()
        assert_that(diff.updated).is_empty()
        assert_that(diff.deleted).contains_only(TextChannel(discord_id=123456, name='User'))

    async def test__sync_created(self):
        text_channel = TextChannel(discord_id=123456, name='Admin')
        diff = Diff(created={text_channel}, updated=set(), deleted=set())

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).contains_only(text_channel)

    async def test__sync_updated(self):
        await self.repository.create(TextChannel(discord_id=123456, name='Admin'))
        text_channel = TextChannel(discord_id=123456, name='User')
        diff = Diff(created=set(), updated={text_channel}, deleted=set())

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).contains_only(text_channel)

    async def test__sync_deleted(self):
        db_text_channel = await self.repository.create(
            TextChannel(discord_id=123456, name='Admin'))
        diff = Diff(created=set(), updated=set(), deleted={db_text_channel})

        await self.syncer._sync(diff)

        results = await self.repository.find_all()
        assert_that(results).is_empty()
