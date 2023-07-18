from typing import cast
from unittest import mock
from unittest.mock import MagicMock, AsyncMock

import discord
from assertpy import assert_that, fail
from discord.ext import commands

import helpers
from helpers import MockBot, MockContext, MockGuild, MockTextChannel, MockMessage, MockMember, MockReaction
from starboard import cog, service
from starboard.config.model import StarboardConfig
from starboard.config.repository import StarboardConfigRepository
from starboard.service import StarboardService


class TestCreate(helpers.TestBase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

        self.bot = MockBot()
        self.guild = MockGuild(id=1)
        self.channel = MockTextChannel(id=2, guild=self.guild)
        self.message = MockMessage(content="!starboard create", channel=self.channel)
        self.ctx = MockContext(bot=self.bot, guild=self.guild, channel=self.channel, message=self.message)

        self.repository = StarboardConfigRepository(session_factory=self.database.session)
        self.service = StarboardService(self.bot, self.repository)
        self.cog = cog.Starboard(self.bot, self.service)

    async def test_create_default_creates_text_channel(self):
        self.guild.create_text_channel.return_value = MockTextChannel(name='starboard')

        await self.cog.create(self.cog, self.ctx)

        self.guild.create_text_channel.assert_called_with(name='starboard', overwrites=mock.ANY, reason=mock.ANY)

    async def test_create_default_saves_to_db(self):
        self.guild.create_text_channel.return_value = MockTextChannel(id=3, name='starboard')

        await self.cog.create(self.cog, self.ctx)

        redirects = await self.repository.find_redirects(guild_id=1, starboard_channel_id=3)
        assert_that(redirects).is_length(1)
        assert_that(redirects[0].target_id).is_none()

    async def test_create_named_creates_text_channel(self):
        self.guild.create_text_channel.return_value = MockTextChannel(name='channel_name')

        await self.cog.create(self.cog, self.ctx, name='channel_name')

        self.guild.create_text_channel.assert_called_with(name='channel_name', overwrites=mock.ANY, reason=mock.ANY)

    async def test_create_named_saves_to_db(self):
        self.guild.create_text_channel.return_value = MockTextChannel(id=3, name='channel_name')

        await self.cog.create(self.cog, self.ctx, name='channel_name')

        redirects = await self.repository.find_redirects(guild_id=1, starboard_channel_id=3)
        assert_that(redirects).is_length(1)
        assert_that(redirects[0].target_id).is_none()


class TestRedirect(helpers.TestBase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

        self.bot = MockBot()
        self.guild = MockGuild(id=1)
        self.channel = MockTextChannel(id=2, guild=self.guild)
        self.message = MockMessage(content="!starboard create", channel=self.channel)
        self.ctx = MockContext(bot=self.bot, guild=self.guild, channel=self.channel, message=self.message)

        self.repository = StarboardConfigRepository(session_factory=self.database.session)
        self.service = StarboardService(self.bot, self.repository)
        self.cog = cog.Starboard(self.bot, self.service)

    async def test_redirect_with_no_db_entry(self):
        starboard_channel = MockTextChannel(id=3, name='starboard')
        targets = cast(commands.Greedy, [self.channel])

        try:
            await self.cog.redirect(self.cog, self.ctx, starboard_channel, targets=targets)
            fail('no starboards should have been found')
        except service.StarError as ex:
            assert_that(str(ex)).is_equal_to('\N{NO ENTRY SIGN} Starboard channel #starboard not found in database.')

    async def test_redirect_single_target_updates_starboard_targets(self):
        await self.repository.create(StarboardConfig(guild_id=1, target_id=None, starboard_channel_id=3))
        starboard_channel = MockTextChannel(id=3, name='starboard')
        targets = cast(commands.Greedy, [self.channel])

        await self.cog.redirect(self.cog, self.ctx, starboard_channel, targets=targets)

        redirects = await self.repository.find_redirects(guild_id=1, starboard_channel_id=3)
        assert_that(redirects).is_length(1)
        assert_that(redirects[0].target_id).is_equal_to(2)

    async def test_redirect_multiple_targets_updates_starboard_targets(self):
        await self.repository.create(StarboardConfig(guild_id=1, target_id=None, starboard_channel_id=3))
        starboard_channel = MockTextChannel(id=3, name='starboard')
        second_target = MockTextChannel(id=4)
        targets = cast(commands.Greedy, [self.channel, second_target])

        await self.cog.redirect(self.cog, self.ctx, starboard_channel, targets=targets)

        redirects = await self.repository.find_redirects(guild_id=1, starboard_channel_id=3)
        assert_that(redirects).is_length(2)
        assert_that(redirects).extracting('target_id').contains_only(2, 4)


class TestReactionAddEvent(helpers.TestBase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

        self.guild = MockGuild(id=1)
        self.channel = MockTextChannel(id=2, guild=self.guild)
        self.member = MockMember(id=3, name="Bob")
        self.message = MockMessage(id=4, content="cool message", channel=self.channel, author=self.member)
        self.bot = MockBot(guilds=[self.guild])

        self.repository = StarboardConfigRepository(session_factory=self.database.session)
        self.service = StarboardService(self.bot, self.repository)
        self.cog = cog.Starboard(self.bot, self.service)

        self.emoji = discord.PartialEmoji(name="kek", animated=False)
        data = {
            "guild_id": 1,
            "channel_id": 2,
            "user_id": 3,
            "message_id": 4,
            "emoji": self.emoji,
            "member": self.member
        }
        self.payload = discord.RawReactionActionEvent(data=data, emoji=self.emoji, event_type="REACTION_ADD")

    async def test_reaction_add_invalid_guild(self):
        self.service.star_message = AsyncMock()
        self.bot.get_guild = MagicMock(return_value=None)

        await self.cog.on_raw_reaction_add(self.payload)

        self.service.star_message.assert_not_called()

    async def test_reaction_add_invalid_channel(self):
        self.service.star_message = AsyncMock()
        self.bot.get_guild = MagicMock(return_value=self.guild)
        self.guild.get_channel_or_thread = MagicMock(return_value=None)
        self.guild.fetch_channel = AsyncMock(return_value=None)

        await self.cog.on_raw_reaction_add(self.payload)

        self.service.star_message.assert_not_called()

    async def test_reaction_add_invalid_user(self):
        self.service.star_message = AsyncMock()
        self.bot.get_guild = MagicMock(return_value=self.guild)
        self.guild.get_channel_or_thread = MagicMock(return_value=self.channel)
        self.payload.member = None
        self.guild.fetch_member = AsyncMock(return_value=None)

        await self.cog.on_raw_reaction_add(self.payload)

        self.service.star_message.assert_not_called()

    async def test_reaction_add_invalid_message(self):
        self.service.star_message = AsyncMock()
        self.bot.get_guild = MagicMock(return_value=self.guild)
        self.guild.get_channel_or_thread = MagicMock(return_value=self.channel)
        self.channel.fetch_message = AsyncMock(return_value=None)

        await self.cog.on_raw_reaction_add(self.payload)

        self.service.star_message.assert_not_called()

    async def test_reaction_add_invalid_reaction(self):
        self.service.star_message = AsyncMock()
        self.bot.get_guild = MagicMock(return_value=self.guild)
        self.guild.get_channel_or_thread = MagicMock(return_value=self.channel)
        self.channel.fetch_message = AsyncMock(return_value=self.message)
        self.message.reactions = []

        await self.cog.on_raw_reaction_add(self.payload)

        self.service.star_message.assert_not_called()

    async def test_reaction_add_invalid_starboard_config(self):
        self.service.star_message = AsyncMock()
        self.bot.get_guild = MagicMock(return_value=self.guild)
        self.guild.get_channel_or_thread = MagicMock(return_value=self.channel)
        self.channel.fetch_message = AsyncMock(return_value=self.message)
        self.message.reactions = [MockReaction(emoji=self.emoji, message=self.message)]

        await self.cog.on_raw_reaction_add(self.payload)

        self.service.star_message.assert_not_called()

    async def test_reaction_add_valid(self):
        self.bot.get_guild = MagicMock(return_value=self.guild)
        self.guild.get_channel_or_thread = MagicMock(return_value=self.channel)
        self.payload.member = self.member
        self.channel.fetch_message = AsyncMock(return_value=self.message)
        self.message.reactions = [MockReaction(emoji=self.emoji, message=self.message)]
        await self.repository.create(StarboardConfig(guild_id=1, target_id=None, starboard_channel_id=5))
        self.service.star_message = AsyncMock(return_value=None)

        await self.cog.on_raw_reaction_add(self.payload)

        self.service.star_message.assert_called()
