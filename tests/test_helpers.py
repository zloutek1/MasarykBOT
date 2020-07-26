import asyncio
import unittest
import unittest.mock

import discord

from tests import helpers

class DiscordMocksTests(unittest.TestCase):
    """Tests for our specialized discord.py mocks."""

    def test_mock_guild_default_initialization(self):
        """Test if the default initialization of Mockguild results in the correct object."""
        guild = helpers.MockGuild()

        # The `spec` argument makes sure `isistance` checks with `discord.Guild` pass
        self.assertIsInstance(guild, discord.Guild)

        self.assertListEqual(guild.roles, [helpers.MockRole(name="@everyone", position=1, id=0)])
        self.assertListEqual(guild.members, [])

    def test_mock_guild_alternative_arguments(self):
        """Test if MockGuild initializes with the arguments provided."""
        core_developer = helpers.MockRole(name="Core Developer", position=2)
        guild = helpers.MockGuild(
            roles=[core_developer],
            members=[helpers.MockMember(id=54321)],
        )

        self.assertListEqual(guild.roles, [helpers.MockRole(name="@everyone", position=1, id=0), core_developer])
        self.assertListEqual(guild.members, [helpers.MockMember(id=54321)])

    def test_mock_guild_accepts_dynamic_arguments(self):
        """Test if MockGuild accepts and sets abitrary keyword arguments."""
        guild = helpers.MockGuild(
            emojis=(":hyperjoseph:", ":pensive_ela:"),
            premium_subscription_count=15,
        )

        self.assertTupleEqual(guild.emojis, (":hyperjoseph:", ":pensive_ela:"))
        self.assertEqual(guild.premium_subscription_count, 15)

    def test_mock_bot_default_initialization(self):
        """Tests if MockBot initializes with the correct values."""
        bot = helpers.MockBot()

        # The `spec` argument makes sure `isistance` checks with `discord.ext.commands.Bot` pass
        self.assertIsInstance(bot, discord.ext.commands.Bot)

    def test_mock_context_default_initialization(self):
        """Tests if MockContext initializes with the correct values."""
        context = helpers.MockContext()

        # The `spec` argument makes sure `isistance` checks with `discord.ext.commands.Context` pass
        self.assertIsInstance(context, discord.ext.commands.Context)

        self.assertIsInstance(context.bot, helpers.MockBot)
        self.assertIsInstance(context.guild, helpers.MockGuild)
        self.assertIsInstance(context.author, helpers.MockMember)

