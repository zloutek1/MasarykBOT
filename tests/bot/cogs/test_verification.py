import unittest
from unittest.mock import Mock, AsyncMock, patch

from bot.cogs import verification
from tests.mocks.discord import MockBot, MockGuild, MockRole, MockMember, MockTextChannel, MockEmoji, MockRawReactionActionEvent

class VerificationTests(unittest.IsolatedAsyncioTestCase):
    async def test_verification_channels(self):
        #
        guild1 = Mock()
        guild1.channels.verification = 123

        guild2 = Mock()
        guild2.channels.verification = 456

        guild3 = Mock()
        guild3.channels.verification = 789

        config = Mock()
        config.guilds = [guild1, guild2, guild3]
        #

        bot = MockBot()
        cog = verification.Verification(bot=bot)
        bot.get_channel = lambda id: MockTextChannel(id=id)

        with patch('bot.cogs.verification.Config', config):
            excepted = [MockTextChannel(id=123), MockTextChannel(id=456), MockTextChannel(id=789)]
            actual = cog.verification_channels
            self.assertCountEqual(excepted, actual)

    async def test_reaction_add(self):
        payload = MockRawReactionActionEvent(
            guild_id = 1,
            emoji=MockEmoji(name="Verification"),
            user_id=2,
            channel_id=3,
            event_type="REACTION_ADD")

        #
        guild = Mock()
        guild.id = 1
        guild.channels.verification = 3

        config = Mock()
        config.guilds = [guild]
        #

        #
        member = MockMember(id=2)

        guild = MockGuild(id=1)
        guild.members = [member]

        bot = MockBot()
        bot.guilds = [guild]
        #

        cog = verification.Verification(bot=bot)

        cog._verify_join = AsyncMock(return_value=None)
        with patch('bot.cogs.verification.Config', config):
            await cog.on_raw_reaction_add(payload)
        cog._verify_join.assert_called_once_with(member)

    async def test_reaction_remove(self):
        payload = MockRawReactionActionEvent(
            guild_id = 1,
            emoji=MockEmoji(name="Verification"),
            user_id=2,
            channel_id=3,
            event_type="REACTION_REMOVE")

        #
        guild = Mock()
        guild.id = 1
        guild.channels.verification = 3

        config = Mock()
        config.guilds = [guild]
        #

        #
        member = MockMember(id=2)

        guild = MockGuild(id=1)
        guild.members = [member]

        bot = MockBot()
        bot.guilds = [guild]
        #

        cog = verification.Verification(bot=bot)

        cog._verify_leave = AsyncMock(return_value=None)
        with patch('bot.cogs.verification.Config', config):
            await cog.on_raw_reaction_remove(payload)
        cog._verify_leave.assert_called_once_with(member)

    async def test_verify_join(self):
        #
        guild = Mock()
        guild.id = 1
        guild.roles.verified = 2

        config = Mock()
        config.guilds = [guild]
        #

        role = MockRole(id=2, name="verified")
        guild = MockGuild(id=1, roles=[role])
        member = MockMember(id=3, guild=guild, name="Bob")

        member.add_roles = AsyncMock(return_value=None)

        bot = MockBot()
        cog = verification.Verification(bot=bot)

        with patch('bot.cogs.verification.Config', config):
            await cog._verify_join(member)

        member.add_roles.assert_called_once_with(role)

    async def test_verify_leave(self):
        #
        guild = Mock()
        guild.id = 1
        guild.roles.verified = 2

        config = Mock()
        config.guilds = [guild]
        #

        role = MockRole(id=2, name="verified")
        guild = MockGuild(id=1)
        member = MockMember(id=3, roles=[role], guild=guild, name="Bob")

        member.remove_roles = AsyncMock(return_value=None)

        bot = MockBot()
        cog = verification.Verification(bot=bot)

        with patch('bot.cogs.verification.Config', config):
            await cog._verify_leave(member)

        member.remove_roles.assert_called_once_with(role)