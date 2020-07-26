import unittest
from unittest import mock

from datetime import datetime

import bot.cogs.logger as logger
from tests.helpers import MockBot, MockGuild, MockConnection, unwrap

class LoggerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """Add mocked bot and cog to the instance."""
        self.bot = MockBot()
        with mock.patch("discord.ext.tasks.Loop.start"):
            self.cog = logger.Logger(bot=self.bot)

    async def test_backup_guilds(self):
        self.bot.guilds = [
            MockGuild(id=0, name="first"),
            MockGuild(id=1, name="second"),
            MockGuild(id=2, name="third")
        ]
        backup_guilds = unwrap(self.cog.backup_guilds)

        conn = MockConnection()
        await backup_guilds(self.cog, conn)
        print(conn.executemany.call_args)

